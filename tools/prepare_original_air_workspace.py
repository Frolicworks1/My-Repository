#!/usr/bin/env python3
"""Prepare a private, package-shaped workspace for an original-SWF AIR experiment.

This is intentionally a no-ANE diagnostic package: the supplied APK has no
ARM64 payload for its three native extensions. The tool preserves the original
SWF and resource tree, updates the diagnostic app ID/target SDK, removes
extension declarations and legacy C2DM manifest components, and never edits the
input APK. It does not produce an APK by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET


ANDROID_NS = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", ANDROID_NS)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def prepare(apk: Path, out: Path, app_id: str, target_sdk: int) -> dict:
    if not apk.is_file():
        raise FileNotFoundError(f"APK not found: {apk}")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    inventory = {
        "source_apk_name": apk.name,
        "source_apk_sha256": digest(apk.read_bytes()),
        "diagnostic_only": True,
        "app_id": app_id,
        "target_sdk": target_sdk,
        "included_assets": [],
        "omitted_native_libraries": [],
        "ane_ids_removed_from_descriptor": [],
        "warning": (
            "This workspace excludes the original ARM32 native libraries and ANEs. "
            "It is a runtime/package diagnostic, not a feature-complete Photoshop Touch port."
        ),
    }
    with zipfile.ZipFile(apk) as zf:
        names = set(zf.namelist())
        descriptor_name = "assets/META-INF/AIR/application.xml"
        swf_name = "assets/TTPixel.swf"
        if descriptor_name not in names or swf_name not in names:
            raise ValueError("APK must contain the AIR descriptor and assets/TTPixel.swf")

        # Map APK assets to the application root expected by ADT.
        copy_map = {
            swf_name: Path("TTPixel.swf"),
            "assets/CABConfig.xml": Path("CABConfig.xml"),
            "assets/adobeair.vch": Path("adobeair.vch"),
        }
        for name in names:
            # ZIP archives may include explicit directory entries. Do not try to
            # write those entries as files; only copy actual asset payloads.
            if name.endswith("/"):
                continue
            if name.startswith("assets/resource/"):
                copy_map[name] = Path(name.removeprefix("assets/"))
            elif name.startswith("assets/icons/"):
                copy_map[name] = Path(name.removeprefix("assets/"))
            elif name.startswith("assets/META-INF/AIR/extensions/"):
                copy_map[name] = Path("ane-evidence") / Path(name).relative_to("assets/META-INF/AIR/extensions")
            elif name.startswith("lib/") and name.endswith(".so"):
                inventory["omitted_native_libraries"].append({
                    "path": name, "size_bytes": zf.getinfo(name).file_size,
                    "reason": "Original APK native libraries are ARM32 and cannot be loaded in an ARM64-only package.",
                })

        for source_name, relative in copy_map.items():
            if source_name not in names:
                continue
            data = zf.read(source_name)
            destination = out / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            inventory["included_assets"].append({
                "source": source_name, "path": relative.as_posix(),
                "size_bytes": len(data), "sha256": digest(data),
                "packaged": not relative.parts[0] == "ane-evidence",
            })

        descriptor = ET.fromstring(zf.read(descriptor_name))
        for child in list(descriptor):
            if local_name(child.tag) == "extensions":
                inventory["ane_ids_removed_from_descriptor"] = [
                    (element.text or "").strip()
                    for element in child.iter()
                    if local_name(element.tag) == "extensionID" and (element.text or "").strip()
                ]
                descriptor.remove(child)
        for element in descriptor.iter():
            tag = local_name(element.tag)
            if tag == "id":
                element.text = app_id
            elif tag == "filename":
                element.text = "PSTouchARM64Diagnostic"
            elif tag == "versionNumber":
                element.text = "1.7.8"
            elif tag == "versionLabel":
                element.text = "1.7.8 ARM64 diagnostic"
            elif tag == "manifestAdditions" and element.text:
                try:
                    manifest = ET.fromstring(element.text)
                except ET.ParseError as exc:
                    raise ValueError(f"Cannot parse embedded Android manifest additions: {exc}") from exc
                for parent in manifest.iter():
                    for child in list(parent):
                        child_tag = local_name(child.tag)
                        android_name = child.attrib.get(f"{{{ANDROID_NS}}}name", "")
                        if child_tag in {"service", "receiver"} and "C2DMReceiver" in android_name:
                            parent.remove(child)
                        elif child_tag == "uses-permission" and "c2dm.permission" in android_name.lower():
                            parent.remove(child)
                for uses_sdk in manifest.iter():
                    if local_name(uses_sdk.tag) == "uses-sdk":
                        uses_sdk.set(f"{{{ANDROID_NS}}}targetSdkVersion", str(target_sdk))
                element.text = ET.tostring(manifest, encoding="unicode")
        (out / "application.xml").write_bytes(
            ET.tostring(descriptor, encoding="utf-8", xml_declaration=True)
        )

    inventory["included_assets"].sort(key=lambda item: item["path"])
    inventory["omitted_native_libraries"].sort(key=lambda item: item["path"])
    (out / "original-air-workspace.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--app-id", default="com.frolicworks.pstoucharm64diagnostic")
    parser.add_argument("--target-sdk", type=int, default=35)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+", args.app_id):
        parser.error("--app-id must be a reverse-DNS identifier")
    if args.target_sdk < 23 or args.target_sdk > 36:
        parser.error("--target-sdk must be between 23 and 36")
    try:
        result = prepare(args.apk.resolve(), args.out.resolve(), args.app_id, args.target_sdk)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(f"Prepared {len(result['included_assets'])} original asset files in {args.out}")
    print(f"Preserved original SWF; removed {len(result['ane_ids_removed_from_descriptor'])} ANE declarations.")
    print("This is a no-ANE diagnostic workspace, not an APK and not a feature-complete port.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
