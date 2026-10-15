#!/usr/bin/env bash
set -Eeuo pipefail

PACKAGE="${1:-air.com.adobe.pstouch}"
SECONDS_TO_CAPTURE="${2:-120}"
OUT_DIR="${3:-build/private-runtime-traces}"

if ! command -v adb >/dev/null 2>&1; then
  echo "ERROR: adb is not installed or not on PATH." >&2
  exit 2
fi
if ! [[ "$SECONDS_TO_CAPTURE" =~ ^[0-9]+$ ]] || (( SECONDS_TO_CAPTURE < 10 || SECONDS_TO_CAPTURE > 1800 )); then
  echo "ERROR: capture duration must be between 10 and 1800 seconds." >&2
  exit 2
fi
adb get-state >/dev/null 2>&1 || {
  echo "ERROR: no authorized Android device/emulator. Connect it and accept the USB debugging prompt." >&2
  exit 3
}

mkdir -p "$OUT_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$OUT_DIR/air-runtime-$STAMP.log"
SUMMARY="$OUT_DIR/air-runtime-$STAMP-summary.txt"

{
  echo "UTC timestamp: $STAMP"
  echo "Requested package: $PACKAGE"
  echo "Capture duration seconds: $SECONDS_TO_CAPTURE"
  echo "Device model:"
  adb shell getprop ro.product.model 2>/dev/null || true
  echo "Android release:"
  adb shell getprop ro.build.version.release 2>/dev/null || true
  echo "Android SDK:"
  adb shell getprop ro.build.version.sdk 2>/dev/null || true
  echo "Supported ABIs:"
  adb shell getprop ro.product.cpu.abilist 2>/dev/null || true
  echo "Package installed:"
  if adb shell pm path "$PACKAGE" 2>/dev/null | grep -q '^package:'; then echo yes; else echo no; fi
} | tee "$SUMMARY"

echo
echo "Capturing device logcat for $SECONDS_TO_CAPTURE seconds."
echo "During capture, attempt one cold launch of the app and reproduce the failure."
echo "Raw logs may contain private information; keep these files local and review before sharing."
set +e
timeout "${SECONDS_TO_CAPTURE}s" adb logcat -v threadtime > "$LOG" 2>&1
RC=$?
set -e
if (( RC != 0 && RC != 124 )); then
  echo "WARNING: adb logcat exited with status $RC; see $LOG" >&2
fi

{
  echo
  echo "Relevant lines (best-effort keyword filter; full raw log is above):"
  grep -Ein 'air.com.adobe.pstouch|Adobe AIR|AppEntry|FREExtension|FREContext|FREFunction|ANE|TTPixel|SyncEngine|PushNotification|UnsatisfiedLinkError|dlopen failed|ClassNotFoundException|NoClassDefFoundError|VerifyError|SecurityException|FATAL EXCEPTION|AndroidRuntime|SIGABRT|SIGSEGV|linker' "$LOG" || true
} >> "$SUMMARY"

echo "Raw trace: $LOG"
echo "Filtered summary: $SUMMARY"
echo "Do not commit either file. Share only reviewed, redacted excerpts."
