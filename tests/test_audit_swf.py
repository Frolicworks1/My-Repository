import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "audit_swf.py"


def tiny_swf(signature=b"FWS"):
    # RECT with Nbits=1 occupies one byte; then 24fps and one frame.
    body = b"\x08\x00\x18\x01"
    body += struct.pack("<H", (1 << 6) | 0)  # End tag
    header = b"FWS" + bytes([10]) + struct.pack("<I", 8 + len(body))
    if signature == b"FWS":
        return header + body
    if signature == b"CWS":
        return b"CWS" + header[3:8] + zlib.compress(body)
    return b"ZWS" + header[3:8] + b"not-lzma"


class AuditSwfTests(unittest.TestCase):
    def run_tool(self, payload, expect_code):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "fixture.swf"
            out = base / "out"
            source.write_bytes(payload)
            result = subprocess.run(
                [sys.executable, str(TOOL), str(source), "--out", str(out)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, expect_code, result.stderr)
            return result, out

    def test_uncompressed_swf(self):
        result, out = self.run_tool(tiny_swf(), 0)
        self.assertIn("SWF v10", result.stdout)
        report = (out / "report.md").read_text(encoding="utf-8")
        self.assertIn("End tag found: True", report)

    def test_zlib_compressed_swf(self):
        result, out = self.run_tool(tiny_swf(b"CWS"), 0)
        self.assertIn("Compression: CWS", (out / "report.md").read_text())

    def test_lzma_is_rejected_explicitly(self):
        result, _ = self.run_tool(tiny_swf(b"ZWS"), 2)
        self.assertIn("ZWS/LZMA", result.stderr)


if __name__ == "__main__":
    unittest.main()
