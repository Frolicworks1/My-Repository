# Native-extension API surface from the packaged SWF stubs

The APK includes ActionScript library SWFs for its embedded ANEs. Their ABC constant pools expose names and call labels. This is a static API-surface inventory, not recovered source code and not proof that each operation is called in every workflow.

## TTPixel extension — highest priority

The SWF library contains 37 ABC blocks and names associated with these groups:

| Group | Observed API-like names | Porting implication |
|---|---|---|
| Image/file operations | bitmapDataCopy, bitmapDataFromFile, bitmapDataFromFileEx, bitmapDataResample, bitmapDataToFile, bitmapDataToFileEx, bitmapFileCreateEmpty, bitmapFileCreateFromBitmapData, bitmapFileRead, bitmapFileResample, bitmapFileWrite, getPixelsBitmapEx, compressBitmapRLE, uncompressBitmapData, uncompressBitmapDataEx | Needed to preserve image IO, resizing, pixel access and the app's internal image representation. Test format compatibility before replacing. |
| Filters and processing | createFilter, createFilterEx, applyFilter, destroyFilter | The SWF expects a native filter lifecycle; Java-side stubs alone would not preserve actual filter results. |
| GPU / rendering | TTGL, TTGLCommandSequence, prepareTextureFromBitmapData, updateTextureFromBitmapData, setRenderTarget, renderPreviewFrame, asyncReadPixels, asyncExecuteSequence | A replacement needs compatible texture/render-target semantics and synchronization, not merely an Android drawing canvas. |
| Selection | TTQuickSelection, quickselection | The quick-selection feature needs its own implementation or a deliberate feature limitation. |
| Camera | TTCamera, TTCameraCapabilities, TTCameraParameters, TTCameraRoll, TTCameraUI, enumerateCameras | Replace using modern Android camera/media APIs behind a compatible extension interface. |
| Stylus pressure | TTPressureProvider, TTPressureSource, createPressureSource, getPressure, getUnbiasedPressure, updatePressureSource | Preserve a safe fallback for devices without supported styluses; old vendor-specific pressure adapters are not portable. |
| Extension lifecycle | createExtensionContext, getExtensionContext, preflight, TTPreflightResult | A replacement must match expected startup/status behavior and error handling. |

### Recommended implementation order

1. **Prove startup and document creation** with a current AIR runtime, then capture missing-class / missing-function errors from the original SWF.
2. **Build a compatibility shim** for the simplest non-native methods and the extension lifecycle; don't return fake success for operations that change image pixels.
3. **Prioritize image/file primitives and basic filters**, with golden-image tests against known inputs and expected outputs.
4. **Implement GL, quick-selection, camera and pressure separately**, each behind a documented capability gate.
5. Keep unsupported cloud features disabled only after the app is confirmed to work locally without them.

The actual native TTPixel shared object is proprietary ARM32 code. The string inventory does not supply its algorithms or an ARM64 implementation; this remains the main feature-parity blocker.

## SyncEngine

The SyncEngine library stub exposes operations such as initialize, isAvailable, start, stop, terminate, setBandwidthLimit, getDeviceManufacturer, getDeviceModel, and getReturnCodeText, plus a root sync directory. The first diagnostic build omits it; cloud sync is not expected to work until a compatible replacement and service endpoint behavior are verified.

## PushNotification

The PushNotification stub exposes C2DM registration, availability, register/unregister and long-polling classes. C2DM is a legacy integration. The first diagnostic build omits it, and no ARM64 push feature is claimed.

## Reproduce the inventory

Extract the user-owned APK locally, then run the SWF audit against each extracted library.swf (the migration extractor preserves these paths):

    python3 tools/prepare_air_migration.py "/path/to/PS Touch Plus.apk" --out build/private-air-input
    python3 tools/audit_swf.py build/private-air-input/assets/META-INF/AIR/extensions/com.adobe.ttpixel.extension/library.swf --out build/ttpixel-ane-audit

Keep the original APK, extracted assets and generated reports local; do not commit them to the repository.
