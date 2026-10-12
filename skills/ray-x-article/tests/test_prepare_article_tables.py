import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_article.py"
SPEC = importlib.util.spec_from_file_location("prepare_article", SCRIPT)
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class TablePackageTests(unittest.TestCase):
    def test_table_is_native_manifest_not_flattened_html(self):
        source = (
            "引言。\n\n"
            "| 项目 | Cue | Grok |\n"
            "| --- | --- | --- |\n"
            "| 费用 | 免费 | 订阅 |\n\n"
            "结论。"
        )
        body_html, blocks, images, tables = prepare.build_editor_content(source, Path("."))
        self.assertEqual(body_html, "<p>引言。</p><p>结论。</p>")
        self.assertEqual(blocks, ["引言。", "结论。"])
        self.assertEqual(images, [])
        self.assertEqual((tables[0]["row_count"], tables[0]["column_count"]), (2, 3))
        self.assertEqual(tables[0]["cells"][1], ["费用", "免费", "订阅"])
        self.assertEqual(tables[0]["after_text"], "引言。")

    def test_source_order_and_adjacency_with_image(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.png").write_bytes(b"image")
            source = (
                "引言。\n\n"
                "![图](sample.png)\n\n"
                "| 甲 | 乙 |\n| --- | --- |\n| 1 | 2 |\n\n"
                "![图二](sample.png)\n\n"
                "结论。"
            )
            _, _, images, tables = prepare.build_editor_content(source, root)
            self.assertEqual([images[0]["source_order"], tables[0]["source_order"], images[1]["source_order"]], [1, 2, 3])
            self.assertEqual(tables[0]["after_image_order"], 1)
            self.assertEqual(images[1]["after_table_order"], 1)

    def test_ragged_table_fails_instead_of_flattening(self):
        source = "前文。\n\n| 甲 | 乙 |\n| --- | --- |\n| 1 | 2 | 3 |"
        with self.assertRaisesRegex(ValueError, "列数不一致"):
            prepare.build_editor_content(source, Path("."))


if __name__ == "__main__":
    unittest.main()
