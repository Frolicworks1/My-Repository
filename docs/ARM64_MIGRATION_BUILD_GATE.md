# ARM64 migration gate — next build stage

## Confirmed target
Create a separately signed PS Touch Plus APK that can be installed and tested on Android 16, with genuine ARM64 native code. Preserve the uploaded original APK unchanged and do not commit proprietary APK contents to Git.

## Evidence from current static audit
- Original APK packages nine native shared objects under `lib/armeabi-v7a/`; no `lib/arm64-v8a/` directory exists.
- The TTPixel, SyncEngine and PushNotification ANE descriptors declare Android-ARM but not Android-ARM64.
- Legacy Stagefright dependencies are present.
- The APK contains compiled SWF/DEX, not the original ActionScript and native extension source project.

## Build gates
1. Select a maintained AIR SDK/runtime with Android ARM64 packaging support and configure Android SDK/JDK dependencies.
2. Obtain or rebuild the TTPixel ANE for ARM64. Do not assume it is optional: its exported classes suggest graphics, camera, selection and image-operation integration.
3. Obtain/rebuild SyncEngine for ARM64 or prove a local-only build works after a controlled removal.
4. Remove or replace the legacy C2DM extension only after confirming application startup does not require it.
5. Replace or isolate old Stagefright paths and test the media workflows that use them.
6. Package a separate test APK, inspect its ELF machine types and APK signature, then install and exercise it on Android 16.

## Why a manifest-only patch is not the port
Changing target SDK, renaming ELF32 libraries, or copying ARM32 binaries into an arm64 directory cannot translate machine code. Modern AIR packaging tools can package compatible ANEs, but the ANE must actually support the target architecture. The closed-source native implementations cannot be regenerated from the APK alone.

## Current status
Reverse-engineering and static tests exist; no rebuilt/installable APK has been produced yet. Do not report the app as fixed until a real package has been created, architecture-inspected, installed and tested.
