# Native Android editor prototype (not full PS Touch)

This is a clean-room proof-of-life module, deliberately separate from the original proprietary APK. It is not a conversion of the original SWF and does not yet load legacy PS Touch projects.

## Implemented in this first native milestone

- Android framework-native drawing canvas (no bundled 32-bit native libraries)
- Finger drawing with round strokes
- Five-color cycling brush palette
- Import an image as a background/reference layer
- Brush and white eraser
- Undo last stroke and clear canvas
- Export artwork to PNG using Android MediaStore
- API 36 compile/target settings, Java 17, minSdk 23
- Debug APK signed with the standard Android debug key by the Gradle build
- Automated Android 16 emulator smoke test checks that the activity launches and the import, eraser and PNG export controls appear

The app is architecture-neutral Java/Dex, so Android's runtime executes it on ARM64 devices; it is not an ARM64-only native binary. The CI gate rejects unexpected bundled `.so` libraries in this prototype.

## Build

From this directory, using JDK 17, Android SDK platform 36, build-tools 35.0.0 and Gradle 8.11.1:

```bash
gradle --no-daemon clean assembleDebug
```

APK output:

```
app/build/outputs/apk/debug/app-debug.apk
```

Or run the GitHub Actions workflow manually from the repository's Actions tab:
[Build native ARM64 editor prototype](../../.github/workflows/build-arm64-prototype.yml)

Successful workflow runs upload the APK as the artifact `PS-Touch-ARM64-Prototype-debug` for 14 days.

## Not implemented yet

- Importing or editing original PS Touch project files
- Layers, selections, transforms, masks, filters, text, blending modes or PSD compatibility
- Image import, multi-touch zoom/pan, pressure sensitivity, stylus support
- Original TTPixel/SWF runtime or feature parity

Do not label this prototype a complete port. It is the first independent native foundation, and must be built, installed and tested on the target Android 16 device before its runtime status is confirmed.
