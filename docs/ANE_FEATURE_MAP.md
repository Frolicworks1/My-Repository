# AIR Native Extension feature map

This map is derived from the bundled ANE XML descriptors, SWC catalogs and DEX printable strings in the supplied APK. It is static evidence, not a guarantee that each symbol is invoked at runtime.

## 1. TTPixel extension — high priority / likely core

ID: `com.adobe.ttpixel.extension`

Declared platforms:
- `Android-ARM` using `library.jar`
- `iPhone-ARM` using `libTTPixelExtensionCocoaTouch.a`
- No Android ARM64 platform declaration is present.

The packaged Android library is `libTTPixelExtensionAndroid.so` (ELF32 ARM, approximately 2.3 MB). DEX strings and the SWC catalog expose classes including:
- `TTGL`, `TTGLCommandSequence`, `ECGLContext` — graphics/OpenGL bridge.
- `TTQuickSelection` — quick-selection feature bridge.
- `TTCamera`, `TTCameraParameters`, `TTCameraCapabilities` — camera access.
- `TTAM`, `TTSS`, `TTCAF`, `TTNEUtils` — additional native-extension operations/utilities; exact semantics need source or controlled runtime tracing.
- `TTPressureProvider*`, `TTPressureSource*` — stylus/pressure integrations (provider names include Pogo, JotTouch, Jaja).
- `TTActivityUI`, `TTMail` — activity UI and mail-related integration.

**Assessment:** do not assume this ANE can simply be omitted. Its GL, quick-selection, camera and image-data bridges may be used by major editing flows. ARM64 source or a vendor-provided ARM64 ANE is the preferred path. Reimplementation is a substantial reverse-engineering project.

## 2. SyncEngine — high priority if cloud sync is required

ID: `air.com.adobe.cc.sync.SyncEngine`

Declared platforms:
- `Android-ARM` using `libAdobeSyncEngineBridge.so`
- `iPhone-ARM` using `libAdobeSyncEngineBridge.a`
- No Android ARM64 platform declaration is present.

The APK packages `libair.com.adobe.cc.sync.SyncEngine.so` with SONAME `libAdobeSyncEngineBridge.so`; it depends on `libCore.so`. The bridge is ELF32 ARM.

**Assessment:** likely tied to Adobe cloud/sync features. Test whether the application can start and edit local projects without it before considering a feature-reduced build. Do not remove it blindly: AIR may fail to resolve a declared extension during startup or the app may reference its classes at initialization.

## 3. PushNotification — possibly optional, but needs a controlled removal test

ID: `air.com.adobe.cc.PushNotification`

Declared platforms:
- `Android-ARM` using `AdobeC2DMLibrary.jar`
- `iPhone-ARM` using `libAdobeAPNAirExtension.a`
- No Android ARM64 platform declaration is present.

The bundled classes refer to C2DM registration/receivers and old notification APIs. C2DM is a legacy integration and is not a safe assumption for current Android push services.

**Assessment:** this is the first extension to investigate for an optional feature-reduced build, but only after checking application startup references and testing a controlled variant. A modern push implementation would require a supported replacement and corresponding app-side changes.

## ARM64 feasibility gate

For a true native ARM64 build, the following are required:
1. An AIR runtime/toolchain that supports current Android deployment and ARM64.
2. An ARM64 build of each required native extension, or a deliberate code-level replacement/removal proven safe.
3. Modernized/replaced legacy Stagefright paths.
4. App-side updates for modern Android storage, lifecycle, permissions and target SDK.
5. Device testing of both launch and real editing/export workflows.

Renaming ELF32 files, editing only the manifest target, or repackaging the APK does not meet this gate.
