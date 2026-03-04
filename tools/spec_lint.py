#!/usr/bin/env python3
"""spec_lint: Lint SDD documents for structural completeness."""
import argparse
import datetime
import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------


class ExitCode:
    SUCCESS = 0
    VALIDATION_ERROR = 1
    USAGE_ERROR = 2


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class Severity(Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class Section:
    title: str
    level: int
    number: str
    line_num: int
    lines: List[str]


@dataclass
class Document:
    title: str
    header_lines: List[str]
    sections: List[Section]
    raw_lines: List[str]


@dataclass
class LintResult:
    checker: str
    severity: Severity
    line_number: int
    message: str


@dataclass
class LintReport:
    results: List[LintResult]
    file_path: str
    timestamp: str = field(default_factory=lambda: datetime.date.today().isoformat())


# ---------------------------------------------------------------------------
# DocumentParser
# ---------------------------------------------------------------------------

_SECTION_RE = re.compile(r"^##\s+(\d+)\.\s+(.+)")


def parse_document(text):
    # type: (str) -> Document
    """Parse Markdown text into a Document structure."""
    lines = text.splitlines()

    # Extract title from first '# ' line
    title = ""
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            break

    # Header: first 10 lines
    header_lines = lines[:10]

    # Walk lines for ## N. Title headers
    sections = []  # type: List[Section]
    for i, line in enumerate(lines):
        m = _SECTION_RE.match(line)
        if m:
            sections.append(Section(
                title=m.group(2).strip(),
                level=2,
                number=m.group(1),
                line_num=i + 1,
                lines=[],
            ))
        elif sections:
            sections[-1].lines.append(line)

    return Document(
        title=title,
        header_lines=header_lines,
        sections=sections,
        raw_lines=lines,
    )


# ---------------------------------------------------------------------------
# Checkers
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS = {"1", "2", "3", "4", "5", "6"}


class SectionPresenceChecker:
    name = "section_presence"

    def run(self, doc):
        # type: (Document) -> List[LintResult]
        found = {s.number for s in doc.sections}
        results = []
        for num in sorted(REQUIRED_SECTIONS):
            if num in found:
                results.append(LintResult(
                    self.name, Severity.PASS, 0,
                    "Section %s present" % num,
                ))
            else:
                results.append(LintResult(
                    self.name, Severity.FAIL, 0,
                    "Missing required section %s" % num,
                ))
        return results


_VERSION_RE = re.compile(r"^版本:\s*v\d+\.\d+")
_STATUS_RE = re.compile(r"^状态:\s*\S+")
_DATE_RE = re.compile(r"^最后更新:\s*\d{4}-\d{2}-\d{2}\s*$")


class HeaderFormatChecker:
    name = "header_format"

    FIELDS = [
        ("版本", _VERSION_RE),
        ("状态", _STATUS_RE),
        ("最后更新", _DATE_RE),
    ]

    def run(self, doc):
        # type: (Document) -> List[LintResult]
        results = []
        for field_name, pattern in self.FIELDS:
            found = False
            for line in doc.header_lines:
                if pattern.match(line):
                    found = True
                    break
            if found:
                results.append(LintResult(
                    self.name, Severity.PASS, 0,
                    "Header field '%s' present and valid" % field_name,
                ))
            else:
                results.append(LintResult(
                    self.name, Severity.FAIL, 0,
                    "Missing or invalid header field: %s" % field_name,
                ))
        return results


_TBD_RE = re.compile(
    r"(?:^|[^a-zA-Z])(TBD|TODO)(?:[^a-zA-Z]|$)|待定|待补充|未决定",
    re.IGNORECASE,
)


class TBDMarkerChecker:
    name = "tbd_marker"

    def run(self, doc):
        # type: (Document) -> List[LintResult]
        results = []
        in_code_block = False
        found_any = False

        for i, line in enumerate(doc.raw_lines, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Strip inline code before checking (backtick content = code)
            check_line = re.sub(r"`[^`]*`", "", line)
            if _TBD_RE.search(check_line):
                found_any = True
                # Extract the matched marker for the message
                m = _TBD_RE.search(line)
                marker = m.group(1) if m.group(1) else m.group(0)
                results.append(LintResult(
                    self.name, Severity.FAIL, i,
                    "TBD marker found: '%s'" % marker.strip(),
                ))

        if not found_any:
            results.append(LintResult(
                self.name, Severity.PASS, 0,
                "No TBD/TODO markers found",
            ))
        return results


_EXIT_CODE_RE = re.compile(r"\|\s*(\d+)\s*\|")
_4B_HEADER_RE = re.compile(r"^#{2,3}\s+4\.B", re.IGNORECASE)

REQUIRED_EXIT_CODES = {"0", "1", "2"}


class ExitCodeTableChecker:
    name = "exit_code_table"

    def run(self, doc):
        # type: (Document) -> List[LintResult]
        # Check if any section 4 content has 4.B header
        has_4b = False
        section4_lines = []

        for section in doc.sections:
            if section.number == "4":
                section4_lines = section.lines
                break

        if not section4_lines:
            # Also check raw lines for 4.B
            for line in doc.raw_lines:
                if _4B_HEADER_RE.match(line):
                    has_4b = True
                    break
        else:
            for line in section4_lines:
                if _4B_HEADER_RE.match(line):
                    has_4b = True
                    break
            if not has_4b:
                # Check the section title line itself
                for section in doc.sections:
                    if section.number == "4":
                        # Check raw_lines around section
                        for line in doc.raw_lines:
                            if _4B_HEADER_RE.match(line):
                                has_4b = True
                                break
                        break

        if not has_4b:
            return [LintResult(
                self.name, Severity.PASS, 0,
                "No 4.B CLI interface section found, skipping exit code check",
            )]

        # Find exit code table in section 4
        found_codes = set()
        # Search all raw lines for the exit code table
        in_section4 = False
        for line in doc.raw_lines:
            if re.match(r"^##\s+4\.\s+", line):
                in_section4 = True
                continue
            if in_section4 and re.match(r"^##\s+[^#]", line) and not re.match(r"^##\s+4", line):
                break
            if in_section4:
                for m in _EXIT_CODE_RE.finditer(line):
                    found_codes.add(m.group(1))

        results = []
        missing = REQUIRED_EXIT_CODES - found_codes
        if missing:
            results.append(LintResult(
                self.name, Severity.FAIL, 0,
                "Missing exit codes in table: %s" % ", ".join(sorted(missing)),
            ))
        else:
            results.append(LintResult(
                self.name, Severity.PASS, 0,
                "All required exit codes (0, 1, 2) present in table",
            ))
        return results


_CHECKER_BLOCK_RE = re.compile(r"^###\s+(\w+)")
_POSITIVE_RE = re.compile(r"^正例（(?:应匹配|应触发\s*PASS)）:")
_NEGATIVE_RE = re.compile(r"^反例（(?:不应匹配|应触发\s*FAIL)）:")
_NUMBERED_ITEM_RE = re.compile(r"^\s*\d+\.\s+")


class PatternExampleChecker:
    name = "pattern_example"

    def run(self, doc):
        # type: (Document) -> List[LintResult]
        # Find section 8
        section8 = None
        for section in doc.sections:
            if section.number == "8":
                section8 = section
                break

        if section8 is None:
            return []

        # Parse checker sub-blocks within section 8
        blocks = []  # list of (name, full_title, lines)
        current_name = None
        current_title = None
        current_lines = []  # type: List[str]

        for line in section8.lines:
            m = _CHECKER_BLOCK_RE.match(line)
            if m:
                if current_name is not None:
                    blocks.append((current_name, current_title, current_lines))
                current_name = m.group(1)
                current_title = line.strip().lstrip("#").strip()
                current_lines = []
            elif current_name is not None:
                current_lines.append(line)

        if current_name is not None:
            blocks.append((current_name, current_title, current_lines))

        if not blocks:
            return [LintResult(
                self.name, Severity.FAIL, section8.line_num,
                "Section 8 exists but contains no checker sub-blocks",
            )]

        results = []
        for block_name, block_title, block_lines in blocks:
            # Skip self-referential block
            if block_name == "PatternExampleChecker":
                continue

            positive_count = 0
            negative_count = 0
            in_positive = False
            in_negative = False

            for bline in block_lines:
                stripped = bline.strip()
                if _POSITIVE_RE.match(stripped):
                    in_positive = True
                    in_negative = False
                    continue
                if _NEGATIVE_RE.match(stripped):
                    in_negative = True
                    in_positive = False
                    continue
                # A new section header or empty-ish break
                if stripped.startswith("###") or stripped.startswith("检查器:") or stripped.startswith("匹配模式:"):
                    in_positive = False
                    in_negative = False
                    continue

                if _NUMBERED_ITEM_RE.match(bline):
                    if in_positive:
                        positive_count += 1
                    elif in_negative:
                        negative_count += 1

            if positive_count >= 3 and negative_count >= 3:
                results.append(LintResult(
                    self.name, Severity.PASS, section8.line_num,
                    "Checker '%s' has %d positive + %d negative examples" % (
                        block_title, positive_count, negative_count),
                ))
            else:
                parts = []
                if positive_count < 3:
                    parts.append("only %d positive examples (need 3+)" % positive_count)
                if negative_count < 3:
                    parts.append("only %d negative examples (need 3+)" % negative_count)
                results.append(LintResult(
                    self.name, Severity.FAIL, section8.line_num,
                    "Checker '%s': %s" % (block_title, ", ".join(parts)),
                ))

        return results


# ---------------------------------------------------------------------------
# Checker registry
# ---------------------------------------------------------------------------

ALL_CHECKERS = [
    SectionPresenceChecker(),
    HeaderFormatChecker(),
    TBDMarkerChecker(),
    ExitCodeTableChecker(),
    PatternExampleChecker(),
]

CHECKER_IDS = {c.name for c in ALL_CHECKERS}


def run_lints(doc, checker_names=None):
    # type: (Document, Optional[List[str]]) -> LintReport
    """Run all (or specified) checkers and return a LintReport."""
    checkers = ALL_CHECKERS
    if checker_names:
        name_set = set(checker_names)
        checkers = [c for c in ALL_CHECKERS if c.name in name_set]

    all_results = []  # type: List[LintResult]
    for checker in checkers:
        results = checker.run(doc)
        all_results.extend(results)

    return LintReport(results=all_results, file_path="")


# ---------------------------------------------------------------------------
# ReportFormatter
# ---------------------------------------------------------------------------


def format_report(report, fmt="summary", verbose=False):
    # type: (LintReport, str, bool) -> str
    """Format LintReport as string output."""
    total = len(report.results)
    passed = sum(1 for r in report.results if r.severity == Severity.PASS)
    failed = sum(1 for r in report.results if r.severity == Severity.FAIL)
    warnings = sum(1 for r in report.results if r.severity == Severity.WARNING)

    if fmt == "json":
        data = {
            "file": report.file_path,
            "timestamp": report.timestamp,
            "summary": {
                "total": total,
                "pass": passed,
                "fail": failed,
                "warning": warnings,
            },
            "results": [
                {
                    "checker": r.checker,
                    "severity": r.severity.value,
                    "line": r.line_number,
                    "message": r.message,
                }
                for r in report.results
            ],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    if fmt == "summary":
        line = "%d passed, %d failed, %d warnings" % (passed, failed, warnings)
        if verbose:
            parts = [line, ""]
            for r in report.results:
                parts.append(
                    "%s [%s] line %d: %s"
                    % (r.severity.value.upper(), r.checker, r.line_number, r.message)
                )
            return "\n".join(parts)
        return line

    # markdown
    lines = [
        "## spec-lint 检查报告",
        "文件: %s" % report.file_path,
        "日期: %s" % report.timestamp,
        "",
        "### 汇总",
        "- 检查项: %d 个" % total,
        "- 通过: %d 个" % passed,
        "- 失败: %d 个" % failed,
        "- 警告: %d 个" % warnings,
    ]

    fails = [r for r in report.results if r.severity == Severity.FAIL]
    if fails:
        lines.extend([
            "",
            "### 失败项",
            "| 检查器 | 行号 | 描述 |",
            "|--------|------|------|",
        ])
        for r in fails:
            ln = str(r.line_number) if r.line_number > 0 else "-"
            lines.append("| %s | %s | %s |" % (r.checker, ln, r.message))

    warns = [r for r in report.results if r.severity == Severity.WARNING]
    if warns:
        lines.extend([
            "",
            "### 警告项",
            "| 检查器 | 行号 | 描述 |",
            "|--------|------|------|",
        ])
        for r in warns:
            ln = str(r.line_number) if r.line_number > 0 else "-"
            lines.append("| %s | %s | %s |" % (r.checker, ln, r.message))

    if verbose:
        passes = [r for r in report.results if r.severity == Severity.PASS]
        if passes:
            lines.extend([
                "",
                "### 通过项",
                "| 检查器 | 行号 | 描述 |",
                "|--------|------|------|",
            ])
            for r in passes:
                ln = str(r.line_number) if r.line_number > 0 else "-"
                lines.append("| %s | %s | %s |" % (r.checker, ln, r.message))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def create_parser():
    parser = argparse.ArgumentParser(
        description="Lint SDD documents for structural completeness.",
    )
    parser.add_argument(
        "spec_file",
        nargs="?",
        help="SDD document path (.md file)",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        default="summary",
        choices=["summary", "json", "markdown"],
        help="Output format (default: summary)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--check",
        default=None,
        help="Only run specified checkers (comma-separated)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show all check results including passed items",
    )
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    # 1. Missing spec_file → exit 2
    if not args.spec_file:
        parser.print_usage(sys.stderr)
        sys.exit(ExitCode.USAGE_ERROR)

    # 2. Validate --check IDs before reading file
    checker_names = None  # type: Optional[List[str]]
    if args.check is not None:
        raw_names = [n.strip() for n in args.check.split(",")]
        checker_names = [n for n in raw_names if n]  # filter empty strings

        if not checker_names:
            print(
                "Error: no valid checker names provided",
                file=sys.stderr,
            )
            sys.exit(ExitCode.USAGE_ERROR)

        invalid = [n for n in checker_names if n not in CHECKER_IDS]
        if invalid:
            print(
                "Error: unknown checker: %s. Valid: %s"
                % (", ".join(invalid), ", ".join(sorted(CHECKER_IDS))),
                file=sys.stderr,
            )
            sys.exit(ExitCode.USAGE_ERROR)

        # Deduplicate
        seen = set()  # type: set
        deduped = []  # type: List[str]
        for n in checker_names:
            if n not in seen:
                seen.add(n)
                deduped.append(n)
        checker_names = deduped

    # 3. Read file
    import os
    spec_path = args.spec_file
    if not os.path.exists(spec_path):
        print(
            "Error: file not found: %s" % spec_path,
            file=sys.stderr,
        )
        sys.exit(ExitCode.USAGE_ERROR)

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            text = f.read()
    except (UnicodeDecodeError, OSError):
        print(
            "Error: cannot read file: %s" % spec_path,
            file=sys.stderr,
        )
        sys.exit(ExitCode.USAGE_ERROR)

    # 4. Empty file → single WARNING, short-circuit
    if not text.strip():
        report = LintReport(
            results=[LintResult(
                "input_validation", Severity.WARNING, 0,
                "file is empty",
            )],
            file_path=spec_path,
        )
        output = format_report(report, fmt=args.fmt, verbose=args.verbose)
        print(output)
        # stderr: WARN only
        print(
            "WARN [input_validation] %s:0: file is empty" % spec_path,
            file=sys.stderr,
        )
        if args.strict:
            sys.exit(ExitCode.VALIDATION_ERROR)
        sys.exit(ExitCode.SUCCESS)

    # 5. Parse and run checkers
    doc = parse_document(text)
    report = run_lints(doc, checker_names)
    report.file_path = spec_path

    output = format_report(report, fmt=args.fmt, verbose=args.verbose)
    print(output)

    # stderr: FAIL and WARN items only
    has_fail = False
    has_warning = False
    for r in report.results:
        loc = "%s:%d" % (spec_path, r.line_number)
        if r.severity == Severity.FAIL:
            has_fail = True
            print("FAIL [%s] %s: %s" % (r.checker, loc, r.message), file=sys.stderr)
        elif r.severity == Severity.WARNING:
            has_warning = True
            print("WARN [%s] %s: %s" % (r.checker, loc, r.message), file=sys.stderr)

    if has_fail:
        sys.exit(ExitCode.VALIDATION_ERROR)
    if has_warning and args.strict:
        sys.exit(ExitCode.VALIDATION_ERROR)
    sys.exit(ExitCode.SUCCESS)


if __name__ == "__main__":
    main()
