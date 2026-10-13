# PS Touch Plus — ARM64 / Android 16 investigation

This branch contains a reproducible, non-destructive audit toolkit for the user-provided PS Touch Plus APK. It does not contain the proprietary APK or a falsely patched build.

## Current evidence

- Adobe AIR namespace 16.0; app ID com.adobe.pstouch, PS Touch 1.7.7.
- Main payload: assets/TTPixel.swf.
- Nine native shared objects are present under lib/armeabi-v7a/; no lib/arm64-v8a/ entries were found.
- Declared ANEs: com.adobe.ttpixel.extension, air.com.adobe.cc.sync.SyncEngine, air.com.adobe.cc.PushNotification.

A manifest/target-SDK edit cannot convert 32-bit ELF binaries to ARM64. A real port needs a compatible AIR runtime, ARM64 versions of required native libraries/ANEs, and Android 16 device testing.

## Run in GitHub Codespaces

Upload the APK privately into the workspace (for example input/PS Touch Plus.apk) without committing it, then run:

    python3 tools/audit_apk.py "input/PS Touch Plus.apk" --out build/audit

The script writes Markdown and JSON inventories. Android Build Tools are optional for extra decoded-manifest output. See docs/REVERSE_ENGINEERING_NOTES.md for the migration plan and blockers.
