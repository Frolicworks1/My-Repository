#!/usr/bin/env python3
"""Fail-closed preflight for genuine ARM64 AIR/ANE migration inputs.

This does not build an APK. It checks that extracted ANE descriptors declare
Android ARM64 and that declared native libraries are real ELF64 AArch64 files.
"""
from __future__ import annotations

import argparse
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

ARM64_PLATFORM_NAMES = {"Android-ARM64", "Android-ARM64-v8a", "Android-ARM64-v8"}
AARCH64_MACHINE = 183


def elf_info(path: Path) -> dict:
    try:
        data = path.read_bytes()[:64]
    except OSError as exc:
        return {"is_elf": False, "error": str(exc)}
    if len(data) < 20 or data[:4] != b"\x7fELF":
        return {"is_elf": False}
    endian = "<" if data[5] == 1 else ">" if data[5] == 2 else None
    machine = struct.unpack_from(endian + "H", data, 18)[0] if endian else None
    return {
        "is_elf": True,
        "class": {1: "ELF32", 2: "ELF64"}.get(data[4], f"class-{data[4]}"),
        "machine": machine,
        "machine_name": {40: "ARM", 183: "AArch64"}.get(machine, str(machine)),
    }


def inspect(root: Path) -> dict:
    blockers = []
    extensions = []
    all_so = list(root.rglob("*.so"))
    for descriptor in sorted(root.rglob("extension.xml")):
        try:
            xml = ET.parse(descriptor).getroot()
        except (ET.ParseError, OSError) as exc:
            blockers.append(f"Cannot parse {descriptor.relative_to(root)}: {exc}")
            continue
        extension_id = xml.findtext("{*}id") or str(descriptor.parent)
        platforms = []
        for platform in xml.findall(".//{*}platform"):
            name = platform.attrib.get("name", "")
            deployment = platform.find("{*}applicationDeployment")
            native_name = deployment.findtext("{*}nativeLibrary") if deployment is not None else None
            item = {"name": name, "native_library": native_name}
            if name in ARM64_PLATFORM_NAMES:
                if native_name:
                    matches = [p for p in all_so if p.name == Path(native_name).name]
                    if not matches:
                        blockers.append(f"{extension_id}: ARM64 descriptor names {native_name}, but no matching .so exists in extracted inputs.")
                    elif not any((lambda info: info.get("is_elf") and info.get("class") == "ELF64" and info.get("machine") == AARCH64_MACHINE)(elf_info(p)) for p in matches):
                        blockers.append(f"{extension_id}: {native_name} exists but no matching ELF64/AArch64 library was found.")
                else:
                    blockers.append(f"{extension_id}: ARM64 platform entry has no nativeLibrary declaration; verify whether this is intentionally pure ActionScript.")
            platforms.append(item)
        if not any(p["name"] in ARM64_PLATFORM_NAMES for p in platforms):
            blockers.append(f"{extension_id}: no Android ARM64 platform entry in {descriptor.relative_to(root)}.")
        extensions.append({"id": extension_id, "descriptor": str(descriptor.relative_to(root)), "platforms": platforms})
    if not extensions:
        blockers.append("No ANE extension.xml descriptors found; input extraction may be incomplete.")
    native = []
    for path in all_so:
        native.append({"path": str(path.relative_to(root)), **elf_info(path)})
    return {
        "input_directory": str(root),
        "status": "blocked" if blockers else "preflight-passed",
        "blockers": blockers,
        "ane_extensions": extensions,
        "native_libraries": native,
        "limitations": [
            "A passed preflight is not proof that the ANE loads or behaves correctly at runtime.",
            "This tool does not compile, patch, sign, or create an APK.",
            "AIR runtime/API compatibility and device testing remain separate gates."
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path, help="Extracted AIR migration input directory")
    parser.add_argument("--out", type=Path, default=Path("build/arm64-preflight"))
    args = parser.parse_args()
    root = args.input_dir.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"input directory not found: {root}")
    report = inspect(root)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "preflight.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# ARM64 ANE build preflight", "", f"- Status: **{report['status']}**", f"- Input: `{root}`", "", "## Blockers", ""]
    lines += [f"- {x}" for x in report["blockers"]] or ["- No static blockers found."]
    lines += ["", "## Native library architecture", ""]
    lines += [f"- `{x['path']}`: {x.get('class', 'not ELF')} / {x.get('machine_name', 'unknown')}" for x in report["native_libraries"]] or ["- No .so files found."]
    lines += ["", "## Limitations", ""] + [f"- {x}" for x in report["limitations"]]
    (args.out / "preflight.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Status: {report['status']}")
    print(f"Report: {args.out / 'preflight.md'}")
    print(f"JSON: {args.out / 'preflight.json'}")
    return 0 if report["status"] == "preflight-passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
