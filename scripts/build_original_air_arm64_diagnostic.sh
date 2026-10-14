#!/usr/bin/env bash
set -euo pipefail

# Build a diagnostic package from the original compiled SWF, not the native demo.
# The supplied ANEs are ARM32-only, so this first experiment deliberately omits
# them to test AIR packaging/runtime compatibility before implementing replacements.
if [[ $# -lt 1 ]]; then
  echo "Usage: AIRSDK_HOME=/path/to/AIRSDK AIR_CERT_PASSWORD='...' $0 /path/to/PS\ Touch\ Plus.apk" >&2
  exit 2
fi
APK="$1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AIRSDK_HOME="${AIRSDK_HOME:-}"
if [[ -z "$AIRSDK_HOME" || ! -f "$AIRSDK_HOME/lib/adt.jar" ]]; then
  echo "Set AIRSDK_HOME to a locally installed HARMAN AIR SDK (license accepted by you)." >&2
  exit 2
fi
if [[ -z "${AIR_CERT_PASSWORD:-}" ]]; then
  echo "Set AIR_CERT_PASSWORD for a temporary test signing certificate." >&2
  exit 2
fi
OUT="${PS_TOUCH_AIR_OUT:-$ROOT/build/original-air-arm64-diagnostic}"
mkdir -p "$ROOT/build"
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
python3 - "$APK_OUT" <<'PY'
import struct, sys, zipfile
from pathlib import Path
apk = Path(sys.argv[1])
with zipfile.ZipFile(apk) as z:
    libs = [n for n in z.namelist() if n.startswith("lib/") and n.endswith(".so")]
    arm64 = [n for n in libs if n.startswith("lib/arm64-v8a/")]
    bad = []
    for name in arm64:
        data = z.read(name)
        if len(data) < 20 or data[:4] != b"\x7fELF":
            bad.append((name, "not ELF"))
            continue
        elf_class = data[4]
        machine = struct.unpack_from("<H", data, 18)[0]
        if elf_class != 2 or machine != 183:
            bad.append((name, f"ELF class={elf_class}, machine={machine}"))
    print(f"APK: {apk} ({apk.stat().st_size:,} bytes)")
    print(f"Native libraries: {len(libs)}; ARM64 libraries: {len(arm64)}")
    if not arm64 or bad:
        print("ARM64 verification failed:", bad)
        raise SystemExit(1)
print("Structural ARM64 package check passed; runtime feature compatibility is NOT proven.")
PY
echo "Diagnostic APK: $APK_OUT"
echo "This APK intentionally omits original ANEs; test startup only and expect editing features may fail."
