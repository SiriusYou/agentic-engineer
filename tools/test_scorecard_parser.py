#!/usr/bin/env python3
"""Unit tests for scorecard_parser."""
import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure the tools package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.scorecard_parser import (
    ExitCode,
    check_consistency_warnings,
    check_duplicate_warnings,
    extract_version,
    generate_convergence,
    generate_markdown,
    main,
    parse_scorecard,
    sanitize_markdown,
    sort_key,
    validate_entry,
)


class _TempDirMixin:
    """Mixin that provides auto-cleaned temporary directory for test classes."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmpdir.cleanup()

    def _write_temp_json(self, data, filename="scorecard.json"):
        """Write data to a temporary JSON file and return its path."""
        filepath = os.path.join(self._tmpdir.name, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return filepath


def _write_temp_json(data, filename="scorecard.json"):
    """Write data to a temporary JSON file and return its path (legacy helper)."""
    tmpdir = tempfile.mkdtemp()
    filepath = os.path.join(tmpdir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return filepath


class TestSortKey(unittest.TestCase):
    """Test sort_key function for correct ordering."""

    def test_u_before_w_before_d(self):
        entries = [
            {"question_id": "D1"},
            {"question_id": "W1"},
            {"question_id": "U1"},
        ]
        result = sorted(entries, key=sort_key)
        ids = [e["question_id"] for e in result]
        self.assertEqual(ids, ["U1", "W1", "D1"])

    def test_numeric_within_prefix(self):
        entries = [
            {"question_id": "U10"},
            {"question_id": "U2"},
            {"question_id": "U1"},
        ]
        result = sorted(entries, key=sort_key)
        ids = [e["question_id"] for e in result]
        self.assertEqual(ids, ["U1", "U2", "U10"])

    def test_unknown_prefix_sorts_after_d(self):
        entries = [
            {"question_id": "X1"},
            {"question_id": "D1"},
            {"question_id": "U1"},
        ]
        result = sorted(entries, key=sort_key)
        ids = [e["question_id"] for e in result]
        self.assertEqual(ids, ["U1", "D1", "X1"])

    def test_mixed_sorting(self):
        entries = [
            {"question_id": "W2"},
            {"question_id": "U5"},
            {"question_id": "D1"},
            {"question_id": "U1"},
            {"question_id": "W1"},
        ]
        result = sorted(entries, key=sort_key)
        ids = [e["question_id"] for e in result]
        self.assertEqual(ids, ["U1", "U5", "W1", "W2", "D1"])


class TestValidateEntry(unittest.TestCase):
    """Test validate_entry function."""

    def test_valid_entry_no_errors(self):
        entry = {
            "question_id": "U1",
            "passed": True,
            "severity": "none",
            "vulnerability": "无",
        }
        errors = validate_entry(entry, 0)
        self.assertEqual(errors, [])

    def test_missing_required_field(self):
        entry = {"question_id": "U1", "passed": True, "severity": "none"}
        errors = validate_entry(entry, 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("vulnerability", errors[0])
        self.assertIn("missing required field", errors[0])

    def test_missing_multiple_fields(self):
        entry = {"question_id": "U1"}
        errors = validate_entry(entry, 2)
        self.assertEqual(len(errors), 3)
        for err in errors:
            self.assertIn("entry[2]", err)

    def test_unknown_severity(self):
        entry = {
            "question_id": "U1",
            "passed": True,
            "severity": "critical",
            "vulnerability": "无",
        }
        errors = validate_entry(entry, 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("invalid value 'critical'", errors[0])
        self.assertIn("high", errors[0])
        self.assertIn("low", errors[0])
        self.assertIn("medium", errors[0])
        self.assertIn("none", errors[0])

    def test_non_dict_entry(self):
        errors = validate_entry("not a dict", 3)
        self.assertEqual(len(errors), 1)
        self.assertIn("expected object", errors[0])
        self.assertIn("entry[3]", errors[0])

    def test_extra_fields_ignored(self):
        entry = {
            "question_id": "U1",
            "passed": True,
            "severity": "none",
            "vulnerability": "无",
            "extra_field": "should be ignored",
            "another": 42,
        }
        errors = validate_entry(entry, 0)
        self.assertEqual(errors, [])


class TestConsistencyWarnings(unittest.TestCase):
    """Test check_consistency_warnings function."""

    def test_passed_true_severity_high_warns(self):
        entry = {
            "question_id": "U1",
            "passed": True,
            "severity": "high",
            "vulnerability": "test",
        }
        warnings = check_consistency_warnings(entry, 0)
        self.assertEqual(len(warnings), 1)
        self.assertIn("passed=true but severity=high", warnings[0])
        self.assertIn("trusting severity", warnings[0])

    def test_passed_true_severity_medium_warns(self):
        entry = {
            "question_id": "U1",
            "passed": True,
            "severity": "medium",
            "vulnerability": "test",
        }
        warnings = check_consistency_warnings(entry, 0)
        self.assertEqual(len(warnings), 1)
        self.assertIn("passed=true but severity=medium", warnings[0])

    def test_passed_false_severity_none_warns(self):
        entry = {
            "question_id": "U1",
            "passed": False,
            "severity": "none",
            "vulnerability": "无",
        }
        warnings = check_consistency_warnings(entry, 0)
        self.assertEqual(len(warnings), 1)
        self.assertIn("passed=false but severity=none", warnings[0])

    def test_consistent_entry_no_warnings(self):
        entry = {
            "question_id": "U1",
            "passed": False,
            "severity": "high",
            "vulnerability": "test",
        }
        warnings = check_consistency_warnings(entry, 0)
        self.assertEqual(warnings, [])

    def test_passed_true_severity_none_no_warning(self):
        entry = {
            "question_id": "U1",
            "passed": True,
            "severity": "none",
            "vulnerability": "无",
        }
        warnings = check_consistency_warnings(entry, 0)
        self.assertEqual(warnings, [])


class TestDuplicateWarnings(unittest.TestCase):
    """Test check_duplicate_warnings function."""

    def test_no_duplicates(self):
        entries = [
            {"question_id": "U1"},
            {"question_id": "U2"},
            {"question_id": "W1"},
        ]
        warnings = check_duplicate_warnings(entries)
        self.assertEqual(warnings, [])

    def test_duplicate_detected(self):
        entries = [
            {"question_id": "U1"},
            {"question_id": "U2"},
            {"question_id": "U1"},
        ]
        warnings = check_duplicate_warnings(entries)
        self.assertEqual(len(warnings), 1)
        self.assertIn("duplicate question_id 'U1'", warnings[0])
        self.assertIn("entry[0]", warnings[0])
        self.assertIn("entry[2]", warnings[0])


class TestExtractVersion(unittest.TestCase):
    """Test extract_version function."""

    def test_standard_version(self):
        self.assertEqual(extract_version("scorecard_v1.json"), "v1")

    def test_version_with_prefix(self):
        self.assertEqual(extract_version("stress_scorecard_v3.json"), "v3")

    def test_no_version(self):
        self.assertEqual(extract_version("scorecard.json"), "unknown")

    def test_version_in_path(self):
        self.assertEqual(extract_version("/path/to/scorecard_v12.json"), "v12")

    def test_no_underscore_version(self):
        self.assertEqual(extract_version("results.json"), "unknown")

    def test_v_without_number(self):
        self.assertEqual(extract_version("scorecard_v.json"), "unknown")

    def test_multiple_v_parts(self):
        self.assertEqual(extract_version("data_v2_v5.json"), "v5")


class TestParseScorecard(unittest.TestCase):
    """Test parse_scorecard function."""

    def test_valid_file(self):
        data = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "none",
                "vulnerability": "无",
            }
        ]
        filepath = _write_temp_json(data)
        entries, warnings = parse_scorecard(filepath)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["question_id"], "U1")
        self.assertEqual(warnings, [])

    def test_file_not_found_exits_2(self):
        with self.assertRaises(SystemExit) as cm:
            parse_scorecard("/nonexistent/path/file.json")
        self.assertEqual(cm.exception.code, ExitCode.FILE_ERROR)

    def test_non_array_json_exits_1(self):
        filepath = _write_temp_json({"key": "value"})
        with self.assertRaises(SystemExit) as cm:
            parse_scorecard(filepath)
        self.assertEqual(cm.exception.code, ExitCode.VALIDATION_ERROR)

    def test_missing_field_exits_1(self):
        data = [{"question_id": "U1", "passed": True}]
        filepath = _write_temp_json(data)
        with self.assertRaises(SystemExit) as cm:
            parse_scorecard(filepath)
        self.assertEqual(cm.exception.code, ExitCode.VALIDATION_ERROR)

    def test_unknown_severity_exits_1(self):
        data = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "critical",
                "vulnerability": "无",
            }
        ]
        filepath = _write_temp_json(data)
        with self.assertRaises(SystemExit) as cm:
            parse_scorecard(filepath)
        self.assertEqual(cm.exception.code, ExitCode.VALIDATION_ERROR)

    def test_empty_array_returns_empty(self):
        filepath = _write_temp_json([])
        entries, warnings = parse_scorecard(filepath)
        self.assertEqual(entries, [])
        self.assertEqual(warnings, [])

    def test_extra_fields_ignored(self):
        data = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "none",
                "vulnerability": "无",
                "extra": "ignored",
            }
        ]
        filepath = _write_temp_json(data)
        entries, warnings = parse_scorecard(filepath)
        self.assertEqual(len(entries), 1)
        self.assertEqual(warnings, [])

    def test_consistency_warning_returned(self):
        data = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "high",
                "vulnerability": "test",
            }
        ]
        filepath = _write_temp_json(data)
        entries, warnings = parse_scorecard(filepath)
        self.assertEqual(len(warnings), 1)
        self.assertIn("passed=true but severity=high", warnings[0])

    def test_duplicate_warning_returned(self):
        data = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "none",
                "vulnerability": "无",
            },
            {
                "question_id": "U1",
                "passed": False,
                "severity": "high",
                "vulnerability": "dup",
            },
        ]
        filepath = _write_temp_json(data)
        entries, warnings = parse_scorecard(filepath)
        self.assertEqual(len(entries), 2)
        dup_warnings = [w for w in warnings if "duplicate" in w]
        self.assertTrue(len(dup_warnings) >= 1)


class TestGenerateMarkdown(unittest.TestCase):
    """Test generate_markdown function."""

    def test_valid_entries_produce_table(self):
        entries = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "none",
                "vulnerability": "无",
            },
            {
                "question_id": "U2",
                "passed": False,
                "severity": "high",
                "vulnerability": "问题描述",
            },
        ]
        lines = generate_markdown(entries, "v1", "2026-03-02")
        output = "\n".join(lines)
        self.assertIn("## 压力测试漏洞记录", output)
        self.assertIn("日期: 2026-03-02", output)
        self.assertIn("Spec 版本: v1", output)
        self.assertIn("| U1", output)
        self.assertIn("| U2", output)

    def test_empty_entries_produce_header_only(self):
        lines = generate_markdown([], "v1", "2026-03-02")
        output = "\n".join(lines)
        self.assertIn("## 压力测试漏洞记录", output)
        self.assertIn("| 题号 |", output)
        # No data rows beyond the header
        table_rows = [l for l in lines if l.startswith("| U") or l.startswith("| W") or l.startswith("| D")]
        self.assertEqual(len(table_rows), 0)

    def test_sorting_in_output(self):
        entries = [
            {
                "question_id": "W1",
                "passed": False,
                "severity": "medium",
                "vulnerability": "a",
            },
            {
                "question_id": "U1",
                "passed": True,
                "severity": "none",
                "vulnerability": "b",
            },
        ]
        lines = generate_markdown(entries, "v1", "2026-03-02")
        data_lines = [l for l in lines if l.startswith("| U") or l.startswith("| W")]
        self.assertEqual(len(data_lines), 2)
        self.assertTrue(data_lines[0].startswith("| U1"))
        self.assertTrue(data_lines[1].startswith("| W1"))

    def test_pass_icon(self):
        entries = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "none",
                "vulnerability": "无",
            },
            {
                "question_id": "U2",
                "passed": False,
                "severity": "high",
                "vulnerability": "问题",
            },
        ]
        lines = generate_markdown(entries, "v1", "2026-03-02")
        output = "\n".join(lines)
        # Check that passed entries get checkmark and failed get warning
        u1_line = [l for l in lines if "U1" in l and l.startswith("|")][0]
        u2_line = [l for l in lines if "U2" in l and l.startswith("|")][0]
        self.assertIn("✅", u1_line)
        self.assertIn("⚠️", u2_line)


class TestGenerateConvergence(unittest.TestCase):
    """Test generate_convergence function."""

    def test_converged_zero_high_zero_medium(self):
        entries = [
            {"severity": "none"},
            {"severity": "low"},
        ]
        lines = generate_convergence(entries)
        output = "\n".join(lines)
        self.assertIn("高严重度问题数: 0", output)
        self.assertIn("中严重度问题数: 0", output)
        self.assertIn("收敛", output)
        self.assertIn("锁定 spec", output)

    def test_converged_zero_high_three_medium(self):
        entries = [
            {"severity": "medium"},
            {"severity": "medium"},
            {"severity": "medium"},
        ]
        lines = generate_convergence(entries)
        output = "\n".join(lines)
        self.assertIn("高严重度问题数: 0", output)
        self.assertIn("中严重度问题数: 3", output)
        self.assertIn("收敛", output)
        self.assertIn("锁定 spec", output)

    def test_not_converged_with_high(self):
        entries = [
            {"severity": "high"},
            {"severity": "none"},
        ]
        lines = generate_convergence(entries)
        output = "\n".join(lines)
        self.assertIn("高严重度问题数: 1", output)
        self.assertIn("未收敛", output)
        self.assertIn("Template 04 修订", output)

    def test_not_converged_four_medium(self):
        entries = [
            {"severity": "medium"},
            {"severity": "medium"},
            {"severity": "medium"},
            {"severity": "medium"},
        ]
        lines = generate_convergence(entries)
        output = "\n".join(lines)
        self.assertIn("高严重度问题数: 0", output)
        self.assertIn("中严重度问题数: 4", output)
        self.assertIn("未收敛", output)
        self.assertIn("Template 04 修订", output)

    def test_empty_entries_converged(self):
        lines = generate_convergence([])
        output = "\n".join(lines)
        self.assertIn("高严重度问题数: 0", output)
        self.assertIn("中严重度问题数: 0", output)
        self.assertIn("收敛", output)


class TestMainCLI(unittest.TestCase):
    """Test main() CLI integration."""

    def test_valid_input_outputs_markdown(self):
        data = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "none",
                "vulnerability": "无",
            },
            {
                "question_id": "W1",
                "passed": False,
                "severity": "medium",
                "vulnerability": "问题",
            },
        ]
        filepath = _write_temp_json(data, "scorecard_v2.json")

        captured_stdout = io.StringIO()
        with patch("sys.argv", ["scorecard_parser.py", filepath]):
            with patch("sys.stdout", captured_stdout):
                result = main()

        self.assertEqual(result, ExitCode.SUCCESS)
        output = captured_stdout.getvalue()
        self.assertIn("## 压力测试漏洞记录", output)
        self.assertIn("Spec 版本: v2", output)
        self.assertIn("| U1", output)
        self.assertIn("| W1", output)

    def test_empty_array_produces_converged(self):
        filepath = _write_temp_json([], "scorecard_v1.json")

        captured_stdout = io.StringIO()
        with patch("sys.argv", ["scorecard_parser.py", filepath]):
            with patch("sys.stdout", captured_stdout):
                result = main()

        self.assertEqual(result, ExitCode.SUCCESS)
        output = captured_stdout.getvalue()
        self.assertIn("高严重度问题数: 0", output)
        self.assertIn("中严重度问题数: 0", output)
        self.assertIn("收敛", output)

    def test_file_not_found_exits_2(self):
        with patch("sys.argv", ["scorecard_parser.py", "/no/such/file.json"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, ExitCode.FILE_ERROR)

    def test_non_array_json_exits_1(self):
        filepath = _write_temp_json({"not": "array"})
        with patch("sys.argv", ["scorecard_parser.py", filepath]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, ExitCode.VALIDATION_ERROR)

    def test_missing_field_exits_1(self):
        data = [{"question_id": "U1"}]
        filepath = _write_temp_json(data)
        with patch("sys.argv", ["scorecard_parser.py", filepath]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, ExitCode.VALIDATION_ERROR)

    def test_unknown_severity_exits_1(self):
        data = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "ultra",
                "vulnerability": "无",
            }
        ]
        filepath = _write_temp_json(data)
        with patch("sys.argv", ["scorecard_parser.py", filepath]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, ExitCode.VALIDATION_ERROR)

    def test_consistency_warning_to_stderr(self):
        data = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "high",
                "vulnerability": "test",
            }
        ]
        filepath = _write_temp_json(data)

        captured_stderr = io.StringIO()
        captured_stdout = io.StringIO()
        with patch("sys.argv", ["scorecard_parser.py", filepath]):
            with patch("sys.stdout", captured_stdout):
                with patch("sys.stderr", captured_stderr):
                    result = main()

        self.assertEqual(result, ExitCode.SUCCESS)
        stderr_output = captured_stderr.getvalue()
        self.assertIn("Warning:", stderr_output)
        self.assertIn("passed=true but severity=high", stderr_output)

    def test_duplicate_warning_to_stderr(self):
        data = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "none",
                "vulnerability": "无",
            },
            {
                "question_id": "U1",
                "passed": True,
                "severity": "none",
                "vulnerability": "无",
            },
        ]
        filepath = _write_temp_json(data)

        captured_stderr = io.StringIO()
        captured_stdout = io.StringIO()
        with patch("sys.argv", ["scorecard_parser.py", filepath]):
            with patch("sys.stdout", captured_stdout):
                with patch("sys.stderr", captured_stderr):
                    result = main()

        self.assertEqual(result, ExitCode.SUCCESS)
        stderr_output = captured_stderr.getvalue()
        self.assertIn("Warning:", stderr_output)
        self.assertIn("duplicate question_id", stderr_output)

    def test_version_unknown_when_no_version_in_filename(self):
        data = [
            {
                "question_id": "U1",
                "passed": True,
                "severity": "none",
                "vulnerability": "无",
            }
        ]
        filepath = _write_temp_json(data, "results.json")

        captured_stdout = io.StringIO()
        with patch("sys.argv", ["scorecard_parser.py", filepath]):
            with patch("sys.stdout", captured_stdout):
                result = main()

        self.assertEqual(result, ExitCode.SUCCESS)
        output = captured_stdout.getvalue()
        self.assertIn("Spec 版本: unknown", output)


class TestSanitizeMarkdown(unittest.TestCase):
    """Test Markdown sanitization."""

    def test_pipe_escaped(self):
        self.assertEqual(sanitize_markdown("a | b"), "a \\| b")

    def test_newlines_replaced(self):
        self.assertEqual(sanitize_markdown("line1\nline2"), "line1 line2")

    def test_html_escaped(self):
        self.assertEqual(sanitize_markdown("<script>"), "&lt;script&gt;")

    def test_plain_text_unchanged(self):
        self.assertEqual(sanitize_markdown("无并发控制"), "无并发控制")


class TestTypeValidation(unittest.TestCase):
    """Test type validation on entry fields."""

    def test_passed_non_boolean_rejected(self):
        entry = {"question_id": "U1", "passed": "yes", "severity": "none", "vulnerability": "无"}
        errors = validate_entry(entry, 0)
        self.assertTrue(any("expected boolean" in e for e in errors))

    def test_passed_integer_rejected(self):
        entry = {"question_id": "U1", "passed": 1, "severity": "none", "vulnerability": "无"}
        errors = validate_entry(entry, 0)
        self.assertTrue(any("expected boolean" in e for e in errors))

    def test_question_id_non_string_rejected(self):
        entry = {"question_id": 42, "passed": True, "severity": "none", "vulnerability": "无"}
        errors = validate_entry(entry, 0)
        self.assertTrue(any("expected string" in e for e in errors))

    def test_vulnerability_non_string_rejected(self):
        entry = {"question_id": "U1", "passed": True, "severity": "none", "vulnerability": 123}
        errors = validate_entry(entry, 0)
        self.assertTrue(any("expected string" in e for e in errors))

    def test_valid_types_accepted(self):
        entry = {"question_id": "U1", "passed": True, "severity": "none", "vulnerability": "无"}
        errors = validate_entry(entry, 0)
        self.assertEqual(errors, [])


class TestMarkdownInjection(unittest.TestCase):
    """Test that pipe chars in vulnerability don't break table."""

    def test_pipe_in_vulnerability_escaped(self):
        entries = [
            {"question_id": "U1", "passed": True, "severity": "none", "vulnerability": "a | b"}
        ]
        lines = generate_markdown(entries, "v1", "2026-03-02")
        table_row = [l for l in lines if "U1" in l][0]
        # Should have escaped pipe, not an extra column
        self.assertIn("a \\| b", table_row)


if __name__ == "__main__":
    unittest.main()
