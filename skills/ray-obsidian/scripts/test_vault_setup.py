import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("vault_setup.py")
SPEC = importlib.util.spec_from_file_location("ray_vault_setup", SCRIPT_PATH)
vault_setup = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(vault_setup)


class VaultSetupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.vault = Path(self.temporary.name) / "vault"

    def tearDown(self):
        self.temporary.cleanup()

    def test_fresh_init_is_ready_and_repeatable(self):
        preview = vault_setup.initialize(self.vault, "测试库", True)
        self.assertEqual(preview["manifest"], "created")
        self.assertFalse(self.vault.exists())

        result = vault_setup.initialize(self.vault, "测试库", False)
        self.assertEqual(result["overwritten_files"], [])
        self.assertEqual(vault_setup.audit(self.vault)["status"], "ready")

        repeated = vault_setup.initialize(self.vault, "测试库", False)
        self.assertEqual(repeated["created_files"], [])
        self.assertEqual(repeated["manifest"], "preserved")
        self.assertEqual(repeated["overwritten_files"], [])

    def test_v1_manifest_upgrades_without_moving_old_content(self):
        old_note = self.vault / "10-创作/20-草稿/旧稿.md"
        old_note.parent.mkdir(parents=True)
        old_note.write_text("# 用户旧稿\n", encoding="utf-8")
        legacy = {
            "schema_version": 1,
            "layout": "ray-content-v1",
            "name": "旧版测试库",
            "created_at": "2026-01-01T00:00:00+00:00",
            "managed_by": "ray-obsidian",
        }
        (self.vault / ".ray-obsidian.json").write_text(
            json.dumps(legacy, ensure_ascii=False), encoding="utf-8"
        )

        audit = vault_setup.audit(self.vault)
        self.assertEqual(audit["status"], "incomplete")
        self.assertTrue(audit["manifest_upgrade_available"])
        preview = vault_setup.initialize(self.vault, "不会覆盖旧名称", True)
        self.assertEqual(preview["manifest"], "upgraded")

        result = vault_setup.initialize(self.vault, "不会覆盖旧名称", False)
        self.assertEqual(result["manifest"], "upgraded")
        self.assertEqual(old_note.read_text(encoding="utf-8"), "# 用户旧稿\n")
        manifest = json.loads(
            (self.vault / ".ray-obsidian.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(manifest["layout"], "ray-content-v2")
        self.assertEqual(manifest["name"], "旧版测试库")
        self.assertEqual(manifest["previous_schema_version"], 1)
        self.assertEqual(vault_setup.audit(self.vault)["status"], "ready")

    def test_unknown_manifest_is_refused(self):
        self.vault.mkdir(parents=True)
        (self.vault / ".ray-obsidian.json").write_text(
            json.dumps({"schema_version": 99, "layout": "unknown"}),
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            vault_setup.initialize(self.vault, "测试库", False)


if __name__ == "__main__":
    unittest.main()
