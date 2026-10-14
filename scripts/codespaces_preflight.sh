#!/usr/bin/env bash
# One-command, local-only diagnostic. Does not modify/sign/build an APK.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT="${1:-}"
if [[ -z "$INPUT" || ! -f "$INPUT" ]]; then
  echo "Usage: bash scripts/codespaces_preflight.sh <PS Touch Plus.apk|PS Touch Plus.zip>" >&2
  exit 64
fi
cd "$ROOT"
mkdir -p build/private-input
if [[ "$INPUT" == *.zip || "$INPUT" == *.ZIP ]]; then
  APK="$(python3 - "$INPUT" <<'PY'
from pathlib import Path
from zipfile import ZipFile
import sys
archive = Path(sys.argv[1]).expanduser().resolve()
with ZipFile(archive) as z:
    candidates = [n for n in z.namelist() if n.lower().endswith(".apk")]
    if len(candidates) != 1:
        raise SystemExit(f"Expected exactly one APK in ZIP; found {len(candidates)}: {candidates}")
    target = Path("build/private-input") / Path(candidates[0]).name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(z.read(candidates[0]))
    print(target)
PY
)" || exit $?
else
  APK="$(realpath "$INPUT")"
fi

echo "== Static APK inventory"
python3 tools/audit_apk.py "$APK" --out build/private-audit || exit $?
echo "== ABI / ANE compatibility report"
python3 tools/ane_compat_report.py "$APK" --out build/private-compat || exit $?
echo "== Preserve AIR migration inputs"
python3 tools/prepare_air_migration.py "$APK" --out build/private-air-input || exit $?
echo "== ARM64 preflight (exit 2 means the native port is blocked)"
python3 tools/arm64_build_gate.py build/private-air-input --out build/arm64-preflight
GATE_STATUS=$?
echo
echo "Reports:"
echo "  build/private-audit/report.md"
echo "  build/private-compat/report.md"
echo "  build/private-air-input/migration-input-inventory.json"
echo "  build/arm64-preflight/preflight.md"
if [[ "$GATE_STATUS" -eq 0 ]]; then
  echo "Static preflight passed; runtime compatibility and device testing are still required."
  exit 0
fi
echo "ARM64 build remains blocked. Do not treat this diagnostic run as an APK build."
exit "$GATE_STATUS"
