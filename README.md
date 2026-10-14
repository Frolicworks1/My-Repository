# PS Touch Plus — ARM64 / Android 16 investigation

This branch contains a reproducible, non-destructive audit toolkit for the user-provided PS Touch Plus APK. It does not contain the proprietary APK or a falsely patched build.

## Current evidence

- Adobe AIR namespace 16.0; app ID com.adobe.pstouch, PS Touch 1.7.7.
- Main payload: assets/TTPixel.swf.
- Nine native shared objects are present under lib/armeabi-v7a/; no lib/arm64-v8a/ entries were found.
- Declared ANEs: com.adobe.ttpixel.extension, air.com.adobe.cc.sync.SyncEngine, air.com.adobe.cc.PushNotification.

A manifest/target-SDK edit cannot convert 32-bit ELF binaries to ARM64. A real port needs a compatible AIR runtime, ARM64 versions of required native libraries/ANEs, and Android 16 device testing.

## Run in GitHub Codespaces

Upload the APK privately into the workspace (for example input/PS Touch Plus.apk) without committing it, then run:

    python3 tools/audit_apk.py "input/PS Touch Plus.apk" --out build/audit

The script writes Markdown and JSON inventories. Android Build Tools are optional for extra decoded-manifest output. See [the Codespaces runbook](docs/CODESPACES_MIGRATION_RUNBOOK.md) for the private input workflow, and docs/REVERSE_ENGINEERING_NOTES.md for the migration plan and blockers.

## Next migration experiment (private workspace only)

The helper below extracts the original SWF, embedded ANE packages/descriptors, and native libraries into a local working folder so they can be tested against a current AIR SDK without committing proprietary payloads:

```sh
mkdir -p input
# Copy your own PS Touch Plus.apk into input/ in Codespaces.
python3 tools/audit_apk.py "input/PS Touch Plus.apk" --out build/audit
python3 tools/ane_compat_report.py "input/PS Touch Plus.apk" --out build/compatibility
python3 tools/prepare_air_migration.py "input/PS Touch Plus.apk" --out build/private-air-input
python3 tools/arm64_build_gate.py build/private-air-input --out build/arm64-preflight
```

Inspect `build/private-air-input/migration-input-inventory.json` and the extracted ANE `extension.xml` descriptors. Keep `input/` and `build/private-air-input/` out of Git. The extraction is not a build and cannot produce an installable ARM64 app by itself.

**Hard gate before packaging:** the current app includes a core TTPixel ANE with no Android ARM64 payload in the original package. Do not attempt to call an ARM32 library an ARM64 library. A package experiment can only move forward once a compatible AIR SDK is available and each required ANE has a real ARM64 implementation or is replaced by a tested code-level alternative. A no-ANE prototype may help test the AIR runtime/SWF startup, but is not expected to retain the editor's core functionality.


The ARM64 preflight is intentionally fail-closed: it returns exit code 2 when any extracted ANE lacks an Android ARM64 descriptor or a matching ELF64/AArch64 native library. This is a diagnostic gate, not an APK build.
