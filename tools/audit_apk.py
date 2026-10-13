#!/usr/bin/env python3
"""Static APK inventory; does not modify or repackage the APK."""
import argparse, hashlib, json, re, shutil, subprocess, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def tool(name, args):
    exe = shutil.which(name)
    if not exe:
        return {"available": False}
    try:
        p = subprocess.run([exe, *args], capture_output=True, text=True, timeout=30)
        return {"available": True, "returncode": p.returncode,
                "stdout": p.stdout[:10000], "stderr": p.stderr[:2000]}
    except Exception as e:
        return {"available": True, "error": str(e)}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("apk", type=Path)
    ap.add_argument("--out", type=Path, default=Path("build/audit"))
    args = ap.parse_args()
    apk = args.apk.expanduser().resolve()
    if not apk.is_file():
        ap.error("APK not found: " + str(apk))
    args.out.mkdir(parents=True, exist_ok=True)
    d = {"file": apk.name, "size_bytes": apk.stat().st_size, "sha256": sha256(apk),
         "native_libraries": [], "architectures": [], "air_descriptor": {},
         "declared_ane_ids": [], "tools": {}}
    with zipfile.ZipFile(apk) as z:
        names = z.namelist()
        libs = [n for n in names if n.startswith("lib/") and n.endswith(".so")]
        d["entry_count"] = len(names)
        d["native_libraries"] = [{"path": n, "size_bytes": z.getinfo(n).file_size} for n in libs]
        d["architectures"] = sorted({n.split("/")[1] for n in libs if len(n.split("/")) > 2})
        d["dex_files"] = [n for n in names if re.fullmatch(r"classes(?:\d+)?\.dex", n)]
        d["swf_files"] = [n for n in names if n.lower().endswith(".swf")]
        desc = "assets/META-INF/AIR/application.xml"
        if desc in names:
            root = ET.fromstring(z.read(desc))
            local = lambda tag: tag.split("}")[-1]
            flat = {}
            for e in root.iter():
                key, value = local(e.tag), (e.text or "").strip()
                if not value:
                    continue
                if key == "extensionID":
                    d["declared_ane_ids"].append(value)
                elif key in {"id", "filename", "name", "versionNumber", "versionLabel",
                             "content", "renderMode", "autoOrients", "aspectRatio", "fullScreen"}:
                    flat[key] = value
            d["air_descriptor"] = {"namespace": root.tag.split("}")[0].lstrip("{"), **flat}
    d["tools"]["aapt"] = tool("aapt", ["dump", "badging", str(apk)])
    d["tools"]["apkanalyzer"] = tool("apkanalyzer", ["manifest", "print", str(apk)])
    (args.out / "inventory.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
    lines = ["# APK static audit", "", "File: " + d["file"],
             "Size: " + str(d["size_bytes"]), "SHA-256: " + d["sha256"],
             "Native ABIs: " + (", ".join(d["architectures"]) or "none"),
             "Native .so count: " + str(len(d["native_libraries"])), "",
             "## AIR descriptor", ""]
    lines += [str(k) + ": " + str(v) for k, v in d["air_descriptor"].items()]
    lines += ["", "## Declared ANEs", ""] + d["declared_ane_ids"]
    lines += ["", "## Native libraries", ""] + [x["path"] for x in d["native_libraries"]]
    lines += ["", "## Important limitation",
              "This is static inventory only. AndroidManifest.xml is binary AXML; use aapt, apkanalyzer or Apktool to decode it.",
              "Changing the manifest or renaming ELF32 ARM libraries cannot convert them to ARM64.",
              "A real port requires a compatible AIR runtime and ARM64 builds of all required native extensions."]
    (args.out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote " + str(args.out / "report.md"))
    print("Wrote " + str(args.out / "inventory.json"))

if __name__ == "__main__":
    main()
