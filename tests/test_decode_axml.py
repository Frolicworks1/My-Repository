import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from decode_axml import parse_axml

NO_INDEX = 0xFFFFFFFF

def utf8_string(value):
    raw = value.encode("utf-8")
    n = len(raw)
    first = bytes([n]) if n < 0x80 else bytes([(n >> 8) | 0x80, n & 0xFF])
    return first + bytes([n]) + raw + b"\x00"

def make_minimal_manifest():
    strings = ["manifest", "package", "com.example.fixture"]
    encoded = [utf8_string(s) for s in strings]
    string_data = b"".join(encoded)
    header_size = 28
    offsets_start = header_size
    strings_start = header_size + 4 * len(strings)
    string_pool_size = strings_start + len(string_data)
    pool = struct.pack("<HHI", 0x0001, header_size, string_pool_size)
    pool += struct.pack("<IIIII", len(strings), 0, 0x100, strings_start, 0)
    pool += b"".join(struct.pack("<I", sum(len(x) for x in encoded[:i])) for i in range(len(strings)))
    pool += string_data
    # Start-element node header: line=1, comment=NO_INDEX, name index=0.
    # Attribute extension starts at offset 16; attributes begin 20 bytes after it.
    element_size = 16 + 20 + 20
    element = struct.pack("<HHI", 0x0102, 16, element_size)
    element += struct.pack("<II", 1, NO_INDEX)
    element += struct.pack("<IIHHHHHH", NO_INDEX, 0, 20, 20, 1, 0, 0, 0)
    # One attribute: ns=NO_INDEX, name=1, rawValue=2, typed string value=2.
    element += struct.pack("<IIIHBBI", NO_INDEX, 1, 2, 8, 0, 3, 2)
    total = 8 + len(pool) + len(element)
    root = struct.pack("<HHI", 0x0003, 8, total)
    return root + pool + element

class DecodeAxmlTests(unittest.TestCase):
    def test_reads_manifest_package_attribute(self):
        result = parse_axml(make_minimal_manifest())
        self.assertEqual(result["package"], "com.example.fixture")
        self.assertEqual(result["element_count"], 1)

    def test_rejects_non_axml(self):
        with self.assertRaises(ValueError):
            parse_axml(b"not xml")

if __name__ == "__main__":
    unittest.main()
