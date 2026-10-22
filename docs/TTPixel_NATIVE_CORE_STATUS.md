# TTPixel native core status

## Implemented and CI-verified

- Checked pixel-buffer allocation with dimension and pixel-count caps.
- ARGB pixel read/write with bounds checks.
- Deep copy and nearest-neighbor resize.
- Host CMake build and contract test.
- Android NDK arm64-v8a cross-compile.
- JNI adapter exposing these primitives to Android Java callers.

## Explicitly not implemented

This is not a replacement for the original com.adobe.ttpixel.extension AIR Native Extension. It does not implement Adobe FRE registration/lifecycle, ActionScript-facing signatures, original proprietary image formats, filters, GL command queues, selection, or the SWF's full call contract. The JNI wrapper is a development bridge for exercising the clean-room core only.

## Next integration gates

1. Establish exact AIR ANE method signatures and lifecycle behavior from the licensed AIR runtime and extension descriptor.
2. Implement a separate FRE/ANE adapter; do not assume JNI names satisfy ActionScript.
3. Connect the SWF extension bootstrap and capture runtime traces.
4. Implement image import/export and filters with fixture-based compatibility tests.
5. Package with the licensed AIR SDK and verify cold launch, document creation, edit/save/reopen/export on Android 16.
