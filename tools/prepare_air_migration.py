#!/usr/bin/env python3
"""Extract private AIR migration inputs from a user-owned APK for local testing.

This does not modify, re-sign, or convert the APK. Extracted proprietary assets
are written only to the caller-selected local output directory; do not commit them.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("apk", type=Path)
    p.add_argument("--out", type=Path, default=Path("build/private-air-input"))
    args = p.parse_args()
    if not args.apk.is_file():
        p.error(f"APK not found: {args.apk}")
    args.out.mkdir(parents=True, exist_ok=True)
    inventory = {
        "source_apk_name": args.apk.name,
        "source_apk_sha256": hashlib.sha256(args.apk.read_bytes()).hexdigest(),
        "extracted": [],
        "native_abi_counts": {},
        "important_warning": (
            "Extraction is not an ARM64 port. This APK's ARM32 native libraries and "
            "ARM-only ANEs must be replaced or rebuilt for AArch64 before a true ARM64 build."
        ),
    }
    with zipfile.ZipFile(args.apk) as z:
        names = z.namelist()
        # Keep the SWF and ANE packages as migration inputs; preserve paths so ANE
        # descriptors can be inspected. Extract native libraries separately too.
        wanted = [
            n for n in names
            if n == "assets/TTPixel.swf"
            or n == "assets/META-INF/AIR/application.xml"
            # Keep the complete packaged ANE payload: descriptors, SWC/library
            # SWFs, Android platform payloads and nested native libraries.
            or n.startswith("assets/META-INF/AIR/extensions/")
            # Native libraries may be at APK root or nested inside an ANE.
            or (n.endswith(".so") and (n.startswith("lib/") or "/extensions/" in n))
        ]
        for name in wanted:
            data = z.read(name)
            destination = args.out / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            item = {"path": name, "size": len(data), "sha256": sha256(data)}
            if name.endswith(".so"):
                parts = name.split("/")
                if name.startswith("lib/") and len(parts) > 2:
                    abi = parts[1]
                elif "Android-ARM64" in parts:
                    abi = "ANE-Android-ARM64"
                elif "Android-ARM" in parts:
                    abi = "ANE-Android-ARM"
                else:
                    abi = "nested-or-unknown"
                inventory["native_abi_counts"][abi] = inventory["native_abi_counts"].get(abi, 0) + 1
            inventory["extracted"].append(item)
    (args.out / "migration-input-inventory.json").write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Extracted {len(inventory['extracted'])} migration inputs to: {args.out}")
    print(f"Source SHA-256: {inventory['source_apk_sha256']}")
    print("Reminder: this is an extraction bundle, not an installable APK.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
