#!/usr/bin/env python3
"""Report Android ABI, AIR Native Extension and legacy-runtime signals from an APK.

Static triage only: DEX strings are not decompiled code and do not prove a
feature executes. No APK is modified and no files are uploaded.
"""
from __future__ import annotations
import argparse, json, re, struct, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from decode_axml import parse_axml

LEGACY_MARKERS = (
    "C2DM", "com.google.android.c2dm", "libstagefright.so",
    "getExternalStorageDirectory", "WRITE_EXTERNAL_STORAGE",
    "requestLegacyExternalStorage", "targetSdkVersion",
)

def elf_summary(data: bytes) -> dict:
    if len(data) < 20 or data[:4] != b"\x7fELF":
        return {"is_elf": False}
    cls = {1: "ELF32", 2: "ELF64"}.get(data[4], f"class-{data[4]}")
    endian = "<" if data[5] == 1 else ">" if data[5] == 2 else None
    machine = struct.unpack_from(endian + "H", data, 18)[0] if endian else None
    machine_name = {3: "x86", 40: "ARM", 62: "x86_64", 183: "AArch64"}.get(machine, str(machine))
    return {"is_elf": True, "class": cls, "machine": machine, "machine_name": machine_name}

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("apk", type=Path)
    ap.add_argument("--out", type=Path, default=Path("build/ane-report"))
    args = ap.parse_args()
    if not args.apk.is_file():
        ap.error(f"APK not found: {args.apk}")
    report = {"apk": args.apk.name, "abis": [], "native_libraries": [],
              "ane_extensions": [], "legacy_markers": {}, "manifest": {},
              "findings": [], "limitations": [
                  "DEX inspection is printable-string triage, not decompilation.",
                  "Presence of a string does not prove the corresponding code path runs.",
                  "Static inspection cannot establish Android 16 launch or feature compatibility."]}
    with zipfile.ZipFile(args.apk) as z:
        names = z.namelist()
        libs = [n for n in names if n.startswith("lib/") and n.endswith(".so")]
        report["abis"] = sorted({n.split("/")[1] for n in libs if len(n.split("/")) > 2})
        for name in libs:
            info = elf_summary(z.read(name)[:64])
            report["native_libraries"].append({"path": name, **info})
        if "AndroidManifest.xml" in names:
            try:
                report["manifest"] = parse_axml(z.read("AndroidManifest.xml"))
            except Exception as exc:
                report["manifest"] = {"decode_error": str(exc)}
        for name in names:
            if name.endswith("/META-INF/ANE/extension.xml"):
                try:
                    root = ET.fromstring(z.read(name))
                    platforms = []
                    for platform in root.findall(".//{*}platform"):
                        deployment = platform.find("{*}applicationDeployment")
                        platforms.append({
                            "name": platform.attrib.get("name"),
                            "nativeLibrary": deployment.findtext("{*}nativeLibrary") if deployment is not None else None,
                            "initializer": deployment.findtext("{*}initializer") if deployment is not None else None,
                            "finalizer": deployment.findtext("{*}finalizer") if deployment is not None else None,
                        })
                    report["ane_extensions"].append({
                        "path": name, "id": root.findtext("{*}id"),
                        "version": root.findtext("{*}versionNumber"), "platforms": platforms,
                    })
                except ET.ParseError as exc:
                    report["ane_extensions"].append({"path": name, "parse_error": str(exc)})
        dex_text = []
        for name in names:
            if re.fullmatch(r"classes(?:\d+)?\.dex", name):
                blob = z.read(name)
                dex_text.extend(x.decode("ascii", "ignore") for x in re.findall(rb"[\x20-\x7e]{5,}", blob))
        for marker in LEGACY_MARKERS:
            hits = sorted({s for s in dex_text if marker.lower() in s.lower()})
            if hits:
                report["legacy_markers"][marker] = hits[:12]
    if "arm64-v8a" not in report["abis"]:
        report["findings"].append({"severity": "blocker", "id": "no-arm64-native-libraries",
                                   "detail": "No packaged AArch64 native libraries found; this APK is not a native ARM64 build."})
    for ane in report["ane_extensions"]:
        platforms = [p.get("name") for p in ane.get("platforms", [])]
        if not any(x in platforms for x in ("Android-ARM64", "Android-ARM64-v8a")):
            report["findings"].append({"severity": "blocker", "id": "ane-missing-arm64",
                                       "detail": f"ANE {ane.get('id')} has no explicit Android ARM64 platform entry."})
    if any("stagefright" in x["path"].lower() for x in report["native_libraries"]):
        report["findings"].append({"severity": "risk", "id": "legacy-stagefright",
                                   "detail": "Legacy Stagefright libraries are packaged; runtime compatibility needs device testing."})
    if any(k.lower() in ("c2dm", "com.google.android.c2dm") for k in report["legacy_markers"]):
        report["findings"].append({"severity": "risk", "id": "legacy-c2dm",
                                   "detail": "DEX strings suggest legacy C2DM push-notification integration."})
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "compatibility.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# AIR / ABI compatibility triage", "", f"- APK: {report['apk']}",
             f"- Packaged ABIs: {', '.join(report['abis']) or 'none'}", "", "## Findings", ""]
    lines.extend([f"- **{x['severity'].upper()} — {x['id']}**: {x['detail']}" for x in report["findings"]] or ["- No static findings from current rules."])
    lines += ["", "## ANE platform declarations", ""]
    for ane in report["ane_extensions"]:
        lines.append(f"- {ane.get('id', ane.get('path'))}")
        for platform in ane.get("platforms", []):
            lines.append(f"  - {platform.get('name')}: {platform.get('nativeLibrary')}")
    lines += ["", "## Legacy marker sample", ""]
    for marker, hits in report["legacy_markers"].items():
        lines.append(f"- {marker}: " + "; ".join(hits[:4]))
    lines += ["", "## Limitations", ""] + [f"- {x}" for x in report["limitations"]]
    (args.out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report: {args.out / 'report.md'}")
    print(f"JSON: {args.out / 'compatibility.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
