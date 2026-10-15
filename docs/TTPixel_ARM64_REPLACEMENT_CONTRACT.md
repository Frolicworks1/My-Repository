# TTPixel ARM64 replacement contract

## Purpose and truthfulness rule

This document defines a testable boundary for a clean-room replacement of the legacy `com.adobe.ttpixel.extension` ANE. It is a contract for future implementation, **not evidence that a replacement exists**. The uploaded APK contains only ARM32 native libraries, and the SWF string inventory is not recovered source code. No method below may be marked implemented until an implementation and its behavioral tests are present.

## Compatibility rules

1. Preserve the extension ID and expected ActionScript-facing names only where legally and technically appropriate for a clean-room implementation.
2. Capture the actual call sequence, argument types, return values, error codes, and thread expectations from a licensed runtime before asserting signature compatibility. Names alone are insufficient.
3. Never return success for an operation that silently drops or corrupts image data.
4. Unsupported optional hardware/services must return a documented unavailable result or safe fallback, not crash the app.
5. Keep the original APK, proprietary libraries, private user assets, and runtime traces containing personal data out of Git.
6. Every implemented capability needs deterministic tests and, for pixel-changing operations, golden-image tests with documented tolerances.

## Capability groups and acceptance gates

The machine-readable inventory is `rebuild/ane/ttpixel_capabilities.json`. Status values are deliberately conservative:

- `blocked_by_runtime_trace`: exact call ABI, types, or semantics still need runtime evidence.
- `unimplemented`: implementation and acceptance tests do not yet exist.
- `deferred_optional`: secondary integration can be deferred while local editing is established.

### Phase 0 — lifecycle and error reporting

Acceptance: extension creation/preflight can run repeatedly; missing capability reports are deterministic; failures are visible in logs; no fake “ready” state when required methods are absent.

### Phase 1 — image and file primitives

Acceptance: test fixtures cover empty images, 1x1 images, large images, alpha, color profiles where supported, malformed files, bounds, and round-trip persistence. Pixel hashes must match where the legacy format is lossless; lossy formats need explicit numeric tolerances.

### Phase 2 — filters

Acceptance: each supported filter has fixtures for normal, edge, transparent and invalid inputs. Parameter ranges and output dimensions are verified. Unknown filter IDs fail clearly.

### Phase 3 — rendering and asynchronous work

Acceptance: texture/render-target lifecycle is balanced; readback completes or fails deterministically; no use-after-free during async completion; orientation, alpha and color space are verified on ARM64 devices.

### Phase 4 — selection, camera and stylus

Acceptance: selection masks are compared against fixtures; camera denial/no-camera cases do not crash; stylus pressure returns a documented neutral fallback when unavailable and respects supported pressure range.

### Phase 5 — secondary integrations

Sync and legacy C2DM push are not blockers for offline editing unless runtime traces prove core startup depends on them. They must remain explicitly unsupported until replaced and tested.

## Required evidence before claiming a real port

- ARM64 package inspection shows any native libraries as ELF64/AArch64; a Java-only APK must not be described as native AArch64.
- Installation and cold launch succeed on the target Android 16 device.
- Original SWF startup reaches document creation without unresolved required ANE calls.
- Import, edit, undo/redo, save/reopen and export pass on known fixtures.
- Each implemented feature has a test and its capability status is updated in the same change.
- Publish an honest unsupported-feature list and keep the native drawing prototype clearly separate from the original app.

## Current state

All TTPixel capabilities in the JSON inventory remain unimplemented or blocked pending runtime traces. This contract does not claim a completed replacement, original-app APK, or successful original-app runtime test.
