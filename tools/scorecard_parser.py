#!/usr/bin/env python3
"""scorecard_parser: Parse stress test scorecards into Markdown reports."""
import json
import sys
import argparse
import datetime
from pathlib import Path


class ExitCode:
    SUCCESS = 0
    VALIDATION_ERROR = 1
    FILE_ERROR = 2


VALID_SEVERITIES = frozenset({"none", "low", "medium", "high"})
REQUIRED_FIELDS = frozenset({"question_id", "passed", "severity", "vulnerability"})

# Sorting order for question ID prefixes
PREFIX_ORDER = {"U": 0, "W": 1, "D": 2}


def sort_key(entry):
    """Generate sort key: prefix order, then numeric value."""
    qid = entry["question_id"]
    prefix = ""
    num_str = ""
    for i, ch in enumerate(qid):
        if ch.isdigit():
            prefix = qid[:i]
            num_str = qid[i:]
            break
    else:
        prefix = qid
        num_str = ""

    prefix_rank = PREFIX_ORDER.get(prefix, len(PREFIX_ORDER))
    try:
        num = int(num_str) if num_str else 0
    except ValueError:
        num = 0
    return (prefix_rank, num)


def validate_entry(entry, index):
    """Validate a single scorecard entry. Returns list of errors."""
    if not isinstance(entry, dict):
        return [f"entry[{index}]: expected object, got {type(entry).__name__}"]

    errors = []

    for field in sorted(REQUIRED_FIELDS):
        if field not in entry:
            errors.append(f"entry[{index}].{field}: missing required field")

    if "severity" in entry and entry["severity"] not in VALID_SEVERITIES:
        errors.append(
            f"entry[{index}].severity: invalid value '{entry['severity']}', "
            f"expected one of: {', '.join(sorted(VALID_SEVERITIES))}"
        )

    return errors


def check_consistency_warnings(entry, index):
    """Check for passed/severity inconsistencies, return warning strings."""
    warnings = []
    passed = entry.get("passed")
    severity = entry.get("severity")

    if passed is True and severity in ("medium", "high"):
        warnings.append(
            f"entry[{index}] ({entry['question_id']}): "
            f"passed=true but severity={severity}, trusting severity for convergence"
        )
    elif passed is False and severity == "none":
        warnings.append(
            f"entry[{index}] ({entry['question_id']}): "
            f"passed=false but severity=none, trusting severity for convergence"
        )

    return warnings


def check_duplicate_warnings(entries):
    """Check for duplicate question IDs, return warning strings."""
    warnings = []
    seen = {}
    for i, entry in enumerate(entries):
        qid = entry.get("question_id", "")
        if qid in seen:
            warnings.append(
                f"duplicate question_id '{qid}' at entry[{seen[qid]}] and entry[{i}]"
            )
        else:
            seen[qid] = i
    return warnings


def extract_version(filepath):
    """Extract version from filename like scorecard_v1.json -> v1."""
    stem = Path(filepath).stem
    parts = stem.split("_")
    for part in reversed(parts):
        if part.startswith("v") and len(part) > 1 and part[1:].isdigit():
            return part
    return "unknown"


def parse_scorecard(filepath):
    """Read and validate scorecard JSON. Returns (entries, warnings) or raises SystemExit."""
    path = Path(filepath)

    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(ExitCode.FILE_ERROR)

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {filepath}: {e}", file=sys.stderr)
        sys.exit(ExitCode.VALIDATION_ERROR)

    if not isinstance(data, list):
        print(
            f"Error: expected JSON array, got {type(data).__name__}",
            file=sys.stderr,
        )
        sys.exit(ExitCode.VALIDATION_ERROR)

    all_errors = []
    all_warnings = []

    for i, entry in enumerate(data):
        all_errors.extend(validate_entry(entry, i))

    if all_errors:
        for err in all_errors:
            print(f"Validation error: {err}", file=sys.stderr)
        sys.exit(ExitCode.VALIDATION_ERROR)

    for i, entry in enumerate(data):
        all_warnings.extend(check_consistency_warnings(entry, i))

    all_warnings.extend(check_duplicate_warnings(data))

    return data, all_warnings


def generate_markdown(entries, version, date_str):
    """Generate the Markdown vulnerability table."""
    sorted_entries = sorted(entries, key=sort_key)

    lines = [
        "## 压力测试漏洞记录",
        f"日期: {date_str}",
        f"Spec 版本: {version}",
        "",
        "| 题号 | 通过 | 问题描述 | 严重程度 |",
        "|-----|------|---------|---------|",
    ]

    for entry in sorted_entries:
        icon = "✅" if entry["passed"] else "⚠️"
        lines.append(
            f"| {entry['question_id']}  | {icon} | {entry['vulnerability']} | {entry['severity']} |"
        )

    return lines


def generate_convergence(entries):
    """Generate convergence judgment lines."""
    high_count = sum(1 for e in entries if e["severity"] == "high")
    medium_count = sum(1 for e in entries if e["severity"] == "medium")

    lines = [
        "",
        f"高严重度问题数: {high_count}",
        f"中严重度问题数: {medium_count}",
        "",
        "收敛判断:",
    ]

    converged = high_count == 0 and medium_count <= 3

    if converged:
        lines.append(
            f"□ 收敛（{high_count} 高 + {medium_count} 中）→ 锁定 spec，进入 Step 5"
        )
    else:
        lines.append(
            f"□ 未收敛（{high_count} 高 + {medium_count} 中）→ 进入 Template 04 修订"
        )

    return lines


def create_parser():
    """Create the argparse parser."""
    parser = argparse.ArgumentParser(
        description="Parse stress test scorecards into Markdown vulnerability reports."
    )
    parser.add_argument(
        "scorecard",
        help="Path to scorecard JSON file (e.g., spec/scorecard_v1.json)",
    )
    return parser


def main():
    """Entry point."""
    parser = create_parser()
    args = parser.parse_args()

    entries, warnings = parse_scorecard(args.scorecard)

    for w in warnings:
        print(f"Warning: {w}", file=sys.stderr)

    version = extract_version(args.scorecard)
    date_str = datetime.date.today().isoformat()

    md_lines = generate_markdown(entries, version, date_str)
    conv_lines = generate_convergence(entries)

    output = "\n".join(md_lines + conv_lines)
    print(output)

    return ExitCode.SUCCESS


if __name__ == "__main__":
    sys.exit(main())
