# Original APK inventory — local analysis

This note records the structural facts measured from the user-provided PS Touch Plus.zip on 2026-10-14. The original APK and extracted app resources remain local and are not committed to Git.

## Original package facts

- Package: air.com.adobe.pstouch
- App version: 1.7.7 (versionCode 1007007)
- Main entry point: assets/TTPixel.swf
- Main SWF: uncompressed FWS, SWF version 19, 7,702,448 bytes, 30 fps, one frame, one DoABC block containing 2,074,958 bytes of ABC payload.
- Native libraries: nine .so files, all under lib/armeabi-v7a/. The main native extension library is libTTPixelExtensionAndroid.so (about 2.3 MB); libCore.so is about 24.9 MB.
- Three ANEs are embedded: com.adobe.ttpixel.extension, air.com.adobe.cc.sync.SyncEngine, and air.com.adobe.cc.PushNotification.
- The TTPixel ANE descriptor declares Android-ARM and iPhone-ARM, and its Android deployment names library.jar; the original app's ARM32 libTTPixelExtensionAndroid.so is packaged separately in the APK's root lib/armeabi-v7a/.
- SyncEngine and push notification descriptors also declare only Android-ARM and iPhone-ARM.

The APK includes ANE ActionScript library SWFs both at the ANE root and beneath META-INF/ANE/Android-ARM/. These are duplicate library-stub placements, not six distinct ANEs. The three distinct extension libraries contain 37 ABC blocks (TTPixel), four (SyncEngine), and 20 (push notifications).

## Porting implications

1. The original compiled UI/application logic is present. We can attempt to package the original SWF in a current AIR runtime without rebuilding the app UI from source.
2. The original native implementation is not ARM64. No manifest change or copy into arm64-v8a can transform the nine ARM32 libraries.
3. TTPixel is the main feature-parity blocker. Its library SWF exposes API names related to bitmap/file operations, filters, texture/render-target commands, quick selection, camera and stylus pressure. Its original native algorithms are not recovered by a string inventory.
4. Sync and C2DM push are separable secondary features. They should not be treated as prerequisites for the first local-editor startup test, but must be replaced if their user-facing functionality is required.
5. A no-ANE package is only a runtime diagnostic. It may fail at startup or in editor workflows because the SWF expects extension classes. A valid ARM64 AIR package is not proof of Photoshop Touch feature compatibility.

## Local detailed report

A local Markdown/JSON report was generated from the supplied APK, including SWF headers, ABC string-pool matches, hashes and the ELF class/machine of every bundled native library. It is intentionally kept outside the repository to avoid committing proprietary app-derived material.

## Next engineering gates

- Build the original-SWF diagnostic with a current, licensed AIR SDK and inspect its actual APK contents.
- Install and launch it on Android 16; collect logcat output and note the first missing ANE API or runtime incompatibility.
- If the editor cannot initialize, implement a compatible ARM64 TTPixel ANE. Prioritize bitmap/file primitives and filters, then GPU rendering, quick selection, camera and pressure. Validate pixel outputs against test fixtures rather than returning fake success.
- Keep the working Java/Dex prototype separate; it is a fallback, not a replacement for the original application.
