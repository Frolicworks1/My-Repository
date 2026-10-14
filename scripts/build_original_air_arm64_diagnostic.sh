#!/usr/bin/env bash
set -euo pipefail

# Build a diagnostic package from the original compiled SWF, not the native demo.
# The supplied ANEs are ARM32-only, so this first experiment deliberately omits
# them to test AIR packaging/runtime compatibility before implementing replacements.
if [[ $# -lt 1 ]]; then
  echo "Usage: AIRSDK_HOME=/path/to/AIRSDK AIR_CERT_PASSWORD='...' $0 /path/to/PS\ Touch\ Plus.apk" >&2
  exit 2
fi
INPUT="$1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AIRSDK_HOME="${AIRSDK_HOME:-}"
if [[ -z "$AIRSDK_HOME" || ! -f "$AIRSDK_HOME/lib/adt.jar" ]]; then
  echo "Set AIRSDK_HOME to a locally installed HARMAN AIR SDK (license accepted by you)." >&2
  exit 2
fi
for tool in java python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Required tool not found on PATH: $tool" >&2
    exit 2
  fi
done
if ! java -version >/dev/null 2>&1; then
  echo "Java is installed but cannot run; check JAVA_HOME and the runtime." >&2
  exit 2
fi
if [[ ! -f "$INPUT" ]]; then
  echo "Input APK/ZIP not found: $INPUT" >&2
  exit 2
fi
if [[ -z "${AIR_CERT_PASSWORD:-}" ]]; then
  echo "Set AIR_CERT_PASSWORD for a temporary test signing certificate." >&2
  exit 2
fi
mkdir -p "$ROOT/build"
if [[ "$INPUT" == *.zip ]]; then
  APK="$ROOT/build/private-input/PS-Touch-Plus.apk"
  mkdir -p "$(dirname "$APK")"
  python3 - "$INPUT" "$APK" <<'PY'
import sys, zipfile
from pathlib import Path
source, target = Path(sys.argv[1]), Path(sys.argv[2])
if not source.is_file():
    raise SystemExit(f"Input ZIP not found: {source}")
with zipfile.ZipFile(source) as z:
    candidates = [n for n in z.namelist() if n.lower().endswith(".apk") and not n.endswith("/")]
    if len(candidates) != 1:
        raise SystemExit(f"Expected exactly one APK inside ZIP, found {len(candidates)}")
    target.write_bytes(z.read(candidates[0]))
print(f"Extracted {candidates[0]} to {target}")
PY
else
  APK="$INPUT"
fi
if [[ ! -f "$APK" ]]; then
  echo "Input APK/ZIP not found: $INPUT" >&2
  exit 2
fi
# Fail before preparing the workspace if the APK is corrupt or lacks the
# original AIR descriptor/SWF. This avoids leaving a misleading partial build.
python3 - "$APK" <<'PY'
import sys, zipfile
from pathlib import Path
apk = Path(sys.argv[1])
try:
    with zipfile.ZipFile(apk) as z:
        corrupt = z.testzip()
        if corrupt:
            raise SystemExit(f"Input APK has a corrupt ZIP member: {corrupt}")
        names = set(z.namelist())
        required = {"assets/META-INF/AIR/application.xml", "assets/TTPixel.swf"}
        missing = sorted(required - names)
        if missing:
            raise SystemExit(f"Input APK is missing required original AIR files: {missing}")
except zipfile.BadZipFile as exc:
    raise SystemExit(f"Input is not a valid APK/ZIP archive: {exc}")
print(f"Input archive preflight passed: {apk} ({apk.stat().st_size:,} bytes)")
PY
OUT="${PS_TOUCH_AIR_OUT:-$ROOT/build/original-air-arm64-diagnostic}"
if [[ -e "$OUT" ]]; then
  echo "Output already exists: $OUT (remove it or set PS_TOUCH_AIR_OUT)." >&2
  exit 2
fi
python3 "$ROOT/tools/prepare_original_air_workspace.py" "$APK" --out "$OUT"
CERT="$ROOT/build/ps-touch-arm64-diagnostic.p12"
if [[ ! -f "$CERT" ]]; then
  java -jar "$AIRSDK_HOME/lib/adt.jar" -certificate \
    -cn "PS Touch ARM64 diagnostic" 2048-RSA "$CERT" "$AIR_CERT_PASSWORD"
fi
java -jar "$AIRSDK_HOME/lib/adt.jar" -package \
  -target apk-captive-runtime -arch armv8 \
  -storetype pkcs12 -keystore "$CERT" -storepass "$AIR_CERT_PASSWORD" \
  "$OUT/PS-Touch-Original-SWF-ARM64-Diagnostic.apk" \
  "$OUT/application.xml" \
  -C "$OUT" TTPixel.swf CABConfig.xml adobeair.vch icons resource
APK_OUT="$OUT/PS-Touch-Original-SWF-ARM64-Diagnostic.apk"
if [[ ! -s "$APK_OUT" ]]; then
  echo "ADT returned without creating the expected APK." >&2
  exit 1
fi
if command -v aapt >/dev/null 2>&1; then
  aapt dump badging "$APK_OUT" > "$OUT/aapt-badging.txt"
fi
python3 - "$APK_OUT" "$OUT/TTPixel.swf" <<'PY'
import hashlib, struct, sys, zipfile
from pathlib import Path
apk, original_swf = Path(sys.argv[1]), Path(sys.argv[2])
with zipfile.ZipFile(apk) as z:
    names = set(z.namelist())
    libs = [n for n in names if n.startswith("lib/") and n.endswith(".so")]
    arm64 = [n for n in libs if n.startswith("lib/arm64-v8a/")]
    non_arm64 = [n for n in libs if not n.startswith("lib/arm64-v8a/")]
    bad = []
    for name in arm64:
        data = z.read(name)
        if len(data) < 20 or data[:4] != b"\\x7fELF":
            bad.append((name, "not ELF"))
            continue
        elf_class = data[4]
        machine = struct.unpack_from("<H", data, 18)[0]
        if elf_class != 2 or machine != 183:
            bad.append((name, f"ELF class={elf_class}, machine={machine}"))
    required = {"AndroidManifest.xml", "TTPixel.swf", "CABConfig.xml"}
    missing = sorted(required - names)
    if missing:
        raise SystemExit(f"APK missing required entries: {missing}")
    packaged_swf = z.read("TTPixel.swf")
    source_swf = original_swf.read_bytes()
    if hashlib.sha256(packaged_swf).digest() != hashlib.sha256(source_swf).digest():
        raise SystemExit("The packaged TTPixel.swf differs from the prepared original SWF.")
    print(f"APK: {apk} ({apk.stat().st_size:,} bytes)")
    print(f"Native libraries: {len(libs)}; ARM64 libraries: {len(arm64)}; non-ARM64 libraries: {len(non_arm64)}")
    print(f"Original SWF SHA-256 preserved: {hashlib.sha256(packaged_swf).hexdigest()}")
    if not arm64 or non_arm64 or bad:
        print("ARM64 verification failed:", {"non_arm64": non_arm64, "bad_elf": bad})
        raise SystemExit(1)
print("Structural ARM64 package check passed; runtime feature compatibility is NOT proven.")
PY
if command -v apksigner >/dev/null 2>&1; then
  apksigner verify --verbose "$APK_OUT"
else
  echo "WARNING: apksigner not found on PATH; signing verification skipped (ADT signing was requested)." >&2
fi
echo "Diagnostic APK: $APK_OUT"
echo "This APK intentionally omits original ANEs; test startup only and expect editing features may fail."
