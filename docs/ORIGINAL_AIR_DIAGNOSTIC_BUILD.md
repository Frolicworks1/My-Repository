# Building the original-SWF ARM64 diagnostic package

This route is now prepared to test the **original compiled Photoshop Touch SWF** under a current AIR runtime. It is intentionally separate from `rebuild/android/`, which is the already-working native prototype.

## Why the first package is diagnostic-only

The original APK contains the full resource tree (`assets/resource/`), `CABConfig.xml`, icons, `TTPixel.swf`, and an AIR descriptor. It also contains nine ARM32 native libraries and three ARM-only ANE declarations. The APK does not preserve complete standalone ANE archives with all their native payloads. A current AIR SDK can target Android ARM64, but it cannot convert these missing ARM64 extension implementations automatically.

The first experiment therefore:
- preserves the original SWF and resource tree in ADT's expected file layout;
- gives the diagnostic app a separate application ID so it can coexist with the original;
- raises the target SDK to 35 for a modern-Android test;
- removes the three ANE declarations and legacy C2DM manifest components;
- excludes all original ARM32 libraries from the package;
- packages the result with a current AIR captive runtime for `armv8`.

This test can tell us whether the original SWF and assets can be loaded by the current runtime. It **cannot** be called the complete app: missing TTPixel services may stop the gallery, editor, filters, selection tools, or image processing from working.

## Run in Codespaces

Install the HARMAN AIR SDK using its official manager and personally accept its license terms first:
https://airsdk.dev/docs/basics/getting-started

Upload the original ZIP in the Codespace (the script extracts its single APK safely), then run:

```bash
export AIRSDK_HOME="$HOME/AIRSDK"
export AIR_CERT_PASSWORD='choose-a-temporary-test-password'
bash scripts/build_original_air_arm64_diagnostic.sh "/path/to/PS Touch Plus.zip"
```

The build script stops if the SDK or password is missing. It does not download or silently accept the SDK license. The diagnostic APK and temporary signing certificate stay under ignored local `build/` output and are not committed to Git.

## Pass/fail criteria

A packaging pass requires a generated APK with `lib/arm64-v8a/` ELF64/AArch64 libraries and a valid signature. That is only the packaging gate. The next gate is installation and launch on the target Android 16 device, followed by logging all missing ANE classes and calls. If TTPixel is required for the first editor screen, the next engineering milestone is an ARM64 replacement for its API surface—not another manifest edit.

Official AIR documentation:
- https://airsdk.dev/docs/building/air-developer-tool/commands/package
- https://airsdk.dev/docs/building/using-native-extensions
