#!/bin/sh
set -eu

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
  adb devices -l || true
  adb shell getprop || true
  exit 1
fi

adb shell settings put global window_animation_scale 0 || true
adb shell settings put global transition_animation_scale 0 || true
adb shell settings put global animator_duration_scale 0 || true

cd rebuild/android
if gradle --no-daemon connectedDebugAndroidTest; then
  echo "Instrumentation tests completed successfully."
else
  result=$?
  echo "Instrumentation failed; collecting device diagnostics before failing."
  adb devices -l || true
  adb shell getprop ro.build.version.sdk || true
  adb logcat -d -t 4000 2>/dev/null | grep -E 'FATAL EXCEPTION|AndroidRuntime|INSTRUMENTATION|Process .*crashed|TTPixelImageCoreTest|TestRunner|am_crash' | tail -n 250 || true
  exit "$result"
fi
