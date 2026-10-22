# PS Touch++ Native Rebuild Roadmap

## Decision

Build a clean-room, native Android photo editor as a separate track from the legacy AIR compatibility investigation. A native ARM64 app avoids depending on the original 32-bit AIR runtime, but it does **not** automatically reproduce the original app's features. Feature parity is an incremental engineering project.

The current app under `rebuild/android` is an early proof of concept (image import, finger drawing, brush colours, eraser, undo-last-stroke, clear, PNG export). It is not feature-complete and must not be presented as the original PS Touch.

## Product target

Working name: **PS Touch++**. Use original, independently created branding and UI assets. Treat the original app as a behavioural reference only; do not copy proprietary code, artwork, or assets without permission.

## Feature parity backlog

### Phase 0 — reliable foundation
- [x] ARM64-native Android application shell and image-core prototype
- [x] Import image through Android document picker
- [x] Finger drawing, simple colour palette, eraser, undo-last-stroke, clear
- [x] PNG export to MediaStore
- [x] Basic image decode limits and instrumentation tests for image primitives
- [ ] Verify current CI emulator test and produce a clearly labelled prototype APK
- [ ] Add document/project state, lifecycle-safe save/reopen, and robust error handling
- [ ] Add zoom/pan canvas with correct coordinate mapping and pressure-aware stylus input

### Phase 1 — core editing
- [ ] Non-destructive layer stack: add, duplicate, reorder, hide, opacity, rename, delete
- [ ] Blend modes and layer masks
- [ ] Brush controls: size, hardness, opacity, flow, colour picker, pressure support
- [ ] Selection tools: rectangle, ellipse, freehand/lasso, invert, feather, clear/copy/paste
- [ ] Transform: move, scale, rotate, flip, crop, straighten
- [ ] Undo/redo history with memory limits
- [ ] Text layers with font, size, colour, alignment, and transform
- [ ] JPEG/PNG import and export with quality options

### Phase 2 — image adjustments and effects
- [ ] Brightness/contrast, levels, curves, hue/saturation, temperature/tint
- [ ] Exposure, black-and-white, colour balance and other adjustment layers
- [ ] Blur, sharpen, noise and basic filters
- [ ] Clone/heal tools and gradients
- [ ] Cutout/refine-edge workflow
- [ ] Selection-aware edits and previews that can be cancelled safely

### Phase 3 — advanced workflows
- [ ] Project file format that preserves layers, masks, text and edit history
- [ ] Large-canvas tiling and background processing to avoid out-of-memory crashes
- [ ] GPU-accelerated previews where correctness can be tested
- [ ] Share/export sizes, metadata handling, accessibility, tablet and stylus UI
- [ ] Automated visual regression tests and real-device testing on Android 16 / ARM64

## Architecture

- **UI:** native Android views first; avoid a web wrapper for the editing canvas.
- **Document model:** explicit document, layer, mask, selection and history types.
- **Raster engine:** isolated image operations with dimension/pixel-count guards and unit tests.
- **Rendering:** tiled or bounded bitmap rendering; keep UI responsive with background workers.
- **Persistence:** versioned project format; atomic writes; never silently discard unsaved edits.
- **Compatibility:** API 23 minimum currently configured; target current Android SDK; test on API 36 and physical Android 16 devices.
- **Validation:** unit tests for each operation, instrumentation tests for Android bitmap behaviour, golden-image tests for deterministic filters, and memory/stress tests.

## Definition of done

Do not claim “all original features copied” until every feature in an agreed checklist has an implemented behaviour and a test. Each release should list what works, what is partial, and what is not implemented. The first useful milestone is a stable layered editor with import/export, brush/eraser, selection, transform, text, undo/redo, and a native ARM64 APK—not a promise of immediate full parity.

## Legacy AIR track

Keep the existing AIR/ANE investigation separate. The original TTPixel native extension is a substantial compatibility blocker. A clean-room native editor may eventually be the more maintainable route, but the two tracks must not be conflated: native image primitives and a prototype APK do not mean the original SWF or its proprietary features are running.
