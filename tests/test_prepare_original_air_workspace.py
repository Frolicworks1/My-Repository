import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "prepare_original_air_workspace.py"


def fixture_apk(path):
    descriptor = b"""<?xml version="1.0" encoding="utf-8"?>
<application xmlns="http://ns.adobe.com/air/application/16.0">
  <id>com.adobe.pstouch</id><filename>PSTouch</filename>
  <versionNumber>1.7.7</versionNumber><versionLabel>1.7.7</versionLabel>
  <initialWindow><content>TTPixel.swf</content></initialWindow>
  <extensions><extensionID>com.example.legacy</extensionID></extensions>
  <android><manifestAdditions><![CDATA[
  <manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-sdk android:minSdkVersion="12" android:targetSdkVersion="12"/>
    <application><service android:name="air.C2DMReceiver"/>
      <receiver android:name="air.C2DMReceiver"/>
    </application>
  </manifest>]]></manifestAdditions></android>
</application>"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("assets/META-INF/AIR/application.xml", descriptor)
        z.writestr("assets/TTPixel.swf", b"SWF-FIXTURE")
        z.writestr("assets/CABConfig.xml", b"<configurations/>")
        z.writestr("assets/resource/application/test.cabmod", b"resource")
        z.writestr("assets/icons/test.png", b"icon")
        z.writestr("assets/META-INF/AIR/extensions/com.example/META-INF/ANE/extension.xml", b"<extension/>")
        z.writestr("lib/armeabi-v7a/libold.so", b"arm32")


class PrepareOriginalAirWorkspaceTests(unittest.TestCase):
    def test_preserves_original_resources_and_removes_arm32_ane_declarations(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            apk, out = base / "input.apk", base / "out"
            fixture_apk(apk)
            result = subprocess.run(
                [sys.executable, str(TOOL), str(apk), "--out", str(out)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((out / "TTPixel.swf").read_bytes(), b"SWF-FIXTURE")
            self.assertEqual((out / "resource/application/test.cabmod").read_bytes(), b"resource")
            self.assertTrue((out / "icons/test.png").exists())
            self.assertTrue((out / "ane-evidence/com.example/META-INF/ANE/extension.xml").exists())
            descriptor = (out / "application.xml").read_text(encoding="utf-8")
            self.assertIn("com.frolicworks.pstoucharm64diagnostic", descriptor)
            self.assertNotIn("com.example.legacy", descriptor)
            self.assertNotIn("C2DMReceiver", descriptor)
            self.assertIn('targetSdkVersion="35"', descriptor)
            inventory = json.loads((out / "original-air-workspace.json").read_text())
            self.assertEqual(len(inventory["ane_ids_removed_from_descriptor"]), 1)
            self.assertEqual(inventory["omitted_native_libraries"][0]["path"], "lib/armeabi-v7a/libold.so")

    def test_refuses_nonempty_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            apk, out = base / "input.apk", base / "out"
            fixture_apk(apk)
            out.mkdir()
            (out / "existing").write_text("keep")
            result = subprocess.run(
                [sys.executable, str(TOOL), str(apk), "--out", str(out)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertTrue((out / "existing").exists())


if __name__ == "__main__":
    unittest.main()
