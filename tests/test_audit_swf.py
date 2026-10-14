import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "audit_swf.py"


def u30(value):
    out = bytearray()
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def swf_tag(code, payload):
    if len(payload) < 63:
        return struct.pack("<H", (code << 6) | len(payload)) + payload
    return struct.pack("<HI", (code << 6) | 63, len(payload)) + payload


def tiny_swf(signature=b"FWS"):
    # RECT (two bytes), frame rate 24fps, one frame.
    body = b"\x08\x00\x00\x18\x01\x00"
    # Minimal ABC constant pool with two ANE-related names.
    strings = [b"TTGLCommandSequence", b"TTQuickSelection"]
    abc = struct.pack("<HH", 16, 46) + b"\x01\x01\x01" + u30(len(strings) + 1)
    for value in strings:
        abc += u30(len(value)) + value
    doabc = b"\x00\x00\x00\x00frame1\x00" + abc
    body += swf_tag(82, doabc)
    body += struct.pack("<H", 0)  # End tag
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
            files = {}
            if out.exists():
                for item in out.iterdir():
                    if item.is_file():
                        files[item.name] = item.read_text(encoding="utf-8")
            return result, files

    def test_uncompressed_swf_and_ane_string_pool(self):
        result, files = self.run_tool(tiny_swf(), 0)
        self.assertIn("SWF v10", result.stdout)
        self.assertIn("End tag found: True", files["report.md"])
        self.assertIn("Frame rate: 24.0", files["report.md"])
        self.assertIn("TTGLCommandSequence", files["report.md"])
        self.assertIn("TTQuickSelection", files["inventory.json"])

    def test_zlib_compressed_swf(self):
        result, files = self.run_tool(tiny_swf(b"CWS"), 0)
        self.assertIn("Compression: CWS", files["report.md"])

    def test_lzma_is_rejected_explicitly(self):
        result, _ = self.run_tool(tiny_swf(b"ZWS"), 2)
        self.assertIn("ZWS/LZMA", result.stderr)


if __name__ == "__main__":
    unittest.main()
