# Verified blockers from the uploaded PS Touch Plus APK

This report records static facts checked against the user-provided `PS Touch Plus.apk` extracted from `PS Touch Plus.zip` on 2026-10-14. The APK itself is not committed to this repository.

## Architecture findings

- All 9 packaged shared libraries are under `lib/armeabi-v7a/`.
- No `lib/arm64-v8a/` library directory was present.
- The ANE descriptors for all three extensions declare `Android-ARM`, not Android ARM64.
- This is not fixed by changing the manifest, target SDK, package name, or library directory.

## Native libraries present

| Library | Packaged size (bytes) |
|---|---:|
| `libCore.so` | 24,916,940 |
| `libTTPixelExtensionAndroid.so` | 2,322,840 |
| `libair.com.adobe.cc.sync.SyncEngine.so` | 16,392 |
| `libgdx-audio.so` | 318,300 |
| `libsibsynclib.so` | 2,332,068 |
| `libstagefright_froyo.so` | 9,016 |
| `libstagefright_honeycomb.so` | 13,112 |
| `libstlport_shared.so` | 619,452 |
| `libysshared.so` | 843,731 |

## ANE declarations checked

- `com.adobe.ttpixel.extension`: `Android-ARM`, native library field `library.jar`; its platform payload is an embedded `library.swf`. Its name and exported extension classes make it a key compatibility risk. A genuine ARM64 implementation or a tested replacement is needed.
- `air.com.adobe.cc.sync.SyncEngine`: `Android-ARM`, native library field `libAdobeSyncEngineBridge.so`. A compatible ARM64 build or evidence-backed removal/replacement is required.
- `air.com.adobe.cc.PushNotification`: `Android-ARM`, native library field `AdobeC2DMLibrary.jar`; it is a legacy C2DM extension. It may be removable only after testing startup and feature dependencies.

## Build gate and honest status

The automated preflight in `tools/arm64_build_gate.py` now handles the important distinction that an ANE descriptor may name a Java JAR while JNI shared objects are packaged separately. It blocks such JAR payloads for manual inspection rather than incorrectly matching the JAR filename to a `.so`.

The CI fixture tests pass, including:
- ARM32-only ANE rejected.
- An Android ARM64 descriptor with an ELF64/AArch64 shared library passes the static architecture gate.
- An Android ARM64 descriptor naming a Java JAR remains blocked until its contents and JNI dependencies receive manual review.

**No installable ARM64 APK has been built or device-tested.** The remaining work is not just packaging: source or ARM64 implementations are needed for the relevant closed-source native dependencies, then the app must be rebuilt, signed, installed and functionally tested on Android 16.
