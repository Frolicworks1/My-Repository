import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "rebuild" / "ane" / "ttpixel_capabilities.json"
DOC = ROOT / "docs" / "TTPixel_ARM64_REPLACEMENT_CONTRACT.md"


class TTPixelContractTests(unittest.TestCase):
    def test_inventory_is_well_formed_and_conservative(self):
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["extension_id"], "com.adobe.ttpixel.extension")
        self.assertIn("allow_fake_success", data["global_rules"])
        self.assertFalse(data["global_rules"]["allow_fake_success"])
        self.assertTrue(data["global_rules"]["require_behavioral_tests_before_implemented"])
        self.assertGreaterEqual(len(data["capabilities"]), 1)
        ids = [item["id"] for item in data["capabilities"]]
        self.assertEqual(len(ids), len(set(ids)))
        allowed = set(data["status_vocabulary"])
        for item in data["capabilities"]:
            self.assertIn(item["status"], allowed)
            self.assertTrue(item["symbols"], item["id"])
            self.assertTrue(item["acceptance"], item["id"])
            self.assertNotEqual(item["status"], "implemented")

    def test_document_states_current_limitation(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("not evidence that a replacement exists", text)
        self.assertIn("All TTPixel capabilities", text)
        self.assertIn("runtime traces", text)


if __name__ == "__main__":
    unittest.main()
