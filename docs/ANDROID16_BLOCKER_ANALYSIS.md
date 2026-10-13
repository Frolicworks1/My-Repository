# Android 16 blocker analysis — PS Touch Plus

## Evidence collected from the supplied APK

This is static reverse engineering only. No rebuilt APK has been produced or tested on an Android 16 device.

- Android package ID: `air.com.adobe.pstouch`.
- Android manifest reports `minSdkVersion=12` and `targetSdkVersion=12` (Android 3.1-era API level).
- Application declares `hardwareAccelerated=false` and `largeHeap=true`.
- Manifest permissions include INTERNET, WRITE_EXTERNAL_STORAGE, CAMERA, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE and WAKE_LOCK.
- AIR descriptor identifies Adobe AIR application namespace 16.0, application version 1.7.7, main content `TTPixel.swf`.
- All 9 packaged native shared libraries are under `lib/armeabi-v7a/`; none are under `lib/arm64-v8a/`. ELF headers confirm 32-bit ARM.
- Three ANEs are embedded: `com.adobe.ttpixel.extension`, `air.com.adobe.cc.sync.SyncEngine`, and `air.com.adobe.cc.PushNotification`. Each embedded `extension.xml` declares Android-ARM only; no Android-ARM64 platform entry exists.
- The sync ANE requires `libAdobeSyncEngineBridge.so` (packaged as `libair.com.adobe.cc.sync.SyncEngine.so`, with SONAME `libAdobeSyncEngineBridge.so`) and depends on `libCore.so`.
- The TTPixel ANE supplies Java classes and native `libTTPixelExtensionAndroid.so`; it is likely central to editing features (GL, quick selection, import/export, pressure, image operations) based on class names visible in DEX strings.
- The APK includes legacy `libstagefright_froyo.so` and `libstagefright_honeycomb.so`, which reference old Android media libraries such as `libstagefright.so`, `libutils.so`, `libcutils.so`, `libgui.so`, and `libui.so`. These are a significant runtime-compatibility risk.
- The push-notification ANE uses legacy Google C2DM classes/actions, another likely obsolete integration.
- Compiled Android DEX and SWF are present, but no original Java/ActionScript source project has been found in the APK.

## What this means

This is not a simple “add an arm64 folder” job. A native 64-bit build requires compatible AArch64 versions of the AIR runtime/native libraries and every required native ANE. The embedded ANE descriptors currently only promise Android-ARM. ARM32 compatibility on 64-bit Android devices may vary by device/OS image, but it does not satisfy the requested native ARM64 support.

Separately, target SDK 12 is below the minimum accepted for ordinary installation on recent Android releases. Changing the manifest value alone is not a safe fix: old AIR APIs, scoped-storage changes, media APIs, native extensions, signing, and app lifecycle must be tested together. The original package is not debuggable, and the application sets hardware acceleration off; do not change either setting without a targeted test.

## Prioritized path

1. **Preserve baseline**: retain the original APK privately and record SHA-256; never commit proprietary APK content to the public repo.
2. **Establish install/runtime baseline**: decode the full manifest and record Android version/device ABI, install error, launch/crash logcat, storage/import/export behavior, camera, and editing workflows.
3. **Identify the AIR runtime provenance**: determine the exact embedded/runtime AIR generation and whether an official AIR SDK/runtime supports the needed modern Android target/ABI. Do not assume a modern SDK can rebuild old closed-source ANEs.
4. **ANE feasibility gate**:
   - obtain source or vendor-provided ARM64 builds for TTPixel and SyncEngine ANEs;
   - decide whether obsolete C2DM can be removed/replaced without breaking core app startup;
   - test or replace old Stagefright code paths.
   If required proprietary ANE source/binaries are unavailable, a genuine ARM64 port may be infeasible without reimplementation.
5. **Build a controlled compatibility prototype**: first test target-SDK/manifest and runtime changes on a copy, with reproducible signing and rollback. Do not label this an ARM64 port unless the APK contains AArch64 libraries and passes runtime tests.
6. **Validate**: install on Android 16, launch, open/create/save layered projects, import images, camera import, brush/selection/transform/text/export, memory pressure, rotation/resume, and inspect logcat. Compare results against the untouched baseline.

## Tools in this branch

- `tools/audit_apk.py`: APK inventory, architecture and AIR/ANE inventory.
- `tools/decode_axml.py`: read-only decoder for selected Android binary-manifest fields; standard-library only.
- Original APK and generated build artifacts are intentionally excluded from Git.

## Current status

**Confirmed blockers:** legacy target SDK; no ARM64 native libraries; no ARM64 ANE declarations; legacy media and push-notification integrations.

**Not yet established:** whether the original app launches on the user's Android 16 device, whether any official compatible AIR SDK can build the app, and whether proprietary ANE sources/ARM64 builds are obtainable.

**No ARM64 APK has been built or tested.** Next practical gate is an actual install/launch log from the target device plus provenance/source availability for the three ANEs.
