# Codespaces runbook — private PS Touch Plus migration inputs

This workflow is for preparing evidence from an APK you own or are authorized to inspect. It does **not** make an ARM64 APK.

## 1. Keep the original APK private

In Codespaces, upload `PS Touch Plus.zip` or `PS Touch Plus.apk` into the workspace using the file explorer. Do not add it to a Git commit, release, issue, or pull request. The repository's CI deliberately fails if an APK is committed.

If you uploaded the ZIP, extract only the APK into a private working folder:

```bash
mkdir -p build/private-input
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile
archive = Path("PS Touch Plus.zip")
with ZipFile(archive) as z:
    candidates = [n for n in z.namelist() if n.lower().endswith(".apk")]
    if len(candidates) != 1:
        raise SystemExit(f"Expected exactly one APK, found: {candidates}")
    target = Path("build/private-input") / Path(candidates[0]).name
    target.write_bytes(z.read(candidates[0]))
    print(f"Extracted privately to {target}")
PY
```

If you uploaded the APK directly, set `APK` to its actual path instead.

## 2. Generate the evidence reports

```bash
APK="build/private-input/PS Touch Plus.apk"
python tools/audit_apk.py "$APK" --out build/private-audit
python tools/ane_compat_report.py "$APK" --out build/private-compat
python tools/prepare_air_migration.py "$APK" --out build/private-air-input
python tools/arm64_build_gate.py build/private-air-input --out build/arm64-preflight
```

Outputs remain under `build/` (which should stay untracked). The reports include the source SHA-256, packaged ABIs, ANE descriptors and extracted AIR payloads. The final command deliberately exits with code 2 while an ANE is missing a real ARM64 descriptor/library. Review the results before any rebuild attempt.

## 3. Do not fake ARM64 support

- Do not copy ARM32 `.so` files into an `arm64-v8a` directory or rename them.
- Do not bump `targetSdkVersion` and call that an ARM64 port.
- Do not delete TTPixel or SyncEngine just to get ADT to package; first determine which ActionScript APIs are referenced and run controlled startup/edit/export tests.
- Do not put proprietary source assets or the original APK into Git.

## 4. Build gate before attempting ADT packaging

A real build attempt requires a licensed/available AIR SDK and Android build dependencies, plus compatible ARM64 implementations for the required ANEs. The key unresolved dependency is the closed-source TTPixel native implementation. The presence of `Android-ARM` payloads only proves 32-bit support; it does not provide AArch64 code.

Once compatible ANEs exist, package a separate test APK with the selected AIR SDK, then inspect every `.so` ELF header and signature, install on the target Android 16 device, and test launch, open/save, import, selection/brush, text, export, camera and resume behavior. Keep the original APK unchanged as the baseline.
