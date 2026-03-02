#!/usr/bin/env python3
"""check_workflow_consistency: Lint agentic-engineer docs for cross-file consistency."""
import argparse
import datetime
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# ---------------------------------------------------------------------------
# Exit codes (aligned with scorecard_parser)
# ---------------------------------------------------------------------------


class ExitCode:
    SUCCESS = 0
    VALIDATION_ERROR = 1
    FILE_ERROR = 2


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


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
# PathResolver
# ---------------------------------------------------------------------------

MAX_PARENT_SEARCH = 5


def resolve_root(cli_root=None):
    """Resolve project root directory.

    If cli_root given, validate it. Otherwise search up from cwd (max 5 levels)
    for a directory containing both plan/ and skills/.
    """
    if cli_root is not None:
        root = Path(cli_root).resolve()
        if not root.is_dir():
            print(f"Error: project root not found: {root}", file=sys.stderr)
            sys.exit(ExitCode.FILE_ERROR)
        if not (root / "plan").is_dir() or not (root / "skills").is_dir():
            print(
                f"Error: {root} does not contain plan/ and skills/ directories",
                file=sys.stderr,
            )
            sys.exit(ExitCode.FILE_ERROR)
        return root

    current = Path.cwd().resolve()
    for _ in range(MAX_PARENT_SEARCH + 1):
        if (current / "plan").is_dir() and (current / "skills").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    print(
        "Error: project root not found (no ancestor contains plan/ and skills/)",
        file=sys.stderr,
    )
    sys.exit(ExitCode.FILE_ERROR)


# ---------------------------------------------------------------------------
# Base checker
# ---------------------------------------------------------------------------


class BaseChecker:
    name = ""

    def run(self, root):
        raise NotImplementedError

    def _read_file(self, path):
        """Read a file, return (lines, None) or (None, error_message)."""
        try:
            text = path.read_text(encoding="utf-8")
            return text.splitlines(), None
        except OSError as e:
            return None, str(e)


# ---------------------------------------------------------------------------
# FileRefChecker
# ---------------------------------------------------------------------------

# Matches: [text](path/to/file) — capture the path
_MD_LINK_RE = re.compile(r"\[(?:[^\]]*)\]\(([^)]+)\)")

# Matches: `path/to/file.ext` — must contain / and a dot-extension
_INLINE_CODE_RE = re.compile(r"`([^`]*?/[^`]*?\.[a-zA-Z0-9]+)`")


class FileRefChecker(BaseChecker):
    name = "file_ref"

    SCAN_PATTERNS = [
        "README.md",
        "plan/*.md",
        "skills/*.md",
        "conductor/*.md",
        "spec/README.md",
    ]

    def run(self, root):
        results = []
        files = self._collect_files(root)
        if not files:
            return [
                CheckResult(
                    self.name,
                    Severity.WARNING,
                    "",
                    0,
                    "No Markdown files found to scan for path references",
                )
            ]

        found_any = False
        for md_file in files:
            lines, err = self._read_file(md_file)
            if err:
                results.append(
                    CheckResult(
                        self.name,
                        Severity.WARNING,
                        str(md_file.relative_to(root)),
                        0,
                        f"Cannot read file: {err}",
                    )
                )
                continue

            refs = self._extract_refs(lines, md_file, root)
            for ref_path, line_num, is_md_link in refs:
                found_any = True
                # For Markdown links without '/', resolve relative to the file's directory
                if is_md_link and "/" not in ref_path:
                    full_path = md_file.parent / ref_path
                    display_path = str(full_path.relative_to(root))
                else:
                    full_path = root / ref_path
                    display_path = ref_path
                if not full_path.exists():
                    results.append(
                        CheckResult(
                            self.name,
                            Severity.FAIL,
                            str(md_file.relative_to(root)),
                            line_num,
                            f"Broken reference: expected {display_path} to exist, found missing",
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            self.name,
                            Severity.PASS,
                            str(md_file.relative_to(root)),
                            line_num,
                            f"Reference {display_path} exists",
                        )
                    )

        if not found_any and not results:
            results.append(
                CheckResult(
                    self.name,
                    Severity.PASS,
                    "",
                    0,
                    "No file path references found in scanned documents",
                )
            )

        return results

    def _collect_files(self, root):
        files = []
        for pattern in self.SCAN_PATTERNS:
            files.extend(sorted(root.glob(pattern)))
        return files

    def _extract_refs(self, lines, md_file, root):
        """Extract (relative_path, line_number, is_md_link) tuples from lines."""
        refs = []
        in_code_block = False

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Skip command-line examples
            if re.match(r"^\s*[$>]|^\s*(python|cat|bash|git|echo|cd)\s", stripped):
                continue

            # Markdown links: [text](path) — may be same-directory relative
            for match in _MD_LINK_RE.finditer(line):
                path = match.group(1).strip()
                # Strip anchor fragments: path/file.md#section → path/file.md
                if "#" in path:
                    path = path.split("#")[0]
                    if not path:
                        continue
                if self._is_checkable_path(path):
                    refs.append((path, i, True))

            # Inline code: `path/to/file.ext` — always relative to root
            for match in _INLINE_CODE_RE.finditer(line):
                path = match.group(1).strip()
                if self._is_checkable_path(path):
                    refs.append((path, i, False))

        return refs

    def _is_checkable_path(self, path):
        """Return True if the path should be verified on disk."""
        if path.startswith(("http://", "https://", "#")):
            return False
        if "[" in path and "]" in path:
            return False
        if path.startswith(("$", ">")):
            return False
        return True


# ---------------------------------------------------------------------------
# ConvergenceChecker
# ---------------------------------------------------------------------------

_THRESHOLD_CONST_RE = re.compile(r"MEDIUM_CONVERGENCE_THRESHOLD\s*=\s*(\d+)")
_THRESHOLD_TEXT_RE = re.compile(r"(\d+)\s*高.*?(\d+)\s*中")
_THRESHOLD_TEXT_FULL_RE = re.compile(r"(\d+)\s*高严重度.*?(\d+)\s*中严重度")


class ConvergenceChecker(BaseChecker):
    name = "convergence"

    SOURCE_FILE = "tools/scorecard_parser.py"
    CHECK_FILES = [
        ("plan/quick_reference.md", _THRESHOLD_TEXT_RE),
        ("skills/planning-workflow.md", _THRESHOLD_TEXT_FULL_RE),
        ("skills/stress-test-prompts.md", _THRESHOLD_TEXT_RE),
    ]

    def run(self, root):
        results = []

        # Extract baseline from scorecard_parser.py
        source_path = root / self.SOURCE_FILE
        if not source_path.exists():
            return [
                CheckResult(
                    self.name,
                    Severity.FAIL,
                    self.SOURCE_FILE,
                    0,
                    "Convergence threshold source file missing: expected tools/scorecard_parser.py to exist",
                )
            ]

        lines, err = self._read_file(source_path)
        if err:
            return [
                CheckResult(
                    self.name,
                    Severity.FAIL,
                    self.SOURCE_FILE,
                    0,
                    f"Cannot read source file: {err}",
                )
            ]

        baseline = None
        baseline_line = 0
        for i, line in enumerate(lines, 1):
            m = _THRESHOLD_CONST_RE.search(line)
            if m:
                baseline = int(m.group(1))
                baseline_line = i
                break

        if baseline is None:
            return [
                CheckResult(
                    self.name,
                    Severity.FAIL,
                    self.SOURCE_FILE,
                    0,
                    "Cannot extract MEDIUM_CONVERGENCE_THRESHOLD from scorecard_parser.py",
                )
            ]

        results.append(
            CheckResult(
                self.name,
                Severity.PASS,
                self.SOURCE_FILE,
                baseline_line,
                f"Baseline convergence threshold extracted: {baseline}",
            )
        )

        # Check each documentation file
        for rel_path, pattern in self.CHECK_FILES:
            file_path = root / rel_path
            if not file_path.exists():
                results.append(
                    CheckResult(
                        self.name,
                        Severity.FAIL,
                        rel_path,
                        0,
                        f"Convergence threshold reference file missing: expected {rel_path} to exist",
                    )
                )
                continue

            doc_lines, err = self._read_file(file_path)
            if err:
                results.append(
                    CheckResult(
                        self.name,
                        Severity.WARNING,
                        rel_path,
                        0,
                        f"Cannot read file: {err}",
                    )
                )
                continue

            found = False
            for j, doc_line in enumerate(doc_lines, 1):
                m = pattern.search(doc_line)
                if m:
                    high_val = int(m.group(1))
                    medium_val = int(m.group(2))
                    found = True

                    if medium_val != baseline:
                        results.append(
                            CheckResult(
                                self.name,
                                Severity.FAIL,
                                rel_path,
                                j,
                                f"Convergence threshold mismatch: expected medium={baseline}, found medium={medium_val}",
                            )
                        )
                    elif high_val != 0:
                        results.append(
                            CheckResult(
                                self.name,
                                Severity.FAIL,
                                rel_path,
                                j,
                                f"Convergence threshold mismatch: expected high=0, found high={high_val}",
                            )
                        )
                    else:
                        results.append(
                            CheckResult(
                                self.name,
                                Severity.PASS,
                                rel_path,
                                j,
                                f"Convergence threshold consistent (0 high + {medium_val} medium)",
                            )
                        )
                    break

            if not found:
                results.append(
                    CheckResult(
                        self.name,
                        Severity.WARNING,
                        rel_path,
                        0,
                        f"Cannot extract convergence threshold from {rel_path}",
                    )
                )

        return results


# ---------------------------------------------------------------------------
# StepNamingChecker
# ---------------------------------------------------------------------------

STEP_NAMES = {
    "1": ("灵感捕获", {"灵感整理"}),
    "2": ("SDD 生成", {"SDD生成", "AI 结构化"}),
    "3": ("压力测试", {"对抗性压测", "压测"}),
    "4": ("反馈修正", {"迭代修正", "修订"}),
    "5": ("锁定执行", {"执行", "移交执行"}),
}

PHASE_NAMES = {
    "0": ("复盘", {"项目复盘", "postmortem"}),
}

# Only match lines where "Step N" is a label/definition, not a prose reference.
# Requires Step N to be followed by a CJK name or known keyword, separated by colon/space.
_STEP_RE = re.compile(r"Step\s+([1-5])\s*[：:]\s*(.+?)(?=[，。、|\n]|$)")
_PHASE_RE = re.compile(r"Phase\s+([0-9])\s*[：:]\s*(.+?)(?=[，。、|\n]|$)")


class StepNamingChecker(BaseChecker):
    name = "step_naming"

    SCAN_FILES = [
        "README.md",
        "plan/quick_reference.md",
        "skills/planning-workflow.md",
        "skills/SKILL.md",
    ]

    def run(self, root):
        results = []
        any_checked = False

        for rel_path in self.SCAN_FILES:
            file_path = root / rel_path
            if not file_path.exists():
                results.append(
                    CheckResult(
                        self.name,
                        Severity.WARNING,
                        rel_path,
                        0,
                        f"File not found, skipping step naming check: {rel_path}",
                    )
                )
                continue

            lines, err = self._read_file(file_path)
            if err:
                results.append(
                    CheckResult(
                        self.name,
                        Severity.WARNING,
                        rel_path,
                        0,
                        f"Cannot read file: {err}",
                    )
                )
                continue

            in_code_block = False
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    continue

                # Skip table rows and Q&A prose
                if "|" in stripped and stripped.startswith("|"):
                    continue
                if stripped.startswith("**Q:") or stripped.startswith("→"):
                    continue

                # Check Step N patterns
                for m in _STEP_RE.finditer(line):
                    any_checked = True
                    step_num = m.group(1)
                    found_name = m.group(2).strip()
                    canonical, aliases = STEP_NAMES.get(step_num, (None, set()))
                    if canonical is None:
                        continue
                    all_valid = {canonical} | aliases
                    if not any(found_name.startswith(valid) for valid in all_valid):
                        results.append(
                            CheckResult(
                                self.name,
                                Severity.FAIL,
                                rel_path,
                                i,
                                f"Step {step_num} naming: expected '{canonical}' (or aliases), found '{found_name}'",
                            )
                        )
                    else:
                        results.append(
                            CheckResult(
                                self.name,
                                Severity.PASS,
                                rel_path,
                                i,
                                f"Step {step_num} naming consistent: '{found_name}'",
                            )
                        )

                # Check Phase N patterns
                for m in _PHASE_RE.finditer(line):
                    any_checked = True
                    phase_num = m.group(1)
                    found_name = m.group(2).strip()
                    canonical, aliases = PHASE_NAMES.get(phase_num, (None, set()))
                    if canonical is None:
                        continue
                    all_valid = {canonical} | aliases
                    if not any(found_name.startswith(valid) for valid in all_valid):
                        results.append(
                            CheckResult(
                                self.name,
                                Severity.FAIL,
                                rel_path,
                                i,
                                f"Phase {phase_num} naming: expected '{canonical}' (or aliases), found '{found_name}'",
                            )
                        )
                    else:
                        results.append(
                            CheckResult(
                                self.name,
                                Severity.PASS,
                                rel_path,
                                i,
                                f"Phase {phase_num} naming consistent: '{found_name}'",
                            )
                        )

        if not any_checked and not results:
            results.append(
                CheckResult(
                    self.name,
                    Severity.PASS,
                    "",
                    0,
                    "No Step/Phase naming patterns found in scanned documents",
                )
            )

        return (
            results
            if results
            else [
                CheckResult(
                    self.name,
                    Severity.PASS,
                    "",
                    0,
                    "Step and Phase naming check completed",
                )
            ]
        )


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
]


class SpecNamingChecker(BaseChecker):
    name = "spec_naming"

    def run(self, root):
        spec_dir = root / "spec"

        if not spec_dir.is_dir():
            return [
                CheckResult(
                    self.name,
                    Severity.WARNING,
                    "spec/",
                    0,
                    "spec/ directory does not exist",
                )
            ]

        files = [f for f in sorted(spec_dir.iterdir()) if f.is_file()]
        if not files:
            return [
                CheckResult(
                    self.name,
                    Severity.PASS,
                    "spec/",
                    0,
                    "spec/ directory is empty, no files to check",
                )
            ]

        results = []
        for f in files:
            name = f.name
            if any(p.match(name) for p in _SPEC_NAME_PATTERNS):
                results.append(
                    CheckResult(
                        self.name,
                        Severity.PASS,
                        f"spec/{name}",
                        0,
                        f"File name '{name}' matches naming convention",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        self.name,
                        Severity.WARNING,
                        f"spec/{name}",
                        0,
                        f"File name '{name}' does not match any known spec naming pattern",
                    )
                )

        return results


# ---------------------------------------------------------------------------
# TrackStatusChecker
# ---------------------------------------------------------------------------

VALID_TRACK_STATUSES = frozenset({"pending", "active", "completed"})


class TrackStatusChecker(BaseChecker):
    name = "track_status"

    FILE = "conductor/tracks.md"

    def run(self, root):
        file_path = root / self.FILE
        if not file_path.exists():
            return [
                CheckResult(
                    self.name,
                    Severity.FAIL,
                    self.FILE,
                    0,
                    "Track registry file missing: expected conductor/tracks.md to exist",
                )
            ]

        lines, err = self._read_file(file_path)
        if err:
            return [
                CheckResult(
                    self.name,
                    Severity.FAIL,
                    self.FILE,
                    0,
                    f"Cannot read file: {err}",
                )
            ]

        results = []
        table_rows = self._parse_table(lines)

        if table_rows is None:
            return [
                CheckResult(
                    self.name,
                    Severity.FAIL,
                    self.FILE,
                    0,
                    "No track registry table found in tracks.md",
                )
            ]

        if not table_rows:
            return [
                CheckResult(
                    self.name,
                    Severity.PASS,
                    self.FILE,
                    0,
                    "No registered tracks in table",
                )
            ]

        for status, track_id, line_num in table_rows:
            status_lower = status.strip().lower()
            if status_lower not in VALID_TRACK_STATUSES:
                results.append(
                    CheckResult(
                        self.name,
                        Severity.FAIL,
                        self.FILE,
                        line_num,
                        f"Invalid track status: expected one of {sorted(VALID_TRACK_STATUSES)}, found '{status}'",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        self.name,
                        Severity.PASS,
                        self.FILE,
                        line_num,
                        f"Track {track_id} status '{status_lower}' is valid",
                    )
                )

            # Check detail section consistency
            detail_status, detail_line = self._find_detail_status(lines, track_id)
            if detail_status is None:
                results.append(
                    CheckResult(
                        self.name,
                        Severity.WARNING,
                        self.FILE,
                        0,
                        f"Track {track_id}: no detail status line found (expected **状态：** ...)",
                    )
                )
            elif detail_status.lower() != status_lower:
                results.append(
                    CheckResult(
                        self.name,
                        Severity.FAIL,
                        self.FILE,
                        detail_line,
                        f"Track {track_id} status inconsistency: table says '{status_lower}', "
                        f"detail says '{detail_status}'",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        self.name,
                        Severity.PASS,
                        self.FILE,
                        detail_line,
                        f"Track {track_id} table/detail status consistent: '{status_lower}'",
                    )
                )

        return results

    def _parse_table(self, lines):
        """Parse markdown table, find Status column by header. Returns list of (status, track_id, line_num) or None."""
        status_col = None
        track_id_col = None
        header_found = False
        rows = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if "|" not in stripped:
                if header_found:
                    continue
                continue

            cells = [c.strip() for c in stripped.split("|")]
            # Remove empty first/last from leading/trailing |
            if cells and cells[0] == "":
                cells = cells[1:]
            if cells and cells[-1] == "":
                cells = cells[:-1]

            if not header_found:
                # Look for header row
                for idx, cell in enumerate(cells):
                    if cell.lower() == "status":
                        status_col = idx
                    if "track" in cell.lower() and "id" in cell.lower():
                        track_id_col = idx
                if status_col is not None:
                    header_found = True
                continue

            # Skip separator row
            if all(c.replace("-", "").replace(" ", "") == "" for c in cells):
                continue

            if not cells:
                continue

            status_val = cells[status_col] if status_col < len(cells) else ""
            track_id_val = (
                cells[track_id_col]
                if track_id_col is not None and track_id_col < len(cells)
                else ""
            )
            rows.append((status_val, track_id_val, i + 1))

        return rows if header_found else None

    def _find_detail_status(self, lines, track_id):
        """Find the **状态：** line in the detail section for a track."""
        _status_re = re.compile(r"\*\*状态[：:]\*\*\s*(.+?)(?:\s*[—\-]|$)")
        in_section = False

        for i, line in enumerate(lines):
            if track_id and track_id in line and line.strip().startswith("#"):
                in_section = True
                continue
            if in_section:
                if line.strip().startswith("#") and track_id not in line:
                    break
                m = _status_re.search(line)
                if m:
                    return m.group(1).strip(), i + 1

        return None, 0


# ---------------------------------------------------------------------------
# QuestionIdChecker
# ---------------------------------------------------------------------------

_QUESTION_ID_RE = re.compile(r"\*\*([A-Z]\d+)\.\s")

EXPECTED_IDS = (
    [f"U{i}" for i in range(1, 11)]
    + [f"W{i}" for i in range(1, 6)]
    + [f"D{i}" for i in range(1, 6)]
)


class QuestionIdChecker(BaseChecker):
    name = "question_id"

    FILE = "skills/stress-test-prompts.md"

    def run(self, root):
        file_path = root / self.FILE
        if not file_path.exists():
            return [
                CheckResult(
                    self.name,
                    Severity.WARNING,
                    self.FILE,
                    0,
                    "stress-test-prompts.md missing, skipping question ID check",
                )
            ]

        lines, err = self._read_file(file_path)
        if err:
            return [
                CheckResult(
                    self.name,
                    Severity.WARNING,
                    self.FILE,
                    0,
                    f"Cannot read file: {err}",
                )
            ]

        found_ids = []
        for i, line in enumerate(lines, 1):
            for m in _QUESTION_ID_RE.finditer(line):
                found_ids.append((m.group(1), i))

        found_id_set = {qid for qid, _ in found_ids}
        expected_set = set(EXPECTED_IDS)

        results = []

        # Check for missing IDs
        missing = expected_set - found_id_set
        if missing:
            results.append(
                CheckResult(
                    self.name,
                    Severity.FAIL,
                    self.FILE,
                    0,
                    f"Missing question IDs: expected {sorted(missing)}, found absent",
                )
            )

        # Check for unexpected IDs
        extra = found_id_set - expected_set
        if extra:
            results.append(
                CheckResult(
                    self.name,
                    Severity.WARNING,
                    self.FILE,
                    0,
                    f"Unexpected question IDs found: {sorted(extra)}",
                )
            )

        # Check total count matches mapping table
        # The mapping table should have exactly 20 rows
        mapping_count = 0
        in_mapping = False
        for line in lines:
            if "新编号" in line and "旧编号" in line:
                in_mapping = True
                continue
            if in_mapping:
                if line.strip().startswith("|") and not line.strip().startswith("|--"):
                    cells = [c.strip() for c in line.strip().split("|") if c.strip()]
                    if cells and re.match(r"[A-Z]\d+", cells[0]):
                        mapping_count += 1
                elif not line.strip().startswith("|"):
                    in_mapping = False

        if mapping_count != len(EXPECTED_IDS):
            results.append(
                CheckResult(
                    self.name,
                    Severity.FAIL,
                    self.FILE,
                    0,
                    f"Mapping table row count: expected {len(EXPECTED_IDS)}, found {mapping_count}",
                )
            )
        else:
            results.append(
                CheckResult(
                    self.name,
                    Severity.PASS,
                    self.FILE,
                    0,
                    f"Mapping table has correct row count: {mapping_count}",
                )
            )

        if not missing and not extra:
            results.append(
                CheckResult(
                    self.name,
                    Severity.PASS,
                    self.FILE,
                    0,
                    f"All {len(EXPECTED_IDS)} question IDs present and complete",
                )
            )

        return results


# ---------------------------------------------------------------------------
# CheckRunner
# ---------------------------------------------------------------------------

ALL_CHECKERS = [
    FileRefChecker(),
    ConvergenceChecker(),
    StepNamingChecker(),
    SpecNamingChecker(),
    TrackStatusChecker(),
    QuestionIdChecker(),
]


def run_checks(root, checker_names=None):
    """Run all (or filtered) checkers and return a CheckReport."""
    checkers = ALL_CHECKERS
    if checker_names:
        name_set = set(checker_names)
        checkers = [c for c in ALL_CHECKERS if c.name in name_set]

    all_results = []
    for checker in checkers:
        try:
            results = checker.run(root)
            all_results.extend(results)
        except Exception as e:
            all_results.append(
                CheckResult(
                    checker.name,
                    Severity.WARNING,
                    "",
                    0,
                    f"Checker {checker.name} raised unexpected error: {e}",
                )
            )

    return CheckReport(results=all_results)


# ---------------------------------------------------------------------------
# ReportFormatter
# ---------------------------------------------------------------------------


def format_report(report, fmt="markdown", verbose=False):
    """Format CheckReport as string."""
    total = len(report.results)
    passed = sum(1 for r in report.results if r.severity == Severity.PASS)
    failed = sum(1 for r in report.results if r.severity == Severity.FAIL)
    warnings = sum(1 for r in report.results if r.severity == Severity.WARNING)

    if fmt == "summary":
        return f"{passed} passed, {failed} failed, {warnings} warnings"

    lines = [
        "## 文档一致性检查报告",
        f"日期: {report.timestamp}",
        "",
        "### 汇总",
        f"- 检查项: {total} 个",
        f"- 通过: {passed} 个",
        f"- 失败: {failed} 个",
        f"- 警告: {warnings} 个",
    ]

    # Failed items
    fails = [r for r in report.results if r.severity == Severity.FAIL]
    if fails:
        lines.extend(
            [
                "",
                "### 失败项",
                "| 检查器 | 文件 | 行号 | 描述 |",
                "|--------|------|------|------|",
            ]
        )
        for r in fails:
            ln = str(r.line_number) if r.line_number > 0 else "-"
            lines.append(f"| {r.checker} | {r.file_path} | {ln} | {r.message} |")

    # Warning items
    warns = [r for r in report.results if r.severity == Severity.WARNING]
    if warns:
        lines.extend(
            [
                "",
                "### 警告项",
                "| 检查器 | 文件 | 描述 |",
                "|--------|------|------|",
            ]
        )
        for r in warns:
            lines.append(f"| {r.checker} | {r.file_path} | {r.message} |")

    # Verbose: show passed items too
    if verbose:
        passes = [r for r in report.results if r.severity == Severity.PASS]
        if passes:
            lines.extend(
                [
                    "",
                    "### 通过项",
                    "| 检查器 | 文件 | 行号 | 描述 |",
                    "|--------|------|------|------|",
                ]
            )
            for r in passes:
                ln = str(r.line_number) if r.line_number > 0 else "-"
                lines.append(f"| {r.checker} | {r.file_path} | {ln} | {r.message} |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def create_parser():
    parser = argparse.ArgumentParser(
        description="Check agentic-engineer documentation for cross-file consistency.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Project root directory (default: auto-detect)",
    )
    parser.add_argument(
        "--check",
        default=None,
        help="Only run specified checkers, comma-separated "
        "(file_ref,convergence,step_naming,spec_naming,track_status,question_id)",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        default="markdown",
        choices=["markdown", "summary"],
        help="Output format (default: markdown)",
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

    root = resolve_root(args.root)

    checker_names = None
    if args.check:
        checker_names = [n.strip() for n in args.check.split(",")]
        valid_names = {c.name for c in ALL_CHECKERS}
        invalid = [n for n in checker_names if n not in valid_names]
        if invalid:
            print(
                f"Error: unknown checker(s): {', '.join(invalid)}. "
                f"Valid checkers: {', '.join(sorted(valid_names))}",
                file=sys.stderr,
            )
            sys.exit(ExitCode.FILE_ERROR)

    report = run_checks(root, checker_names)

    output = format_report(report, fmt=args.fmt, verbose=args.verbose)
    print(output)

    # Write warnings and failures to stderr (per CLI contract: report→stdout, diagnostics→stderr)
    has_fail = False
    for r in report.results:
        loc = (
            f"{r.file_path}:{r.line_number}"
            if r.file_path and r.line_number > 0
            else (r.file_path or "(global)")
        )
        if r.severity == Severity.FAIL:
            has_fail = True
            print(f"FAIL [{r.checker}] {loc}: {r.message}", file=sys.stderr)
        elif r.severity == Severity.WARNING:
            print(f"WARN [{r.checker}] {loc}: {r.message}", file=sys.stderr)

    return ExitCode.VALIDATION_ERROR if has_fail else ExitCode.SUCCESS


if __name__ == "__main__":
    sys.exit(main())
