#!/usr/bin/env python3
"""scorecard_parser: Parse stress test scorecards into Markdown reports.

JSON output contract (--format json):
{
    "version": "v1",               # extracted from filename
    "date": "2026-03-02",          # ISO 8601
    "entries": [                    # sorted by prefix order (U→W→D), then numeric
        {"question_id": "U1", "passed": true, "severity": "none", "vulnerability": "..."}
    ],
    "summary": {
        "total": 10,
        "passed": 8,
        "failed": 2,
        "by_severity": {"high": 0, "medium": 1, "low": 1, "none": 8}
    },
    "convergence": {
        "converged": true,
        "high_count": 0,
        "medium_count": 1,
        "threshold": "0 high + <=3 medium"
    },
    "warnings": []                  # consistency/duplicate warnings
}
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path


class ExitCode:
    SUCCESS = 0
    VALIDATION_ERROR = 1
    FILE_ERROR = 2


VALID_SEVERITIES = frozenset({"none", "low", "medium", "high"})
REQUIRED_FIELDS = frozenset({"question_id", "passed", "severity", "vulnerability"})

# Sorting order for question ID prefixes
PREFIX_ORDER = {"U": 0, "W": 1, "D": 2}

# Convergence threshold: 0 high + at most this many medium = converged
MEDIUM_CONVERGENCE_THRESHOLD = 3

# Pattern to split question IDs into prefix + number (e.g., "U1" → "U", "1")
_QID_PATTERN = re.compile(r"^([A-Za-z]*)(\d*)$")


def sort_key(entry):
    """Generate sort key: prefix order, then numeric value."""
    qid = entry.get("question_id", "")
    m = _QID_PATTERN.match(qid)
    prefix, num_str = (m.group(1), m.group(2)) if m else (qid, "")
    prefix_rank = PREFIX_ORDER.get(prefix, len(PREFIX_ORDER))
    return (prefix_rank, int(num_str) if num_str else 0)


def validate_entry(entry, index):
    """Validate a single scorecard entry. Returns list of errors."""
    if not isinstance(entry, dict):
        return [f"entry[{index}]: expected object, got {type(entry).__name__}"]

    errors = []

    for field in sorted(REQUIRED_FIELDS):
        if field not in entry:
            errors.append(f"entry[{index}].{field}: missing required field")

    for field in ("question_id", "severity", "vulnerability"):
        if field in entry and not isinstance(entry[field], str):
            errors.append(
                f"entry[{index}].{field}: expected string, got {type(entry[field]).__name__}"
            )

    if "passed" in entry and not isinstance(entry["passed"], bool):
        errors.append(
            f"entry[{index}].passed: expected boolean, got {type(entry['passed']).__name__}"
        )

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
    except OSError as e:
        print(f"Error: cannot read file {filepath}: {e}", file=sys.stderr)
        sys.exit(ExitCode.FILE_ERROR)

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


def sanitize_markdown(text):
    """Escape characters that could break Markdown table structure."""
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("|", "\\|")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


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
        qid = sanitize_markdown(entry["question_id"])
        vuln = sanitize_markdown(entry["vulnerability"])
        sev = sanitize_markdown(entry["severity"])
        lines.append(f"| {qid}  | {icon} | {vuln} | {sev} |")

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

    converged = high_count == 0 and medium_count <= MEDIUM_CONVERGENCE_THRESHOLD

    if converged:
        lines.append(
            f"□ 收敛（{high_count} 高 + {medium_count} 中）→ 锁定 spec，进入 Step 5"
        )
    else:
        lines.append(
            f"□ 未收敛（{high_count} 高 + {medium_count} 中）→ 进入 Template 04 修订"
        )

    return lines


def generate_json_output(entries, version, date_str, warnings):
    """Generate structured JSON output per the contract in the module docstring."""
    sorted_entries = sorted(entries, key=sort_key)

    high_count = sum(1 for e in entries if e["severity"] == "high")
    medium_count = sum(1 for e in entries if e["severity"] == "medium")
    low_count = sum(1 for e in entries if e["severity"] == "low")
    none_count = sum(1 for e in entries if e["severity"] == "none")
    passed_count = sum(1 for e in entries if e["passed"])
    total = len(entries)

    return {
        "version": version,
        "date": date_str,
        "entries": sorted_entries,
        "summary": {
            "total": total,
            "passed": passed_count,
            "failed": total - passed_count,
            "by_severity": {
                "high": high_count,
                "medium": medium_count,
                "low": low_count,
                "none": none_count,
            },
        },
        "convergence": {
            "converged": high_count == 0
            and medium_count <= MEDIUM_CONVERGENCE_THRESHOLD,
            "high_count": high_count,
            "medium_count": medium_count,
            "threshold": "0 high + <=3 medium",
        },
        "warnings": warnings,
    }


def create_parser():
    """Create the argparse parser."""
    parser = argparse.ArgumentParser(
        description="Parse stress test scorecards into Markdown vulnerability reports."
    )
    parser.add_argument(
        "scorecard",
        help="Path to scorecard JSON file (e.g., spec/scorecard_v1.json)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        dest="output_format",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
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

    if args.output_format == "json":
        result = generate_json_output(entries, version, date_str, warnings)
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        md_lines = generate_markdown(entries, version, date_str)
        conv_lines = generate_convergence(entries)
        output = "\n".join(md_lines + conv_lines)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
                f.write("\n")
        except OSError as e:
            print(f"Error: cannot write to {args.output}: {e}", file=sys.stderr)
            return ExitCode.FILE_ERROR
    else:
        print(output)

    return ExitCode.SUCCESS


if __name__ == "__main__":
    sys.exit(main())
