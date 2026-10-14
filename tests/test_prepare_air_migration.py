import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "prepare_air_migration.py"


class PrepareAirMigrationTests(unittest.TestCase):
    def test_extracts_complete_embedded_ane_payload_and_descriptor(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            apk = base / "fixture.apk"
            out = base / "out"
            with zipfile.ZipFile(apk, "w") as zf:
                zf.writestr("assets/TTPixel.swf", b"main-swf")
                zf.writestr("assets/META-INF/AIR/application.xml", b"<application/>")
                zf.writestr(
                    "assets/META-INF/AIR/extensions/com.example/META-INF/ANE/extension.xml",
                    b"<extension/>",
                )
                zf.writestr(
                    "assets/META-INF/AIR/extensions/com.example/META-INF/ANE/Android-ARM/library.swf",
                    b"ane-library-swf",
                )
                zf.writestr(
                    "assets/META-INF/AIR/extensions/com.example/META-INF/ANE/Android-ARM/libnative.so",
                    b"arm32-native",
                )
                zf.writestr("lib/armeabi-v7a/libair.so", b"runtime-arm32")
                zf.writestr("assets/unrelated.txt", b"not needed")

            result = subprocess.run(
                [sys.executable, str(TOOL), str(apk), "--out", str(out)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = [
                "assets/TTPixel.swf",
                "assets/META-INF/AIR/application.xml",
                "assets/META-INF/AIR/extensions/com.example/META-INF/ANE/extension.xml",
                "assets/META-INF/AIR/extensions/com.example/META-INF/ANE/Android-ARM/library.swf",
                "assets/META-INF/AIR/extensions/com.example/META-INF/ANE/Android-ARM/libnative.so",
                "lib/armeabi-v7a/libair.so",
            ]
            for rel in expected:
                self.assertTrue((out / rel).is_file(), f"missing extracted file: {rel}")
            self.assertFalse((out / "assets/unrelated.txt").exists())
            inventory = json.loads((out / "migration-input-inventory.json").read_text(encoding="utf-8"))
            self.assertEqual(inventory["native_abi_counts"]["armeabi-v7a"], 1)
            self.assertEqual(inventory["native_abi_counts"]["ANE-Android-ARM"], 1)
            self.assertEqual(len(inventory["source_apk_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
