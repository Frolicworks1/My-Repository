#!/bin/sh
set -eu

ROOT_DIR="$(pwd)"
DIAG_DIR="$ROOT_DIR/build/ci-emulator-diagnostics"
mkdir -p "$DIAG_DIR"

echo "Waiting for Android emulator boot completion..."
adb wait-for-device

attempt=1
while [ "$attempt" -le 60 ]; do
  booted="$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
  if [ "$booted" = "1" ]; then
    break
  fi
  echo "Emulator boot not complete (attempt $attempt/60)"
  sleep 5
  attempt=$((attempt + 1))
done

booted="$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
if [ "$booted" != "1" ]; then
  echo "Emulator failed to report boot completion."
  adb devices -l > "$DIAG_DIR/adb-devices.txt" 2>&1 || true
  adb shell getprop > "$DIAG_DIR/getprop.txt" 2>&1 || true
  exit 1
fi

adb shell settings put global window_animation_scale 0 || true
adb shell settings put global transition_animation_scale 0 || true
adb shell settings put global animator_duration_scale 0 || true
adb shell getprop > "$DIAG_DIR/getprop.txt" 2>&1 || true
adb shell df -h > "$DIAG_DIR/disk-space.txt" 2>&1 || true

cd rebuild/android
if gradle --no-daemon connectedDebugAndroidTest; then
  echo "Instrumentation tests completed successfully."
else
  result=$?
  echo "Instrumentation failed; collecting full device diagnostics before failing."
  adb devices -l > "$DIAG_DIR/adb-devices.txt" 2>&1 || true
  adb shell getprop ro.build.version.sdk > "$DIAG_DIR/android-sdk.txt" 2>&1 || true
  adb shell dumpsys activity > "$DIAG_DIR/activity.txt" 2>&1 || true
  adb shell dumpsys meminfo > "$DIAG_DIR/meminfo.txt" 2>&1 || true
  adb logcat -d -t 12000 > "$DIAG_DIR/logcat-full.txt" 2>&1 || true
  grep -E -i 'FATAL EXCEPTION|AndroidRuntime|INSTRUMENTATION|InstrumentationResultPrinter|AndroidJUnitRunner|Process .*crashed|am_crash|Fatal signal|crash_dump|lowmemorykiller|TestRunner|testInstrumentationRunner' "$DIAG_DIR/logcat-full.txt" > "$DIAG_DIR/logcat-filtered.txt" || true
  tail -n 250 "$DIAG_DIR/logcat-filtered.txt" || true
  exit "$result"
fi
