import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
from compare_apk_variants import compare, summarize
from test_decode_axml import make_minimal_manifest


def make_apk(path, swf_bytes, platform, abi_path):
    descriptor = f"""<extension xmlns="http://ns.adobe.com/air/extension/3.1">
      <id>example.test</id><versionNumber>1</versionNumber>
      <platforms><platform name="{platform}"><applicationDeployment>
        <nativeLibrary>libexample.so</nativeLibrary>
      </applicationDeployment></platform></platforms>
    </extension>"""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("AndroidManifest.xml", make_minimal_manifest())
        zf.writestr("assets/META-INF/AIR/application.xml",
                    "<application><id>air.example</id><versionNumber>1</versionNumber></application>")
        zf.writestr("assets/TTPixel.swf", swf_bytes)
        zf.writestr("assets/META-INF/AIR/extensions/example/META-INF/ANE/extension.xml", descriptor)
        zf.writestr(abi_path, b"fake native library")


class CompareApkVariantsTests(unittest.TestCase):
    def test_reports_swf_hash_and_ane_platform_differences(self):
        with tempfile.TemporaryDirectory() as tmp:
            left_path = Path(tmp) / "left.apk"
            right_path = Path(tmp) / "right.apk"
            make_apk(left_path, b"left SWF", "Android-ARM", "lib/armeabi-v7a/libexample.so")
            make_apk(right_path, b"right SWF", "Android-ARM64", "lib/arm64-v8a/libexample.so")
            result = compare(summarize(left_path), summarize(right_path))
            comp = result["comparison"]
            self.assertFalse(comp["same_abis"])
            self.assertFalse(comp["common_swf_hash_matches"]["assets/TTPixel.swf"])
            self.assertEqual(comp["ane_platforms_left"]["example.test"], ["Android-ARM"])
            self.assertEqual(comp["ane_platforms_right"]["example.test"], ["Android-ARM64"])
            self.assertIn("does not prove", result["warning"])


if __name__ == "__main__":
    unittest.main()
