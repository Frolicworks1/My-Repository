# Reverse-engineering notes — PS Touch Plus

## Static evidence from the supplied APK

- SHA-256: ce61c9a0235731e048f6be4ae556d70760cdaee48357f614e6ea620a7deac091
- ZIP contains 404 entries.
- AIR descriptor: assets/META-INF/AIR/application.xml; namespace http://ns.adobe.com/air/application/16.0.
- Application ID: com.adobe.pstouch; name/version: PS Touch 1.7.7.
- Main SWF: assets/TTPixel.swf (7,702,448 bytes).
- Nine native shared libraries are all under lib/armeabi-v7a/; no lib/arm64-v8a/ entries were found. All nine inspected objects are ELF32 ARM.
- Libraries: libCore.so, libTTPixelExtensionAndroid.so, libair.com.adobe.cc.sync.SyncEngine.so, libgdx-audio.so, libsibsynclib.so, libstagefright_froyo.so, libstagefright_honeycomb.so, libstlport_shared.so, libysshared.so.
- Declared ANEs: com.adobe.ttpixel.extension, air.com.adobe.cc.sync.SyncEngine, air.com.adobe.cc.PushNotification.

## Why a manifest-only patch is insufficient

A 64-bit process cannot load an ARM32 shared object. A genuine ARM64 build needs a compatible AIR runtime and ARM64 versions of every required native library/ANE. Do not create empty or renamed .so files as substitutes.

## Work plan

1. Decode AndroidManifest.xml with Android Build Tools (aapt dump badging, apkanalyzer manifest print) or Apktool; record package, min/target SDK, activities, permissions, exported components and native extraction flags.
2. Inspect DEX/bootstrap code with JADX; identify AIR runtime and ANE loading paths.
3. Inspect SWF/ABC metadata with a compatible SWF tool. A compiled SWF is not original editable ActionScript source.
4. Inspect each ELF with readelf -h -d, nm -D and strings; record architecture, NEEDED libraries, SONAMEs, exports and legacy Android API references.
5. Locate original ANE packages or source for all three extension IDs. Installed .so files alone do not contain complete ANE package/configuration.
6. Check current Harman AIR SDK documentation for Android ABI, target-SDK and Android 16 support before choosing a toolchain.
7. Rebuild with compatible ARM64 ANEs; optionally retain ARMv7 if supported.
8. Test on a real 64-bit Android 16 device: clean install, lifecycle, image import/export, camera, storage, sync/push, filters, large documents, crashes and ANRs.

## Stop conditions

- If a required closed-source ANE has no ARM64 build, do not claim full ARM64 support until its vendor supplies one or a permitted replacement is implemented.
- If runtime APIs/ANE ABI are unsupported, runtime migration or reimplementation is required.
- An APK that installs but crashes is not a successful port; capture adb logcat.

Run: python3 tools/audit_apk.py /path/to/PS-Touch-Plus.apk --out build/audit
Keep the proprietary APK local and out of Git history.
