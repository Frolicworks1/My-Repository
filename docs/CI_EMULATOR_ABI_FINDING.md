# CI emulator ABI finding — PS Touch Plus

## Evidence source

Reviewed the retained CI artifact `android-emulator-diagnostics.zip` from the Android 15 emulator run on 2026-10-15. This is the build emulator, not the user's physical Android 16 device.

Observed properties:

- `ro.build.version.release=15`
- `ro.build.version.sdk=35`
- `ro.product.cpu.abi=x86_64`
- `ro.product.cpu.abilist=x86_64`
- `ro.product.cpu.abilist32=` (empty)
- `ro.product.cpu.abilist64=x86_64`
- ADB identifies it as `Android_SDK_built_for_x86_64`.

## What this establishes

1. The saved CI emulator is **x86_64-only** and does not advertise ARM32 (`armeabi-v7a`) or ARM64 (`arm64-v8a`) ABIs.
2. It cannot answer whether the user's phone supports 32-bit ARM applications.
3. It is not a valid runtime target for validating this original APK's ARMv7 native libraries. A successful managed-code prototype test on it would not establish that the original AIR/ANE stack works on ARM hardware.
4. The retained test report says instrumentation failed to complete because the test process crashed; it reports zero completed tests. Therefore this run must not be presented as a successful runtime validation.

## Correct next validation gate

- Keep static APK checks and managed prototype CI separate from original-app runtime compatibility claims.
- For CI, use a compatible ARM64 Android emulator/device configuration where available; record `ro.product.cpu.abilist` and `ro.build.version.sdk` in every run.
- For the real target, collect the same properties and an install/launch log from an authorized device. This repo workflow has no access to the user's phone, so it cannot infer that phone's ABI from the CI emulator.
- Even if a device advertises `armeabi-v7a`, that only establishes OS ABI support, not that the legacy target-SDK, AIR runtime, native libraries, or ANEs will install and run successfully.
- Do not modify or claim success for the original APK until a real original-APK test is available. The existing prototype is not a substitute for the original application.

## Status

This is a corrected interpretation of existing diagnostics, not a new device test and not an APK build.
