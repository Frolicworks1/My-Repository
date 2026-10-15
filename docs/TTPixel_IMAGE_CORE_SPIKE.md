# TTPixel image core spike

This module is a clean-room, Android-side experiment for basic image primitives. It is intentionally not described as a complete ANE or a replacement for the original TTPixel implementation.

## Implemented in this spike

- Bitmap copy
- ARGB pixel read/write
- PNG encode/decode round-trip
- Resampling with explicit target dimensions
- Rejection of empty/malformed input and unreasonable output sizes
- Android instrumentation tests for exact ARGB and PNG round trips

## Not implemented / not yet proven

- AIR `FREExtension`, `FREContext`, or `FREFunction` glue
- The original SWF's actual argument types, return values, callback ordering, or error semantics
- Proprietary TTPixel compression, file formats, filters, TTGL, selection, or pressure APIs
- Compatibility with original Photoshop Touch documents

The real SWF call contract must be captured from an authorized runtime with logs or instrumentation. This core must not be wired to guessed signatures. The emulator instrumentation test is only a deterministic core test, not proof that the original app launches or works.
