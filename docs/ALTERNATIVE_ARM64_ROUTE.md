# Practical route to a real Android ARM64 app

## Why the current compatibility path is blocked

The uploaded APK was inspected locally on 2026-10-14:
- package ID: `air.com.adobe.pstouch`
- version: 2.1 (versionCode 1007007)
- nine native shared libraries, all under `lib/armeabi-v7a/`
- the three embedded ANE descriptors declare `Android-ARM`, not Android ARM64
- no original ActionScript project or native-extension source project is packaged in the APK

The ARM64 preflight gate and static CI can verify inputs, but cannot synthesize missing ARM64 implementations from the original binary.

## Two distinct routes

### Route A — patch the legacy AIR app
Useful only on devices whose Android build can still execute 32-bit ARM apps and whose Android version allows installation after the legacy target-SDK restriction is handled. It is not a solution for a 64-bit-only Android 16 device. Repackaging or changing the manifest does not convert ARMv7 machine code to AArch64.

### Route B — clean-room native ARM64 rebuild
A public, related project is available at https://github.com/Vauzi-17/pscc. It describes a native Rust + wgpu + Kotlin Android editor prototype and a separate patch pipeline. This is a research lead, not a drop-in dependency:
- its README describes a PS CC phone-oriented variant and a different mod package ID;
- this project's uploaded APK is `air.com.adobe.pstouch`, so compatibility of SWF version, resource layout, ANE APIs and patch assumptions must be proven before reusing any workflow;
- its repository currently documents a phase-0 engine spike, not full feature parity with the legacy app;
- no code or assets from that repository are copied into this project. Treat it as a reference for architecture and test planning unless its license and compatibility are independently established.

For an Android 16 device that cannot run 32-bit apps, Route B is the technically credible long-term path. It is a rewrite, not a binary conversion, and must be built and tested incrementally.

## Recommended next milestone

1. Compare the two variants using package name, version, SWF hash, manifest, ANE descriptor IDs, and resource inventory.
2. Create an ARM64-only proof-of-life APK with a native editor canvas and verified input/render loop; sign it with a new test key.
3. Add a minimal document model, layers, brush/eraser, undo/redo, image import, save and export.
4. Add a PS Touch project importer only after the exact project format is documented and fixture tests exist.
5. Do not call it a PS Touch port until existing projects import correctly and core workflows pass on the user's Android 16 device.

## Release gates

- APK contains `lib/arm64-v8a/` libraries that are ELF64/AArch64.
- APK signature verifies; install succeeds on the target Android 16 device.
- Cold launch, canvas rendering, touch input, brush, erase, save/reopen, import/export and memory-pressure tests pass.
- Any unsupported legacy project features are explicitly reported; no claim of full compatibility based solely on launching a demo.

**Status:** The investigation and automated static tooling are progressing, but there is no installable ARM64 build of the uploaded app yet. This route requires native implementation work and cannot honestly be completed by manifest edits alone.


## Native prototype work started (2026-10-14)
A separate module now exists at `rebuild/android/`. It is a Java/Dex Android app targeting API 36, with no copied proprietary libraries. Current first-milestone features are touch drawing, brush/eraser, cycling brush colors, undo/clear, image import as a reference/background, and PNG export through MediaStore. The new workflow `.github/workflows/build-arm64-prototype.yml` builds and uploads a debug APK artifact when the build and structural checks pass.

This prototype is architecture-neutral managed code and runs on ARM64 Android; it is **not** a native AArch64 binary and is **not** the original Photoshop Touch application. Its first build must pass CI and the APK must be installed and tested on the actual target device before claiming runtime success. Legacy project import, layers, selections, filters, text, pressure support and original PS Touch feature parity remain unimplemented.
