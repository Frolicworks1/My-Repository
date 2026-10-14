# Capturing real AIR / ANE runtime evidence

The TTPixel string inventory is not enough to infer ActionScript argument types, return types, callback order, or error semantics. These must be captured from an authorized runtime. This helper collects evidence from a connected Android device; it does not create traces by itself and does not inject code into the app.

## Capture on a connected Android device

1. Enable Developer options and USB debugging; connect the device and authorize the host.
2. Ensure `adb devices` shows the device as `device`, not `unauthorized`.
3. Run from the repository root:

   ```bash
   bash scripts/capture_air_runtime_trace.sh air.com.adobe.pstouch 120
   ```

4. During the two-minute capture, manually attempt a cold launch and reproduce one operation at a time. Start with launch/document creation, then image open/save, then a basic filter.
5. Review the private output in `build/private-runtime-traces/`. The script records Android version, SDK, supported ABIs, whether the package is installed, raw logcat, and a best-effort filtered summary.

Use `bash scripts/capture_air_runtime_trace.sh PACKAGE SECONDS OUTPUT_DIR` to change the package, duration (10–1800 seconds), or output directory.

## Privacy and evidence quality

- Logs can contain device identifiers, file paths, account details or other personal information. The output directory is private and must not be committed. Redact before sharing.
- A log showing `dlopen failed` or `UnsatisfiedLinkError` can establish a loading failure, but usually does not reveal the complete method ABI.
- For actual argument and return types, correlate logs with a debugger/instrumented test harness or a known-good licensed AIR/ANE runtime. Record method name, call order, input types/ranges, output type, error behavior, and whether callbacks are synchronous.
- Do not claim a method contract is known until supported by repeatable evidence. Never guess a signature and then report it as recovered.

## Current limitation

No target Android device is attached to this GitHub workflow, and this script has not captured a trace from the user's device. CI can validate the script, not simulate the proprietary extension. An original-app trace and an authorized AIR SDK/runtime are still required before the replacement can be integrated with confidence.
