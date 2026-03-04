#!/usr/bin/env python3
"""Tests for spec_lint.py"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

# Ensure tools/ is on path
sys.path.insert(0, os.path.dirname(__file__))

from spec_lint import (
    Document,
    ExitCode,
    LintReport,
    LintResult,
    Severity,
    ExitCodeTableChecker,
    HeaderFormatChecker,
    PatternExampleChecker,
    SectionPresenceChecker,
    TBDMarkerChecker,
    format_report,
    parse_document,
    run_lints,
)

SPEC_LINT_PATH = os.path.join(os.path.dirname(__file__), "spec_lint.py")


def _make_well_formed_sdd():
    """Return a well-formed SDD document string with sections 1-6."""
    return """\
# My Tool — SDD
版本: v1.0
状态: Final
最后更新: 2026-03-03

---

## 1. 项目概述

Some overview text.

## 2. 技术栈

| 层次 | 技术选型 |
|------|---------|
| 语言 | Python  |

## 3. 系统架构

Architecture details.

## 4. 接口定义

> 本项目为 CLI 工具，使用变体 4.B。

### 4.B.1 命令行参数

Usage info.

### 4.B.3 Exit Code 语义

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 验证失败 |
| 2 | 使用错误 |

## 5. 数据模型

Data model info.

## 6. 错误处理策略

Error handling info.
"""


class TestDocumentParser(unittest.TestCase):
    """DocumentParser tests (5 tests)."""

    def test_parse_well_formed(self):
        doc = parse_document(_make_well_formed_sdd())
        self.assertEqual(doc.title, "My Tool — SDD")
        self.assertEqual(len(doc.sections), 6)
        self.assertEqual(doc.sections[0].number, "1")
        self.assertEqual(doc.sections[5].number, "6")
        self.assertTrue(len(doc.header_lines) <= 10)

    def test_empty_file(self):
        doc = parse_document("")
        self.assertEqual(doc.title, "")
        self.assertEqual(doc.sections, [])
        self.assertEqual(doc.raw_lines, [])

    def test_no_section_headers(self):
        doc = parse_document("# Title\n\nSome text without sections.\n")
        self.assertEqual(doc.title, "Title")
        self.assertEqual(doc.sections, [])
        self.assertTrue(len(doc.raw_lines) > 0)

    def test_mixed_heading_levels(self):
        text = "# Title\n## 1. First\n### 1.1 Sub\n## 2. Second\n#### Deep\n"
        doc = parse_document(text)
        self.assertEqual(len(doc.sections), 2)
        self.assertEqual(doc.sections[0].number, "1")
        self.assertEqual(doc.sections[1].number, "2")

    def test_multiple_titles_first_wins(self):
        text = "# First Title\n# Second Title\n## 1. Section\n"
        doc = parse_document(text)
        self.assertEqual(doc.title, "First Title")


class TestSectionPresenceChecker(unittest.TestCase):
    """SectionPresenceChecker tests (4 tests)."""

    def test_all_sections_present(self):
        doc = parse_document(_make_well_formed_sdd())
        checker = SectionPresenceChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_missing_section(self):
        # Remove section 3
        text = "# T\n## 1. A\n## 2. B\n## 4. D\n## 5. E\n## 6. F\n"
        doc = parse_document(text)
        checker = SectionPresenceChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)
        self.assertIn("3", fails[0].message)

    def test_extra_sections_pass(self):
        text = "# T\n## 1. A\n## 2. B\n## 3. C\n## 4. D\n## 5. E\n## 6. F\n## 7. Extra\n## 8. More\n"
        doc = parse_document(text)
        checker = SectionPresenceChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_non_standard_title_matches_by_number(self):
        text = "# T\n## 1. Overview\n## 2. Stack\n## 3. Arch\n## 4. API\n## 5. Data\n## 6. Errors\n"
        doc = parse_document(text)
        checker = SectionPresenceChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)


class TestHeaderFormatChecker(unittest.TestCase):
    """HeaderFormatChecker tests (4 tests)."""

    def test_all_fields_present(self):
        doc = parse_document(_make_well_formed_sdd())
        checker = HeaderFormatChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_missing_version(self):
        text = "# T\n状态: Final\n最后更新: 2026-03-03\n"
        doc = parse_document(text)
        checker = HeaderFormatChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)
        self.assertIn("版本", fails[0].message)

    def test_missing_status(self):
        text = "# T\n版本: v1.0\n最后更新: 2026-03-03\n"
        doc = parse_document(text)
        checker = HeaderFormatChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)
        self.assertIn("状态", fails[0].message)

    def test_version_without_v_prefix(self):
        text = "# T\n版本: 1.0\n状态: Final\n最后更新: 2026-03-03\n"
        doc = parse_document(text)
        checker = HeaderFormatChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)
        self.assertIn("版本", fails[0].message)


class TestTBDMarkerChecker(unittest.TestCase):
    """TBDMarkerChecker tests (6 tests)."""

    def test_clean_document(self):
        doc = parse_document("# Title\n\nAll content is complete.\n")
        checker = TBDMarkerChecker()
        results = checker.run(doc)
        self.assertTrue(all(r.severity == Severity.PASS for r in results))

    def test_tbd_in_text(self):
        doc = parse_document("# Title\n\n数据库选型: TBD\n")
        checker = TBDMarkerChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)
        self.assertEqual(fails[0].line_number, 3)

    def test_chinese_marker(self):
        doc = parse_document("# Title\n\n认证方式待定\n")
        checker = TBDMarkerChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)

    def test_code_block_skipped(self):
        text = "# Title\n\n```\nclass TBDMarkerChecker:\n    pass\n```\n\nClean text.\n"
        doc = parse_document(text)
        checker = TBDMarkerChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_todo_at_line_start(self):
        doc = parse_document("# Title\n\nTODO: add error codes\n")
        checker = TBDMarkerChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)

    def test_table_definition_no_false_positive(self):
        doc = parse_document("# Title\n\ntable_definition is fine\n")
        checker = TBDMarkerChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)


class TestExitCodeTableChecker(unittest.TestCase):
    """ExitCodeTableChecker tests (4 tests)."""

    def test_complete_table(self):
        doc = parse_document(_make_well_formed_sdd())
        checker = ExitCodeTableChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_missing_exit_code(self):
        text = """\
# T
## 4. 接口定义

### 4.B.1 命令行参数

Usage.

### 4.B.3 Exit Code

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 失败 |
"""
        doc = parse_document(text)
        checker = ExitCodeTableChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)
        self.assertIn("2", fails[0].message)

    def test_no_4b_header_skips(self):
        text = "# T\n## 4. 接口定义\n\nSome API docs.\n"
        doc = parse_document(text)
        checker = ExitCodeTableChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_table_header_not_counted(self):
        text = """\
# T
## 4. 接口定义

### 4.B.3 Exit Code

| code | 含义 |
|------|------|
| 0 | 成功 |
| 1 | 失败 |
| 2 | 使用错误 |
"""
        doc = parse_document(text)
        checker = ExitCodeTableChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)


class TestPatternExampleChecker(unittest.TestCase):
    """PatternExampleChecker tests (5 tests)."""

    def _make_section8_doc(self, blocks):
        """Build a document with a §8 containing given checker blocks."""
        lines = ["# T\n## 8. 模式定义约束\n"]
        for name, positives, negatives in blocks:
            lines.append("### %s\n" % name)
            lines.append("检查器: %s\n" % name)
            lines.append("匹配模式: `test`\n\n")
            lines.append("正例（应匹配）:\n")
            for i in range(positives):
                lines.append("  %d. example %d\n" % (i + 1, i + 1))
            lines.append("\n反例（不应匹配）:\n")
            for i in range(negatives):
                lines.append("  %d. counter %d\n" % (i + 1, i + 1))
            lines.append("\n")
        return parse_document("".join(lines))

    def test_sufficient_examples(self):
        doc = self._make_section8_doc([("FooChecker", 3, 3)])
        checker = PatternExampleChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_insufficient_positives(self):
        doc = self._make_section8_doc([("FooChecker", 2, 3)])
        checker = PatternExampleChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)
        self.assertIn("positive", fails[0].message)

    def test_no_section8_skips(self):
        doc = parse_document("# T\n## 1. Overview\n")
        checker = PatternExampleChecker()
        results = checker.run(doc)
        self.assertEqual(len(results), 0)

    def test_multiple_blocks_one_incomplete(self):
        doc = self._make_section8_doc([
            ("FooChecker", 3, 3),
            ("BarChecker", 1, 3),
        ])
        checker = PatternExampleChecker()
        results = checker.run(doc)
        fails = [r for r in results if r.severity == Severity.FAIL]
        passes = [r for r in results if r.severity == Severity.PASS]
        self.assertEqual(len(fails), 1)
        self.assertEqual(len(passes), 1)
        self.assertIn("BarChecker", fails[0].message)

    def test_self_check_skipped(self):
        doc = self._make_section8_doc([
            ("SomeChecker", 3, 3),
            ("PatternExampleChecker", 0, 0),
        ])
        checker = PatternExampleChecker()
        results = checker.run(doc)
        # Should only have results for SomeChecker, not PatternExampleChecker
        self.assertEqual(len(results), 1)
        self.assertIn("SomeChecker", results[0].message)


class TestCLIIntegration(unittest.TestCase):
    """CLI integration tests (16 tests)."""

    def _run(self, args, input_text=None):
        """Run spec_lint.py with given args, return (stdout, stderr, returncode)."""
        cmd = [sys.executable, SPEC_LINT_PATH] + args
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
        )
        return result.stdout, result.stderr, result.returncode

    def _write_temp(self, content, suffix=".md"):
        """Write content to a temp file and return path."""
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_valid_file_exit_0(self):
        path = self._write_temp(_make_well_formed_sdd())
        try:
            stdout, stderr, rc = self._run([path])
            self.assertEqual(rc, 0)
            self.assertIn("passed", stdout)
        finally:
            os.unlink(path)

    def test_missing_file_exit_2(self):
        stdout, stderr, rc = self._run(["nonexistent_file_xyz.md"])
        self.assertEqual(rc, 2)
        self.assertIn("Error: file not found:", stderr)

    def test_binary_file_exit_2(self):
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "wb") as f:
            f.write(b"\x80\x81\x82\xff\xfe")
        try:
            stdout, stderr, rc = self._run([path])
            self.assertEqual(rc, 2)
            self.assertIn("Error: cannot read file", stderr)
        finally:
            os.unlink(path)

    def test_empty_file_exit_0(self):
        path = self._write_temp("")
        try:
            stdout, stderr, rc = self._run([path])
            self.assertEqual(rc, 0)
            self.assertIn("warning", stdout.lower())
        finally:
            os.unlink(path)

    def test_empty_file_strict_exit_1(self):
        path = self._write_temp("")
        try:
            stdout, stderr, rc = self._run(["--strict", path])
            self.assertEqual(rc, 1)
        finally:
            os.unlink(path)

    def test_empty_file_with_check_still_shortcircuits(self):
        path = self._write_temp("")
        try:
            stdout, stderr, rc = self._run(["--check", "section_presence", "--format", "json", path])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            # Should have input_validation warning, not section_presence results
            checkers = {r["checker"] for r in data["results"]}
            self.assertEqual(checkers, {"input_validation"})
        finally:
            os.unlink(path)

    def test_strict_with_warning_exit_1(self):
        # A doc missing section 3 produces FAIL, but let's test warning + strict
        # Use an empty file which produces a WARNING
        path = self._write_temp("")
        try:
            stdout, stderr, rc = self._run(["--strict", path])
            self.assertEqual(rc, 1)
        finally:
            os.unlink(path)

    def test_format_json_valid(self):
        path = self._write_temp(_make_well_formed_sdd())
        try:
            stdout, stderr, rc = self._run(["--format", "json", path])
            data = json.loads(stdout)
            self.assertIn("results", data)
            self.assertIn("summary", data)
            self.assertIsInstance(data["results"], list)
        finally:
            os.unlink(path)

    def test_check_single_checker(self):
        path = self._write_temp(_make_well_formed_sdd())
        try:
            stdout, stderr, rc = self._run(["--check", "section_presence", "--format", "json", path])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            checkers = {r["checker"] for r in data["results"]}
            self.assertEqual(checkers, {"section_presence"})
        finally:
            os.unlink(path)

    def test_check_with_whitespace_trim(self):
        path = self._write_temp(_make_well_formed_sdd())
        try:
            stdout, stderr, rc = self._run(["--check", "section_presence, tbd_marker", "--format", "json", path])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            checkers = {r["checker"] for r in data["results"]}
            self.assertEqual(checkers, {"section_presence", "tbd_marker"})
        finally:
            os.unlink(path)

    def test_check_unknown_name_exit_2(self):
        stdout, stderr, rc = self._run(["--check", "unknown_name", "somefile.md"])
        self.assertEqual(rc, 2)
        self.assertIn("Error: unknown checker:", stderr)

    def test_check_all_empty_exit_2(self):
        stdout, stderr, rc = self._run(["--check", ",", "somefile.md"])
        self.assertEqual(rc, 2)
        self.assertIn("Error: no valid checker names provided", stderr)

    def test_check_unknown_before_file_check(self):
        # --check validated before file read
        stdout, stderr, rc = self._run(["--check", "unknown_name", "nonexistent.md"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown checker", stderr)
        self.assertNotIn("file not found", stderr)

    def test_check_empty_before_file_check(self):
        stdout, stderr, rc = self._run(["--check", ",", "nonexistent.md"])
        self.assertEqual(rc, 2)
        self.assertIn("no valid checker names", stderr)
        self.assertNotIn("file not found", stderr)

    def test_check_input_validation_rejected(self):
        stdout, stderr, rc = self._run(["--check", "input_validation", "somefile.md"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown checker", stderr)

    def test_verbose_includes_pass(self):
        path = self._write_temp(_make_well_formed_sdd())
        try:
            stdout, stderr, rc = self._run(["--verbose", path])
            self.assertIn("PASS", stdout)
        finally:
            os.unlink(path)


class TestStderrFormat(unittest.TestCase):
    """stderr format tests (2 tests)."""

    def _write_temp(self, content):
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_fail_stderr_format(self):
        # Missing section → FAIL
        text = "# T\n版本: v1.0\n状态: Final\n最后更新: 2026-03-03\n## 1. A\n"
        path = self._write_temp(text)
        try:
            cmd = [sys.executable, SPEC_LINT_PATH, path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            # Should have FAIL lines in stderr
            fail_lines = [l for l in result.stderr.splitlines() if l.startswith("FAIL")]
            self.assertTrue(len(fail_lines) > 0)
            # Check format: FAIL [checker] file:line: message
            for line in fail_lines:
                self.assertRegex(line, r"^FAIL \[\w+\] .+:\d+: .+")
        finally:
            os.unlink(path)

    def test_warn_stderr_format(self):
        path = self._write_temp("")
        try:
            cmd = [sys.executable, SPEC_LINT_PATH, path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            warn_lines = [l for l in result.stderr.splitlines() if l.startswith("WARN")]
            self.assertTrue(len(warn_lines) > 0)
            for line in warn_lines:
                self.assertRegex(line, r"^WARN \[\w+\] .+:\d+: .+")
        finally:
            os.unlink(path)


class TestFormatOutputs(unittest.TestCase):
    """Format output tests (6 tests)."""

    def _make_report(self):
        return LintReport(
            results=[
                LintResult("section_presence", Severity.PASS, 0, "Section 1 present"),
                LintResult("tbd_marker", Severity.FAIL, 42, "TBD marker found"),
                LintResult("header_format", Severity.WARNING, 0, "Missing field"),
            ],
            file_path="test.md",
        )

    def test_summary_format(self):
        report = self._make_report()
        output = format_report(report, fmt="summary")
        self.assertIn("passed", output)
        self.assertIn("failed", output)

    def test_json_format_valid(self):
        report = self._make_report()
        output = format_report(report, fmt="json")
        data = json.loads(output)
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_json_severity_lowercase(self):
        report = self._make_report()
        output = format_report(report, fmt="json")
        data = json.loads(output)
        severities = {r["severity"] for r in data["results"]}
        self.assertTrue(severities.issubset({"pass", "warning", "fail"}))

    def test_json_results_order(self):
        report = self._make_report()
        output = format_report(report, fmt="json")
        data = json.loads(output)
        checkers = [r["checker"] for r in data["results"]]
        self.assertEqual(checkers, ["section_presence", "tbd_marker", "header_format"])

    def test_json_verbose_no_effect(self):
        report = self._make_report()
        output_normal = format_report(report, fmt="json", verbose=False)
        output_verbose = format_report(report, fmt="json", verbose=True)
        self.assertEqual(json.loads(output_normal), json.loads(output_verbose))

    def test_markdown_format_headers(self):
        report = self._make_report()
        output = format_report(report, fmt="markdown")
        self.assertIn("##", output)
        self.assertIn("失败项", output)


if __name__ == "__main__":
    unittest.main()
