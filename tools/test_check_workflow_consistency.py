#!/usr/bin/env python3
"""Tests for check_workflow_consistency."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.check_workflow_consistency import (
    ALL_CHECKERS,
    CheckReport,
    CheckResult,
    ConvergenceChecker,
    ExitCode,
    FileRefChecker,
    QuestionIdChecker,
    Severity,
    SpecNamingChecker,
    StepNamingChecker,
    TrackStatusChecker,
    format_report,
    main,
    resolve_root,
    run_checks,
)


class TempProjectMixin:
    """Creates a minimal project skeleton for testing."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.root = self.tmpdir / "project"
        self.root.mkdir()
        (self.root / "plan").mkdir()
        (self.root / "skills").mkdir()
        (self.root / "tools").mkdir()
        (self.root / "conductor").mkdir()
        (self.root / "spec").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def write_file(self, rel_path, content):
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


# ============================================================================
# PathResolver
# ============================================================================


class TestResolveRoot(TempProjectMixin, unittest.TestCase):

    def test_explicit_root(self):
        result = resolve_root(str(self.root))
        self.assertEqual(result, self.root.resolve())

    def test_explicit_root_missing_dirs(self):
        empty = self.tmpdir / "empty"
        empty.mkdir()
        with self.assertRaises(SystemExit) as ctx:
            resolve_root(str(empty))
        self.assertEqual(ctx.exception.code, ExitCode.FILE_ERROR)

    def test_explicit_root_nonexistent(self):
        with self.assertRaises(SystemExit) as ctx:
            resolve_root(str(self.tmpdir / "nonexistent"))
        self.assertEqual(ctx.exception.code, ExitCode.FILE_ERROR)

    def test_auto_detect_from_subdir(self):
        subdir = self.root / "tools"
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            result = resolve_root(None)
            self.assertEqual(result, self.root.resolve())
        finally:
            os.chdir(original_cwd)


# ============================================================================
# FileRefChecker
# ============================================================================


class TestFileRefChecker(TempProjectMixin, unittest.TestCase):

    def test_valid_reference(self):
        self.write_file("README.md", "See `plan/quick_reference.md` for details.")
        self.write_file("plan/quick_reference.md", "# Quick Ref")
        checker = FileRefChecker()
        results = checker.run(self.root)
        passes = [r for r in results if r.severity == Severity.PASS]
        self.assertTrue(len(passes) >= 1)

    def test_broken_reference(self):
        self.write_file("README.md", "See `plan/nonexistent.md` for details.")
        checker = FileRefChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)
        self.assertIn("nonexistent.md", fails[0].message)

    def test_markdown_link_reference(self):
        self.write_file("README.md", "[guide](plan/quick_reference.md)")
        self.write_file("plan/quick_reference.md", "# Quick Ref")
        checker = FileRefChecker()
        results = checker.run(self.root)
        passes = [r for r in results if r.severity == Severity.PASS]
        self.assertTrue(len(passes) >= 1)

    def test_same_directory_relative_link(self):
        self.write_file("conductor/index.md", "[Product](product.md)")
        self.write_file("conductor/product.md", "# Product")
        checker = FileRefChecker()
        results = checker.run(self.root)
        passes = [r for r in results if r.severity == Severity.PASS]
        self.assertTrue(len(passes) >= 1)

    def test_same_directory_broken_link(self):
        self.write_file("conductor/index.md", "[Missing](missing.md)")
        checker = FileRefChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)

    def test_anchor_link_strips_fragment(self):
        self.write_file("README.md", "[ref](plan/quick_reference.md#section)")
        self.write_file("plan/quick_reference.md", "# Quick Ref")
        checker = FileRefChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)
        passes = [r for r in results if r.severity == Severity.PASS]
        self.assertTrue(len(passes) >= 1)

    def test_pure_anchor_link_skipped(self):
        self.write_file("README.md", "See [section](#overview)")
        checker = FileRefChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_skips_urls(self):
        self.write_file("README.md", "See [docs](https://example.com/path.md)")
        checker = FileRefChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_skips_code_blocks(self):
        content = "```\n`plan/nonexistent.md`\n```"
        self.write_file("README.md", content)
        checker = FileRefChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_skips_template_paths(self):
        self.write_file("README.md", "See `[项目目录]/spec/raw_requirements.md`")
        checker = FileRefChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_no_files_returns_warning(self):
        # Empty project — no markdown files to scan
        shutil.rmtree(self.root / "plan")
        shutil.rmtree(self.root / "conductor")
        (self.root / "plan").mkdir()
        (self.root / "conductor").mkdir()
        checker = FileRefChecker()
        results = checker.run(self.root)
        self.assertTrue(len(results) >= 1)


# ============================================================================
# ConvergenceChecker
# ============================================================================


class TestConvergenceChecker(TempProjectMixin, unittest.TestCase):

    def _setup_baseline(self, threshold=3):
        self.write_file(
            "tools/scorecard_parser.py",
            f"MEDIUM_CONVERGENCE_THRESHOLD = {threshold}\n",
        )

    def test_all_consistent(self):
        self._setup_baseline(3)
        self.write_file("plan/quick_reference.md", "收敛阈值（0 高 + ≤3 中）")
        self.write_file("skills/planning-workflow.md", "0 高严重度 + ≤3 中严重度")
        self.write_file("skills/stress-test-prompts.md", "0 高 + ≤3 中")
        checker = ConvergenceChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_mismatch_detected(self):
        self._setup_baseline(3)
        self.write_file("plan/quick_reference.md", "收敛阈值（0 高 + ≤5 中）")
        self.write_file("skills/planning-workflow.md", "0 高严重度 + ≤3 中严重度")
        self.write_file("skills/stress-test-prompts.md", "0 高 + ≤3 中")
        checker = ConvergenceChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)
        self.assertIn("expected medium=3", fails[0].message)
        self.assertIn("found medium=5", fails[0].message)

    def test_source_file_missing(self):
        checker = ConvergenceChecker()
        results = checker.run(self.root)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, Severity.FAIL)
        self.assertIn("source file missing", results[0].message)

    def test_doc_file_missing(self):
        self._setup_baseline(3)
        # Don't create doc files
        checker = ConvergenceChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        # 3 doc files missing = 3 FAIL results
        self.assertEqual(len(fails), 3)

    def test_no_threshold_found_in_doc(self):
        self._setup_baseline(3)
        self.write_file("plan/quick_reference.md", "Some content without threshold")
        self.write_file("skills/planning-workflow.md", "No threshold here either")
        self.write_file("skills/stress-test-prompts.md", "Nothing here")
        checker = ConvergenceChecker()
        results = checker.run(self.root)
        warnings = [r for r in results if r.severity == Severity.WARNING]
        self.assertEqual(len(warnings), 3)


# ============================================================================
# StepNamingChecker
# ============================================================================


class TestStepNamingChecker(TempProjectMixin, unittest.TestCase):

    def test_correct_names(self):
        self.write_file("README.md", "Step 1: 灵感捕获\nStep 2: SDD 生成")
        self.write_file("plan/quick_reference.md", "Step 3: 压力测试")
        checker = StepNamingChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_alias_accepted(self):
        self.write_file("README.md", "Step 1: 灵感整理")
        checker = StepNamingChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_wrong_name_detected(self):
        self.write_file("README.md", "Step 1: 需求分析")
        checker = StepNamingChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 1)
        self.assertIn("expected '灵感捕获'", fails[0].message)

    def test_skips_table_rows(self):
        self.write_file("README.md", "| Step 1 | 任意 AI | 随便 |")
        checker = StepNamingChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_skips_code_blocks(self):
        self.write_file("README.md", "```\nStep 1: wrong_name\n```")
        checker = StepNamingChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_phase_naming(self):
        self.write_file("skills/planning-workflow.md", "Phase 0: 复盘")
        checker = StepNamingChecker()
        results = checker.run(self.root)
        passes = [r for r in results if r.severity == Severity.PASS]
        self.assertTrue(any("Phase 0" in r.message for r in passes))


# ============================================================================
# SpecNamingChecker
# ============================================================================


class TestSpecNamingChecker(TempProjectMixin, unittest.TestCase):

    def test_valid_names(self):
        self.write_file("spec/raw_requirements.md", "")
        self.write_file("spec/spec_v1.md", "")
        self.write_file("spec/scorecard_v1.json", "[]")
        self.write_file("spec/spec_final.md", "")
        self.write_file("spec/postmortem_v1.md", "")
        checker = SpecNamingChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        warnings = [r for r in results if r.severity == Severity.WARNING]
        self.assertEqual(len(fails), 0)
        self.assertEqual(len(warnings), 0)

    def test_invalid_name_warning(self):
        self.write_file("spec/notes.txt", "random file")
        checker = SpecNamingChecker()
        results = checker.run(self.root)
        warnings = [r for r in results if r.severity == Severity.WARNING]
        self.assertEqual(len(warnings), 1)
        self.assertIn("notes.txt", warnings[0].message)

    def test_empty_spec_dir(self):
        checker = SpecNamingChecker()
        results = checker.run(self.root)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, Severity.PASS)

    def test_no_spec_dir(self):
        shutil.rmtree(self.root / "spec")
        checker = SpecNamingChecker()
        results = checker.run(self.root)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, Severity.WARNING)

    def test_subdirectory_valid_names(self):
        """Verify SpecNamingChecker recurses into subdirectories."""
        (self.root / "spec" / "spec-lint").mkdir(parents=True)
        self.write_file("spec/spec-lint/raw_requirements.md", "")
        self.write_file("spec/spec-lint/spec_v1.md", "")
        self.write_file("spec/spec-lint/spec_final.md", "")
        self.write_file("spec/spec-lint/scorecard_v1.json", "[]")
        self.write_file("spec/spec-lint/postmortem.md", "")  # no version — should warn
        checker = SpecNamingChecker()
        results = checker.run(self.root)
        sub_results = [r for r in results if "spec-lint" in r.file_path]
        self.assertEqual(len(sub_results), 5)
        passes = [r for r in sub_results if r.severity == Severity.PASS]
        warns = [r for r in sub_results if r.severity == Severity.WARNING]
        self.assertEqual(len(passes), 4)
        self.assertEqual(len(warns), 1)
        self.assertIn("postmortem.md", warns[0].message)

    def test_subdirectory_invalid_name(self):
        """Verify warning for non-matching file in subdirectory."""
        (self.root / "spec" / "my-project").mkdir(parents=True)
        self.write_file("spec/my-project/notes.txt", "random")
        checker = SpecNamingChecker()
        results = checker.run(self.root)
        warns = [r for r in results if r.severity == Severity.WARNING]
        self.assertTrue(any("notes.txt" in w.message for w in warns))


# ============================================================================
# TrackStatusChecker
# ============================================================================


class TestTrackStatusChecker(TempProjectMixin, unittest.TestCase):

    VALID_TRACKS = (
        "| Status | Track ID | Title |\n"
        "| ------ | -------- | ----- |\n"
        "| pending | TRACK-001 | Test |\n"
        "\n---\n\n"
        "## TRACK-001: Test\n\n"
        "**状态：** pending — waiting\n"
    )

    def test_valid_track(self):
        self.write_file("conductor/tracks.md", self.VALID_TRACKS)
        checker = TrackStatusChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_invalid_status(self):
        content = self.VALID_TRACKS.replace("pending", "draft")
        self.write_file("conductor/tracks.md", content)
        checker = TrackStatusChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertTrue(len(fails) >= 1)

    def test_status_inconsistency(self):
        content = (
            "| Status | Track ID | Title |\n"
            "| ------ | -------- | ----- |\n"
            "| active | TRACK-001 | Test |\n"
            "\n---\n\n"
            "## TRACK-001: Test\n\n"
            "**状态：** pending — waiting\n"
        )
        self.write_file("conductor/tracks.md", content)
        checker = TrackStatusChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertTrue(any("inconsistency" in r.message for r in fails))

    def test_missing_file(self):
        checker = TrackStatusChecker()
        results = checker.run(self.root)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, Severity.FAIL)

    def test_no_table(self):
        self.write_file("conductor/tracks.md", "# Tracks\n\nNo table here.")
        checker = TrackStatusChecker()
        results = checker.run(self.root)
        self.assertEqual(results[0].severity, Severity.FAIL)
        self.assertIn("No track registry table", results[0].message)


# ============================================================================
# QuestionIdChecker
# ============================================================================


class TestQuestionIdChecker(TempProjectMixin, unittest.TestCase):

    def _write_complete_prompts(self):
        lines = []
        for i in range(1, 6):
            lines.append(f"**C{i}. CLI Question {i}**")
        for i in range(1, 11):
            lines.append(f"**U{i}. Question {i}**")
        for i in range(1, 6):
            lines.append(f"**W{i}. Question {i}**")
        for i in range(1, 6):
            lines.append(f"**D{i}. Question {i}**")
        # Add mapping table
        lines.append("\n| 新编号 | 旧编号 | 层级 |")
        lines.append("|-------|--------|------|")
        mapping = [
            ("C1", "新增"),
            ("C2", "新增"),
            ("C3", "新增"),
            ("C4", "新增"),
            ("C5", "新增"),
            ("U1", "Q3"),
            ("U2", "Q4"),
            ("U3", "Q5"),
            ("U4", "Q10"),
            ("U5", "Q14"),
            ("U6", "Q15"),
            ("U7", "Q16"),
            ("U8", "Q17"),
            ("U9", "Q18"),
            ("U10", "Q20"),
            ("W1", "Q1"),
            ("W2", "Q7"),
            ("W3", "Q8"),
            ("W4", "Q9"),
            ("W5", "Q11"),
            ("D1", "Q2"),
            ("D2", "Q6"),
            ("D3", "Q12"),
            ("D4", "Q13"),
            ("D5", "Q19"),
        ]
        for new, old in mapping:
            lines.append(f"| {new} | {old} | test |")
        self.write_file("skills/stress-test-prompts.md", "\n".join(lines))

    def test_complete_ids(self):
        self._write_complete_prompts()
        checker = QuestionIdChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertEqual(len(fails), 0)

    def test_missing_id(self):
        # Write all except U5
        lines = []
        for i in range(1, 6):
            lines.append(f"**C{i}. CLI Question**")
        for i in range(1, 11):
            if i != 5:
                lines.append(f"**U{i}. Question**")
        for i in range(1, 6):
            lines.append(f"**W{i}. Question**")
        for i in range(1, 6):
            lines.append(f"**D{i}. Question**")
        self.write_file("skills/stress-test-prompts.md", "\n".join(lines))
        checker = QuestionIdChecker()
        results = checker.run(self.root)
        fails = [r for r in results if r.severity == Severity.FAIL]
        self.assertTrue(any("U5" in r.message for r in fails))

    def test_missing_file(self):
        checker = QuestionIdChecker()
        results = checker.run(self.root)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, Severity.WARNING)


# ============================================================================
# run_checks
# ============================================================================


class TestRunChecks(TempProjectMixin, unittest.TestCase):

    def test_filter_by_name(self):
        self.write_file("spec/raw_requirements.md", "")
        report = run_checks(self.root, ["spec_naming"])
        checkers_used = {r.checker for r in report.results}
        self.assertEqual(checkers_used, {"spec_naming"})

    def test_all_checkers_run(self):
        report = run_checks(self.root)
        checkers_used = {r.checker for r in report.results}
        expected = {c.name for c in ALL_CHECKERS}
        self.assertEqual(checkers_used, expected)

    def test_invalid_checker_name_produces_empty_results(self):
        """run_checks with unknown name returns empty (main() guards this)."""
        report = run_checks(self.root, ["typo_checker"])
        self.assertEqual(len(report.results), 0)


# ============================================================================
# ReportFormatter
# ============================================================================


class TestFormatReport(unittest.TestCase):

    def _make_report(self, results):
        return CheckReport(results=results, timestamp="2026-03-02")

    def test_summary_format(self):
        report = self._make_report(
            [
                CheckResult("test", Severity.PASS, "f.md", 1, "ok"),
                CheckResult("test", Severity.FAIL, "f.md", 2, "bad"),
            ]
        )
        output = format_report(report, fmt="summary")
        self.assertEqual(output, "1 passed, 1 failed, 0 warnings")

    def test_markdown_format_has_header(self):
        report = self._make_report(
            [
                CheckResult("test", Severity.PASS, "f.md", 1, "ok"),
            ]
        )
        output = format_report(report, fmt="markdown")
        self.assertIn("## 文档一致性检查报告", output)
        self.assertIn("通过: 1 个", output)

    def test_markdown_shows_fails(self):
        report = self._make_report(
            [
                CheckResult("test", Severity.FAIL, "f.md", 10, "broken ref"),
            ]
        )
        output = format_report(report, fmt="markdown")
        self.assertIn("### 失败项", output)
        self.assertIn("broken ref", output)

    def test_verbose_shows_passes(self):
        report = self._make_report(
            [
                CheckResult("test", Severity.PASS, "f.md", 1, "all good"),
            ]
        )
        output = format_report(report, fmt="markdown", verbose=True)
        self.assertIn("### 通过项", output)
        self.assertIn("all good", output)

    def test_non_verbose_hides_passes(self):
        report = self._make_report(
            [
                CheckResult("test", Severity.PASS, "f.md", 1, "all good"),
            ]
        )
        output = format_report(report, fmt="markdown", verbose=False)
        self.assertNotIn("### 通过项", output)


# ============================================================================
# ExitCode
# ============================================================================


class TestExitCodes(TempProjectMixin, unittest.TestCase):

    def test_success_when_no_fails(self):
        self.write_file("spec/raw_requirements.md", "")
        report = run_checks(self.root, ["spec_naming"])
        has_fail = any(r.severity == Severity.FAIL for r in report.results)
        self.assertFalse(has_fail)

    def test_failure_when_has_fails(self):
        # Missing tracks.md will cause FAIL
        report = run_checks(self.root, ["track_status"])
        has_fail = any(r.severity == Severity.FAIL for r in report.results)
        self.assertTrue(has_fail)


# ============================================================================
# CLI: --check validation and stderr output
# ============================================================================


class TestCLIInvalidCheck(TempProjectMixin, unittest.TestCase):

    def test_invalid_checker_name_exits_2(self):
        with patch(
            "sys.argv", ["prog", "--root", str(self.root), "--check", "typo_checker"]
        ):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, ExitCode.FILE_ERROR)

    def test_mixed_valid_invalid_checker_exits_2(self):
        with patch(
            "sys.argv",
            ["prog", "--root", str(self.root), "--check", "file_ref,bogus"],
        ):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, ExitCode.FILE_ERROR)

    def test_valid_checker_name_does_not_exit_2(self):
        self.write_file("spec/raw_requirements.md", "")
        with patch(
            "sys.argv", ["prog", "--root", str(self.root), "--check", "spec_naming"]
        ):
            code = main()
            self.assertEqual(code, ExitCode.SUCCESS)


class TestCLIStderrOutput(TempProjectMixin, unittest.TestCase):

    def test_failures_written_to_stderr(self):
        # Missing tracks.md causes FAIL in track_status checker
        stderr_capture = io.StringIO()
        with patch(
            "sys.argv", ["prog", "--root", str(self.root), "--check", "track_status"]
        ):
            with patch("sys.stderr", stderr_capture):
                code = main()
        self.assertEqual(code, ExitCode.VALIDATION_ERROR)
        stderr_output = stderr_capture.getvalue()
        self.assertIn("FAIL [track_status]", stderr_output)

    def test_no_stderr_on_clean_run(self):
        self.write_file("spec/raw_requirements.md", "")
        stderr_capture = io.StringIO()
        with patch(
            "sys.argv", ["prog", "--root", str(self.root), "--check", "spec_naming"]
        ):
            with patch("sys.stderr", stderr_capture):
                code = main()
        self.assertEqual(code, ExitCode.SUCCESS)
        stderr_output = stderr_capture.getvalue()
        self.assertEqual(stderr_output, "")


if __name__ == "__main__":
    unittest.main()
