import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "arm64_build_gate.py"


def elf_header(elf_class, machine):
    data = bytearray(64)
    data[:4] = bytes((127, 69, 76, 70))
    data[4] = elf_class
    data[5] = 1
    struct.pack_into("<H", data, 18, machine)
    return bytes(data)


class Arm64BuildGateTests(unittest.TestCase):
    def test_blocks_arm32_only_ane_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "inputs"
            descriptor = root / "extensions" / "ttpixel" / "META-INF" / "ANE" / "extension.xml"
            descriptor.parent.mkdir(parents=True)
            descriptor.write_text("""<extension xmlns="http://ns.adobe.com/air/extension/3.1">
              <id>com.adobe.ttpixel.extension</id><versionNumber>1</versionNumber>
              <platforms><platform name="Android-ARM"><applicationDeployment>
                <nativeLibrary>libTTPixelExtensionAndroid.so</nativeLibrary>
              </applicationDeployment></platform></platforms>
            </extension>""", encoding="utf-8")
            lib = descriptor.parent / "Android-ARM" / "libTTPixelExtensionAndroid.so"
            lib.parent.mkdir()
            lib.write_bytes(elf_header(1, 40))
            out = Path(tmp) / "report"
            result = subprocess.run([sys.executable, str(TOOL), str(root), "--out", str(out)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            report = json.loads((out / "preflight.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "blocked")
            self.assertTrue(any("no Android ARM64 platform entry" in x for x in report["blockers"]))
            self.assertIn("ELF32", (out / "preflight.md").read_text(encoding="utf-8"))

    def test_passes_only_when_arm64_descriptor_has_aarch64_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "inputs"
            descriptor = root / "extensions" / "example" / "META-INF" / "ANE" / "extension.xml"
            descriptor.parent.mkdir(parents=True)
            descriptor.write_text("""<extension xmlns="http://ns.adobe.com/air/extension/3.1">
              <id>example.arm64</id><versionNumber>1</versionNumber>
              <platforms><platform name="Android-ARM64"><applicationDeployment>
                <nativeLibrary>libexample.so</nativeLibrary>
              </applicationDeployment></platform></platforms>
            </extension>""", encoding="utf-8")
            lib = descriptor.parent / "Android-ARM64" / "libexample.so"
            lib.parent.mkdir()
            lib.write_bytes(elf_header(2, 183))
            out = Path(tmp) / "report"
            result = subprocess.run([sys.executable, str(TOOL), str(root), "--out", str(out)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((out / "preflight.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "preflight-passed")
            self.assertEqual(report["blockers"], [])
            self.assertIn("AArch64", (out / "preflight.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
