#!/usr/bin/env python3
"""check_consistency: Validate spec directory naming and cross-file references.

Part of the spec-driven-dev methodology.
Pure Python stdlib — no external dependencies required.

Simplified from the full agentic-engineer check_workflow_consistency.py
to work in any project using the spec-driven-dev workflow.

Checks:
- file_ref: Verify that Markdown file references point to existing files
- spec_naming: Validate spec/ directory file naming conventions

Exit codes:
  0 = all checks pass
  1 = validation failures found
  2 = file/usage error
"""
import argparse
import datetime
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ExitCode:
    SUCCESS = 0
    VALIDATION_ERROR = 1
    FILE_ERROR = 2


class Severity(Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class CheckResult:
    checker: str
    severity: Severity
    file_path: str
    line_number: int
    message: str


@dataclass
class CheckReport:
    results: list
    timestamp: str = field(default_factory=lambda: datetime.date.today().isoformat())


# ---------------------------------------------------------------------------
# Root resolution
# ---------------------------------------------------------------------------

MAX_PARENT_SEARCH = 5


def resolve_root(cli_root=None):
    """Resolve project root directory.

    If cli_root given, validate it. Otherwise search up from cwd (max 5 levels)
    for a directory containing spec/.
    """
    if cli_root is not None:
        root = Path(cli_root).resolve()
        if not root.is_dir():
            print(f"Error: directory not found: {root}", file=sys.stderr)
            sys.exit(ExitCode.FILE_ERROR)
        return root

    current = Path.cwd().resolve()
    for _ in range(MAX_PARENT_SEARCH + 1):
        if (current / "spec").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Fall back to cwd
    return Path.cwd().resolve()


# ---------------------------------------------------------------------------
# FileRefChecker
# ---------------------------------------------------------------------------

_MD_LINK_RE = re.compile(r"\[(?:[^\]]*)\]\(([^)]+)\)")
_INLINE_CODE_RE = re.compile(r"`([^`]*?/[^`]*?\.[a-zA-Z0-9]+)`")


class FileRefChecker:
    name = "file_ref"

    def run(self, root):
        results = []
        md_files = sorted(root.glob("**/*.md"))
        # Limit to reasonable scope (skip node_modules, .git, etc.)
        md_files = [
            f for f in md_files
            if not any(part.startswith(".") or part == "node_modules"
                       for part in f.relative_to(root).parts)
        ]

        if not md_files:
            return [CheckResult(
                self.name, Severity.PASS, "", 0,
                "No Markdown files found to scan",
            )]

        found_any = False
        for md_file in md_files:
            try:
                lines = md_file.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue

            in_code_block = False
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    continue
                if re.match(r"^\s*[$>]|^\s*(python|cat|bash|git|echo|cd)\s", stripped):
                    continue

                for match in _MD_LINK_RE.finditer(line):
                    path = match.group(1).strip()
                    if "#" in path:
                        path = path.split("#")[0]
                        if not path:
                            continue
                    if not self._is_checkable(path):
                        continue

                    found_any = True
                    if "/" not in path:
                        full_path = md_file.parent / path
                    else:
                        full_path = root / path
                    display = str(full_path.relative_to(root)) if full_path.is_relative_to(root) else path

                    if not full_path.exists():
                        results.append(CheckResult(
                            self.name, Severity.FAIL,
                            str(md_file.relative_to(root)), i,
                            f"Broken reference: {display}",
                        ))
                    else:
                        results.append(CheckResult(
                            self.name, Severity.PASS,
                            str(md_file.relative_to(root)), i,
                            f"Reference OK: {display}",
                        ))

        if not found_any and not results:
            results.append(CheckResult(
                self.name, Severity.PASS, "", 0,
                "No file path references found",
            ))

        return results

    def _is_checkable(self, path):
        if path.startswith(("http://", "https://", "#")):
            return False
        if "[" in path and "]" in path:
            return False
        if path.startswith(("$", ">")):
            return False
        return True


# ---------------------------------------------------------------------------
# SpecNamingChecker
# ---------------------------------------------------------------------------

_SPEC_NAME_PATTERNS = [
    re.compile(r"^raw_requirements\.md$"),
    re.compile(r"^spec_v\d+\.md$"),
    re.compile(r"^scorecard_v\d+\.json$"),
    re.compile(r"^stress_test_v\d+\.md$"),
    re.compile(r"^spec_final\.md$"),
    re.compile(r"^spec_final_v\d+\.md$"),
    re.compile(r"^scorecard_final_v\d+\.json$"),
    re.compile(r"^stress_test_final_v\d+\.md$"),
    re.compile(r"^postmortem_v\d+\.md$"),
    re.compile(r"^README\.md$"),
    re.compile(r"^behavior_inventory\.md$"),
]


class SpecNamingChecker:
    name = "spec_naming"

    def run(self, root):
        spec_dir = root / "spec"

        if not spec_dir.is_dir():
            return [CheckResult(
                self.name, Severity.WARNING, "spec/", 0,
                "spec/ directory does not exist",
            )]

        results = self._check_directory(spec_dir, root)

        if not results:
            return [CheckResult(
                self.name, Severity.PASS, "spec/", 0,
                "spec/ directory is empty",
            )]

        return results

    def _check_directory(self, directory, root):
        results = []
        for entry in sorted(directory.iterdir()):
            if entry.is_dir():
                results.extend(self._check_directory(entry, root))
            elif entry.is_file():
                name = entry.name
                rel_path = str(entry.relative_to(root))
                is_valid = any(p.match(name) for p in _SPEC_NAME_PATTERNS)
                severity = Severity.PASS if is_valid else Severity.WARNING
                message = (
                    f"File '{name}' matches naming convention"
                    if is_valid
                    else f"File '{name}' does not match spec naming pattern"
                )
                results.append(CheckResult(self.name, severity, rel_path, 0, message))
        return results


# ---------------------------------------------------------------------------
# Runner and Formatter
# ---------------------------------------------------------------------------

ALL_CHECKERS = [
    FileRefChecker(),
    SpecNamingChecker(),
]


def run_checks(root, checker_names=None):
    checkers = ALL_CHECKERS
    if checker_names:
        name_set = set(checker_names)
        checkers = [c for c in ALL_CHECKERS if c.name in name_set]

    all_results = []
    for checker in checkers:
        try:
            all_results.extend(checker.run(root))
        except Exception as e:
            all_results.append(CheckResult(
                checker.name, Severity.WARNING, "", 0,
                f"Checker error: {e}",
            ))

    return CheckReport(results=all_results)


def format_report(report, fmt="markdown", verbose=False):
    total = len(report.results)
    passed = sum(1 for r in report.results if r.severity == Severity.PASS)
    failed = sum(1 for r in report.results if r.severity == Severity.FAIL)
    warnings = sum(1 for r in report.results if r.severity == Severity.WARNING)

    if fmt == "summary":
        return f"{passed} passed, {failed} failed, {warnings} warnings"

    lines = [
        "## Consistency Check Report",
        f"Date: {report.timestamp}",
        "",
        "### Summary",
        f"- Checks: {total}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Warnings: {warnings}",
    ]

    fails = [r for r in report.results if r.severity == Severity.FAIL]
    if fails:
        lines.extend(["", "### Failures", "| Checker | File | Line | Description |",
                       "|---------|------|------|-------------|"])
        for r in fails:
            ln = str(r.line_number) if r.line_number > 0 else "-"
            lines.append(f"| {r.checker} | {r.file_path} | {ln} | {r.message} |")

    warns = [r for r in report.results if r.severity == Severity.WARNING]
    if warns:
        lines.extend(["", "### Warnings", "| Checker | File | Description |",
                       "|---------|------|-------------|"])
        for r in warns:
            lines.append(f"| {r.checker} | {r.file_path} | {r.message} |")

    if verbose:
        passes = [r for r in report.results if r.severity == Severity.PASS]
        if passes:
            lines.extend(["", "### Passed", "| Checker | File | Line | Description |",
                           "|---------|------|------|-------------|"])
            for r in passes:
                ln = str(r.line_number) if r.line_number > 0 else "-"
                lines.append(f"| {r.checker} | {r.file_path} | {ln} | {r.message} |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Check spec directory naming and cross-file references.",
    )
    parser.add_argument(
        "--root", default=None,
        help="Project root directory (default: auto-detect via spec/)",
    )
    parser.add_argument(
        "--check", default=None,
        help="Only run specified checkers, comma-separated (file_ref, spec_naming)",
    )
    parser.add_argument(
        "--format", dest="fmt", default="markdown",
        choices=["markdown", "summary"],
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show all results including passed items",
    )
    args = parser.parse_args()

    root = resolve_root(args.root)

    checker_names = None
    if args.check:
        checker_names = [n.strip() for n in args.check.split(",")]
        valid_names = {c.name for c in ALL_CHECKERS}
        invalid = [n for n in checker_names if n not in valid_names]
        if invalid:
            print(
                f"Error: unknown checker(s): {', '.join(invalid)}. "
                f"Valid: {', '.join(sorted(valid_names))}",
                file=sys.stderr,
            )
            sys.exit(ExitCode.FILE_ERROR)

    report = run_checks(root, checker_names)
    output = format_report(report, fmt=args.fmt, verbose=args.verbose)
    print(output)

    has_fail = False
    for r in report.results:
        loc = (f"{r.file_path}:{r.line_number}"
               if r.file_path and r.line_number > 0
               else (r.file_path or "(global)"))
        if r.severity == Severity.FAIL:
            has_fail = True
            print(f"FAIL [{r.checker}] {loc}: {r.message}", file=sys.stderr)
        elif r.severity == Severity.WARNING:
            print(f"WARN [{r.checker}] {loc}: {r.message}", file=sys.stderr)

    return ExitCode.VALIDATION_ERROR if has_fail else ExitCode.SUCCESS


if __name__ == "__main__":
    sys.exit(main())
