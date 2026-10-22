#!/usr/bin/env python3
"""Compare two APK variants before reusing patches or native rebuild assumptions."""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from decode_axml import parse_axml


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def summarize(path: Path) -> dict:
    result = {
        "file": path.name, "size_bytes": path.stat().st_size,
        "package": None, "version_code": None, "version_name": None,
        "air_descriptor": {}, "swf_files": {}, "abis": [],
        "native_libraries": [], "ane_extensions": [],
    }
    with zipfile.ZipFile(path) as apk:
        names = apk.namelist()
        if "AndroidManifest.xml" in names:
            try:
                result.update(parse_axml(apk.read("AndroidManifest.xml")))
            except Exception as exc:
                result["manifest_error"] = str(exc)
        libs = [n for n in names if n.startswith("lib/") and n.endswith(".so")]
        result["native_libraries"] = [
            {"path": n, "size_bytes": apk.getinfo(n).file_size,
             "sha256": digest(apk.read(n))}
            for n in libs
        ]
        result["abis"] = sorted({n.split("/")[1] for n in libs if len(n.split("/")) > 2})
        for name in names:
            if name.lower().endswith(".swf"):
                result["swf_files"][name] = {
                    "size_bytes": apk.getinfo(name).file_size,
                    "sha256": digest(apk.read(name)),
                }
        descriptor = "assets/META-INF/AIR/application.xml"
        if descriptor in names:
            root = ET.fromstring(apk.read(descriptor))
            flat = {}
            for element in root.iter():
                key = element.tag.split("}")[-1]
                value = (element.text or "").strip()
                if key in {"id", "versionNumber", "versionLabel", "filename", "content"} and value:
                    flat[key] = value
            result["air_descriptor"] = flat
        for name in names:
            if name.endswith("/META-INF/ANE/extension.xml"):
                try:
                    root = ET.fromstring(apk.read(name))
                    platforms = sorted({
                        platform.attrib.get("name", "")
                        for platform in root.findall(".//{*}platform")
                    })
                    result["ane_extensions"].append({
                        "id": root.findtext("{*}id"),
                        "version": root.findtext("{*}versionNumber"),
                        "platforms": platforms,
                        "descriptor_path": name,
                    })
                except ET.ParseError as exc:
                    result["ane_extensions"].append({"descriptor_path": name, "parse_error": str(exc)})
    result["ane_extensions"].sort(key=lambda item: (item.get("id") or "", item["descriptor_path"]))
    return result


def compare(left: dict, right: dict) -> dict:
    left_swf = left["swf_files"]
    right_swf = right["swf_files"]
    common_swf = sorted(set(left_swf) & set(right_swf))
    swf_matches = {
        name: left_swf[name]["sha256"] == right_swf[name]["sha256"]
        for name in common_swf
    }
    left_anes = {x.get("id"): x.get("platforms") for x in left["ane_extensions"]}
    right_anes = {x.get("id"): x.get("platforms") for x in right["ane_extensions"]}
    return {
        "left": left,
        "right": right,
        "comparison": {
            "same_android_package": left.get("package") == right.get("package"),
            "same_air_app_id": left["air_descriptor"].get("id") == right["air_descriptor"].get("id"),
            "same_abis": left["abis"] == right["abis"],
            "common_swf_hash_matches": swf_matches,
            "swf_paths_only_left": sorted(set(left_swf) - set(right_swf)),
            "swf_paths_only_right": sorted(set(right_swf) - set(left_swf)),
            "ane_ids_only_left": sorted(set(left_anes) - set(right_anes)),
            "ane_ids_only_right": sorted(set(right_anes) - set(left_anes)),
            "ane_platforms_left": left_anes,
            "ane_platforms_right": right_anes,
        },
        "warning": "Similarity is evidence only. It does not prove bytecode/API compatibility, licensing permission, or that patches can be reused safely.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path, help="First APK")
    parser.add_argument("right", type=Path, help="Second APK")
    parser.add_argument("--out", type=Path, default=Path("build/variant-compare"))
    args = parser.parse_args()
    for path in (args.left, args.right):
        if not path.is_file():
            parser.error(f"APK not found: {path}")
    result = compare(summarize(args.left), summarize(args.right))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "comparison.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    comp = result["comparison"]
    lines = [
        "# APK variant comparison", "",
        f"- Left: {result['left']['file']} ({result['left'].get('package')})",
        f"- Right: {result['right']['file']} ({result['right'].get('package')})",
        f"- Same Android package: {comp['same_android_package']}",
        f"- Same AIR application ID: {comp['same_air_app_id']}",
        f"- Same native ABIs: {comp['same_abis']}", "",
        "## Common SWF files", "",
    ]
    lines += [f"- {name}: SHA-256 {'MATCH' if same else 'DIFFERENT'}" for name, same in comp["common_swf_hash_matches"].items()] or ["- No identically named SWF files in common."]
    lines += ["", "## ANE platforms", ""]
    lines += [f"- Left {name}: {', '.join(platforms or [])}" for name, platforms in comp["ane_platforms_left"].items()] or ["- None found on left."]
    lines += [f"- Right {name}: {', '.join(platforms or [])}" for name, platforms in comp["ane_platforms_right"].items()] or ["- None found on right."]
    lines += ["", "## Warning", "", result["warning"], ""]
    (args.out / "comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out / 'comparison.md'}")
    print(f"Wrote {args.out / 'comparison.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
