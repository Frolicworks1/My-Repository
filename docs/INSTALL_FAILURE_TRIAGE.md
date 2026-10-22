# PS Touch Plus — installation failure triage

## Evidence from the uploaded APK

Inspected file: `PS Touch Plus.apk` extracted from the user-provided ZIP (51,599,899 bytes).

- Package: `air.com.adobe.pstouch`
- Manifest target SDK: 12
- Packaged native ABI: `armeabi-v7a` only
- Signing certificate subject: `EMAILADDRESS=android@android.com, CN=Android, OU=Android, O=Android, L=Mountain View, ST=California, C=US`
- Certificate SHA-256 fingerprint: `A4:0D:A8:0A:59:D1:70:CA:A9:50:CF:15:C1:8C:45:4D:47:A3:9B:26:98:9D:8B:64:0E:CD:74:5B:A7:1B:F5:DC`
- Certificate uses `SHA1withRSA`; this is a legacy signing setup. The ZIP contains JAR-signature entries in `META-INF`. The available local environment did not include Android's `apksigner`, so scheme verification should be repeated with Android Build Tools before making a final signing-scheme claim.

The certificate looks like the generic Android platform test certificate, rather than an identifiable vendor release certificate. That may mean the supplied APK was test-signed or repackaged. It does **not**, on its own, prove the cause of installation failure.

## Candidate causes (not yet distinguished)

1. **Obsolete target SDK:** recent Android releases can block installation of apps targeting very old SDK levels. The manifest's target SDK 12 is a strong candidate.
2. **Device ABI / 32-bit support:** the APK contains only 32-bit ARM native libraries. A device/OS build that does not support 32-bit apps may reject it or fail when loading native code.
3. **Signature / package conflict:** if another app with the same package name is installed and signed with a different key, Android may reject an update. A test/repacked signature also means it may not update an official installation.
4. **APK integrity or packaging:** the supplied APK could have been modified or repackaged; the certificate and ZIP inventory alone cannot establish its provenance.
5. **Other install constraints:** the exact Android installer error is needed to distinguish these possibilities.

## Safe diagnostic sequence

1. Keep the original ZIP unchanged and do not overwrite an installed copy.
2. Record the exact message shown by Android Package Installer.
3. If Android Platform Tools are available, run:
   ```sh
   adb install -r "PS Touch Plus.apk"
   ```
   Capture the exact `INSTALL_FAILED_...` line. Do not uninstall an existing app unless its local projects/data are backed up.
4. With Android SDK Build Tools, run:
   ```sh
   apksigner verify --verbose --print-certs "PS Touch Plus.apk"
   aapt dump badging "PS Touch Plus.apk"
   ```
5. Only after identifying the failure should we create a test variant. Raising target SDK alone cannot convert ARM32 native libraries to ARM64 or rebuild the AIR runtime/ANEs.

## Current status

No patched or rebuilt APK has been produced. This document records newly checked signing metadata and a diagnostic path; it is not a claim that installation has been fixed.
