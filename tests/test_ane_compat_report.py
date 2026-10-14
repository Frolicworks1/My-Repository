import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "tests"))

from test_decode_axml import make_minimal_manifest


def fake_arm_elf():
    # Minimal ELF header sufficient for the report's architecture triage.
    header = bytearray(64)
    header[:4] = bytes((127, 69, 76, 70))
    header[4] = 1  # ELFCLASS32
    header[5] = 1  # little endian
    struct.pack_into("<H", header, 18, 40)  # EM_ARM
    return bytes(header)


class AneCompatibilityReportTests(unittest.TestCase):
    def test_cli_reports_arm32_and_missing_arm64_ane(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            apk = tmp_path / "fixture.apk"
            out = tmp_path / "report"
            extension = """<extension xmlns="http://ns.adobe.com/air/extension/3.1">
              <id>example.test</id><versionNumber>1</versionNumber>
              <platforms><platform name="Android-ARM">
                <applicationDeployment><nativeLibrary>libexample.so</nativeLibrary></applicationDeployment>
              </platform><platform name="iPhone-ARM">
                <applicationDeployment><nativeLibrary>libexample-ios.a</nativeLibrary></applicationDeployment>
              </platform></platforms>
            </extension>"""
            with zipfile.ZipFile(apk, "w") as zf:
                zf.writestr("AndroidManifest.xml", make_minimal_manifest())
                zf.writestr("lib/armeabi-v7a/libexample.so", fake_arm_elf())
                zf.writestr("example.ane/META-INF/ANE/extension.xml", extension)
                zf.writestr("classes.dex", b"com.google.android.c2dm")

            result = subprocess.run(
                [sys.executable, str(TOOLS / "ane_compat_report.py"),
                 str(apk), "--out", str(out)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((out / "compatibility.json").read_text(encoding="utf-8"))
            self.assertEqual(report["abis"], ["armeabi-v7a"])
            self.assertTrue(any(x["id"] == "no-arm64-native-libraries" for x in report["findings"]))
            self.assertTrue(any(x["id"] == "ane-missing-arm64" for x in report["findings"]))
            self.assertTrue(any(x["id"] == "legacy-c2dm" for x in report["findings"]))
            self.assertIn("iPhone-ARM", (out / "report.md").read_text(encoding="utf-8"))
            self.assertIn("example.test", (out / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
