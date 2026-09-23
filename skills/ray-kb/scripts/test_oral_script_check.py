from __future__ import annotations

import hashlib
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import oral_script_check as checker


SPOKEN = (
    "很多人以为模型越强，企业就越不需要现场服务。"
    "但真正进入业务之后，最难的从来不是生成一个答案，而是知道这个答案应该改变哪一步工作。"
    "管理层看到的是目标，员工看到的是任务，中间真正断掉的是责任、数据和反馈。"
    "所以判断一项服务有没有价值，不要只看工程师去了多久，要看现场问题有没有回到共同产品。"
    "如果每个客户都从头写一遍，那只是更昂贵的定制开发。"
    "如果同一种问题能被整理成下一位客户直接使用的能力，驻场才开始变成产品研究。"
    "你今天就可以检查一件事：上一个项目留下来的，到底是一份交付文档，还是下一次可以直接调用的能力。"
)


class OralScriptCheckTests(unittest.TestCase):
    def run_check(self, *args: str) -> tuple[int, str]:
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["oral_script_check.py", *args]):
            with redirect_stdout(output):
                result = checker.main()
        return result, output.getvalue()

    def write(self, root: Path, name: str, text: str) -> Path:
        path = root / name
        path.write_text(text, encoding="utf-8")
        return path

    def fast_script(self, spoken: str = SPOKEN, pending: str = "- 【编的经历】第一句的现场：需要 Ray 决定。") -> str:
        return (
            "---\n"
            "kind: oral-script\n"
            "status: draft\n"
            "production_route: fast-oral\n"
            "central_judgment: 驻场只有回流成共同能力才不是定制开发\n"
            "target_duration_seconds: 60\n"
            "recording_status: pending\n"
            "---\n\n"
            "# 测试\n\n"
            f"## 口播正文\n\n{spoken}\n\n"
            f"## 待确认\n\n{pending}\n\n"
            "## 素材与来源\n\n- [[某条笔记]]\n\n"
            "## 录制与发布收尾\n\n- [ ] 待录制\n"
        )

    def test_fast_oral_passes_with_four_sections(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            script = self.write(Path(raw), "fast.md", self.fast_script())
            result, output = self.run_check(str(script))
            self.assertEqual(result, 0, output)
            self.assertIn("模式: 原生快速口播", output)

    def test_style_is_not_checked(self) -> None:
        loose = SPOKEN + "首先我要说一句，说实话这件事一定一定一定要想清楚，综上所述你别再给自己找借口了而且这句话我就是要说得很长很长一口气说完不停下来。"
        with tempfile.TemporaryDirectory() as raw:
            script = self.write(Path(raw), "fast.md", self.fast_script(spoken=loose))
            result, output = self.run_check(str(script))
            self.assertEqual(result, 0, output)

    def test_pending_section_is_required_but_can_be_none(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            ok = self.write(Path(raw), "ok.md", self.fast_script(pending="无"))
            self.assertEqual(self.run_check(str(ok))[0], 0)
            missing = self.write(
                Path(raw), "missing.md", self.fast_script().replace("## 待确认", "## 别的")
            )
            result, output = self.run_check(str(missing))
            self.assertEqual(result, 1)
            self.assertIn("待确认", output)

    def test_spoken_text_rejects_lists_and_brackets(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            script = self.write(
                Path(raw), "fast.md", self.fast_script(spoken=SPOKEN + "\n- 列表项（镜头切换）")
            )
            result, output = self.run_check(str(script))
            self.assertEqual(result, 1)
            self.assertIn("列表或表格", output)
            self.assertIn("括号", output)

    def test_article_repurpose_checks_source_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self.write(root, "source.md", "---\nkind: draft\n---\n\n# 母稿\n")
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            body = (
                "---\nkind: oral-script\nstatus: ready-to-record\n"
                "source_draft: source\n"
                "source_sha256: {sha}\n"
                "central_judgment: 驻场只有回流成共同能力才不是定制开发\n"
                "target_duration_seconds: 60\n---\n\n"
                f"## 逐字稿\n\n{SPOKEN}\n\n"
                "## 待确认\n\n无\n\n"
                "## 素材与来源\n\n- https://example.com/source\n"
            )
            script = self.write(root, "article.md", body.replace("{sha}", sha))
            result, output = self.run_check(str(script), "--source", str(source))
            self.assertEqual(result, 0, output)
            self.assertIn("模式: 长文再分发", output)

            stale = self.write(root, "stale.md", body.replace("{sha}", "0" * 64))
            result, output = self.run_check(str(stale), "--source", str(source))
            self.assertEqual(result, 1)
            self.assertIn("已经过期", output)


if __name__ == "__main__":
    unittest.main()
