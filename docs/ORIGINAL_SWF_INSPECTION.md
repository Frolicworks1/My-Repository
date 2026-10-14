# Original SWF inspection — next migration gate

The supplied PS Touch Plus APK contains `assets/TTPixel.swf`, a compiled SWF rather than the original ActionScript authoring project. The local copy inspected on 2026-10-14 has SWF signature `FWS` (uncompressed), SWF version 19, and an uncompressed length of 7,702,448 bytes. A structural scan found one `DoABC` block named `frame1` with about 2.07 MB of ABC data, along with hundreds of sprite/shape and other display-list tags. This is evidence that the core application logic is present as compiled bytecode, not that the original source can be recovered perfectly.

## New local inspection tool

Run this against a locally extracted SWF:

```bash
python3 tools/audit_swf.py build/private-air-input/assets/TTPixel.swf --out build/swf-audit
```

It emits `report.md` and `inventory.json`, supports FWS and CWS, and deliberately rejects ZWS until LZMA handling is implemented. It does not modify or decompile the SWF. The proprietary SWF and full APK must remain outside Git.

## What this changes for the original-app plan

A current AIR SDK is a credible packaging experiment because the compiled SWF may be usable without ActionScript source. HARMAN's maintained AIR SDK supports modern Android packaging, but that alone does not fix this app's native extensions. The APK's TTPixel, SyncEngine and push-notification ANEs only declare Android-ARM, so the first experiment must isolate packaging/runtime compatibility from ANE compatibility.

1. Use a licensed current AIR SDK and Android build tools to prepare a private packaging workspace.
2. Keep the original SWF and app descriptor as inputs; do not replace them with the native prototype.
3. First package a diagnostic variant with the minimum extension set only if its descriptors and bytecode references permit it; do not assume TTPixel can be removed.
4. Check the produced APK's manifest, native ABI contents, signature and installability before testing.
5. If the app fails because TTPixel is required, obtain its ARM64 ANE/source or plan a compatible replacement. An APK that merely installs without working edit tools is not success.

Official references:
- HARMAN AIR SDK: https://airsdk.harman.com/
- AIR SDK Manager getting started: https://airsdk.dev/docs/basics/getting-started
- Current release notes: https://airsdk.dev/news/2026/04/17/air-release

**Status:** SWF structure has been inspected locally. This is a new reverse-engineering input, not an ARM64 build. The next decisive milestone is a private AIR packaging experiment with the original SWF and a controlled ANE set.
