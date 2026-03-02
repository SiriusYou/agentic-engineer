---
title: "feat: Batch 2 — Workflow Tooling and Protocol Additions"
type: feat
status: completed
date: 2026-03-02
---

# feat: Batch 2 — Workflow Tooling and Protocol Additions

Batch 1 fixed documentation consistency across the planning workflow templates. Batch 2 adds three missing capabilities: an automation tool, a governance protocol, and a validation template.

## Overview

| Task | Deliverable | Type |
|------|------------|------|
| #4 | `tools/scorecard_parser.py` | CLI tool (new dir + file) |
| #5 | Change Request protocol in `plan/quick_reference.md` | Documentation addition |
| #6 | `plan/template_00_postmortem.md` | Template (new file) |

All three tasks are independent and can be implemented in parallel.

---

## Task #4: Create `tools/scorecard_parser.py`

### Problem

`template_03_stress_test.md` references `tools/scorecard_parser.py` as the optional automation path, but the tool doesn't exist. Users must manually transcribe JSON scorecard data into Markdown tables.

### Acceptance Criteria

- [x] `tools/` directory created
- [x] `python tools/scorecard_parser.py spec/scorecard_v1.json` works as documented
- [x] Reads JSON array with schema: `{question_id, passed, severity, vulnerability}`
- [x] Outputs Markdown vulnerability table matching `template_03` manual table format
- [x] Outputs convergence judgment: `0 high + ≤3 medium = converged`
- [x] Prints to stdout (supports `> stress_test_v1.md` redirection)
- [x] Validates JSON structure, exits with clear error on malformed input
- [x] Stdlib only (no third-party dependencies): `json`, `sys`, `datetime`
- [x] Include a sample `tools/test_scorecard.json` for testing
- [x] Unit tests in `tools/test_scorecard_parser.py`

### Input Schema (from `template_03_stress_test.md:80-88`)

```json
[
  {"question_id": "U1", "passed": true, "severity": "none", "vulnerability": "无"},
  {"question_id": "U2", "passed": false, "severity": "high", "vulnerability": "无并发控制机制"},
  {"question_id": "W1", "passed": false, "severity": "medium", "vulnerability": "连接池未配置上限"}
]
```

### Output Format (matching `template_03_stress_test.md:111-129`)

```markdown
## 压力测试漏洞记录
日期: 2026-03-02
Spec 版本: v1 (extracted from filename)

| 题号 | 通过 | 问题描述 | 严重程度 |
|-----|------|---------|---------|
| U1  | ✅ | 无 | none |
| U2  | ⚠️ | 无并发控制机制 | high |
| W1  | ⚠️ | 连接池未配置上限 | medium |

高严重度问题数: 1
中严重度问题数: 1

收敛判断:
□ 未收敛（1 高 + 1 中）→ 进入 Template 04 修订
```

### Validation Rules (SpecFlow Gap Resolution)

| Scenario | Behavior |
|----------|----------|
| Empty array `[]` | Output empty table + "0 issues, converged" |
| Missing required field | Error with entry index + missing field name, exit 1 |
| Extra fields (e.g., `confidence`) | Ignore silently (lenient parsing) |
| Unknown severity value | Error listing valid values, exit 1 |
| Non-array JSON | Error "expected JSON array", exit 1 |
| File not found | Error with path, exit 2 |
| `passed: true` + `severity: "high"` | **Trust `severity` for convergence counting**, log warning to stderr |
| `passed: false` + `severity: "none"` | **Trust `severity` for convergence counting**, log warning to stderr |
| Duplicate question_id | Keep both entries, log warning to stderr |
| Unrecognized question_id format | Accept any string (no format validation on IDs) |

**Decision rationale**: `severity` is the authoritative field because convergence threshold is defined in terms of severity counts. `passed` is a convenience display field.

### Edge Cases

- Version extraction: parse `_vN` from filename, default to "unknown"
- Date: use current system date (`datetime.date.today()`)
- Output sorting: sort by question_id (U before W before D, numeric within prefix)
- Old Q-format IDs: not supported, only U/W/D prefix accepted in output sorting

### Implementation Notes

- Follow user's coding style: immutable patterns, functions < 50 lines, comprehensive error handling
- Use `argparse` for CLI (supports future `--output` and `--version` flag extensions)
- Exit codes: 0 = success, 1 = validation error, 2 = file error
- Warnings go to stderr, Markdown output goes to stdout (clean separation)

### Research Insights

**Best Practices (from research):**
- Use `ExitCode` constants class instead of magic numbers
- Implement recursive validation with path tracking for clear error messages (e.g., `entry[2].severity: expected string`)
- Use `pathlib.Path` for file operations
- Generate Markdown tables with calculated column widths for alignment
- Use `encoding='utf-8'` explicitly on all file operations

**Testing Pattern:**
- Use `unittest.mock.patch('sys.argv', [...])` to test CLI invocation
- Capture stdout with `io.StringIO` for output verification
- Use `tempfile.mkdtemp()` for test fixture files
- Test both valid and malformed JSON inputs
- Test exit codes match expected values for each error type

**Code Structure (single-file ~200 lines):**
```python
#!/usr/bin/env python3
"""scorecard_parser: Parse stress test scorecards into Markdown reports."""
import json, sys, argparse, datetime
from pathlib import Path

class ExitCode:
    SUCCESS = 0
    VALIDATION_ERROR = 1
    FILE_ERROR = 2

VALID_SEVERITIES = frozenset({"none", "low", "medium", "high"})
REQUIRED_FIELDS = frozenset({"question_id", "passed", "severity", "vulnerability"})

def validate_entry(entry, index): ...
def parse_scorecard(path): ...
def sort_entries(entries): ...  # U before W before D, numeric within
def generate_markdown(entries, version, date): ...
def generate_convergence(entries): ...
def create_parser(): ...
def main() -> int: ...

if __name__ == '__main__':
    sys.exit(main())
```

### Files

```
tools/
├── scorecard_parser.py        # CLI tool
├── test_scorecard.json        # Sample input for testing
└── test_scorecard_parser.py   # Unit tests
```

---

## Task #5: Add Change Request Protocol to `plan/quick_reference.md`

### Problem

The current workflow has no formal process for amending `spec_final.md` after it's locked. The only guidance is a one-line FAQ: "不要直接修改 spec_final.md，创建 spec_final_v2.md，重走 Step 3-4". This is insufficient for real-world use where locked specs regularly need amendments.

### Acceptance Criteria

- [x] New `## 变更请求流程（Change Request）` section added to `quick_reference.md`
- [x] Written in Chinese (matching existing content)
- [x] Defines: trigger conditions, versioning rules, re-testing requirements
- [x] Placed before `## Claude Code 启动命令` section (logical position)
- [x] Updates the existing FAQ answer to reference the new protocol
- [x] Consistent with convergence threshold language used elsewhere

### SpecFlow Gap Resolution: Approval & Re-testing

| Question | Decision |
|----------|----------|
| Who approves? | Solo developer: self-approve via checklist. Team: second person review. |
| Full or partial re-test? | **Full re-test** in new Gemini conversation (consistent with Template 03 isolation rule) |
| Impact on in-flight execution? | Execution pauses at current phase boundary, does not roll back committed code |
| Point of no return? | If change affects >50% of spec sections → start new project instead |
| SKILL.md awareness of spec_final_v2? | Add `spec_final_v*.md` glob pattern to SKILL.md file discovery (separate sub-task) |

### Proposed Content Structure

```markdown
## 变更请求流程（Change Request）

适用于 spec_final.md 锁定后发现需要修改的情况。

### 触发条件
| 类型 | 示例 | 严重度 |
|------|------|--------|
| Spec 逻辑漏洞 | 执行中发现接口定义冲突 | 必须走 CR |
| 外部需求变更 | 客户/产品要求新功能 | 必须走 CR |
| 遗漏问题 | 压力测试未覆盖的场景 | 必须走 CR |
| 文字勘误 | 错别字、格式问题 | 直接修正，不走 CR |

### 流程
1. 创建变更说明：一句话描述 + 影响的 Spec 章节列表
2. 评估范围：如果影响 >50% 章节，考虑重新走 Step 1
3. 复制 spec_final.md → spec_final_v2.md
4. 在 spec_final_v2.md 中修改（只改必须改的章节）
5. 全新 Gemini 对话，对完整 spec_final_v2.md 重新执行 Step 3（压力测试）
6. 满足收敛阈值（0 高 + ≤3 中）后锁定 spec_final_v2.md
7. 通知 Claude Code 切换到新版本

### 文件命名
spec_final.md → spec_final_v2.md → spec_final_v3.md
（配套产物：scorecard_final_v2.json, stress_test_final_v2.md）

### 原则
- 绝不修改已锁定的 spec_final.md
- 每次变更有明确的触发原因记录
- 修改范围最小化，只改必须改的章节
- 已提交的代码不回滚，在新版 Spec 基础上增量修改
```

### Research Insights

**Best Practices (from research):**
- Use impact assessment classification: Minor (typo/formatting) → direct fix, no CR needed; Moderate (logic in 1-2 sections) → CR with targeted re-test; Major (>50% sections affected) → restart from Step 1
- Include a one-line "变更原因" (change reason) in each CR for audit trail
- Track CRs with a simple counter in the spec directory (changelog approach)
- The existing FAQ answer should cross-reference the new protocol, not duplicate it

**Edge Case: In-flight Execution:**
- If Claude Code is mid-execution, pause at the current phase boundary
- Already-committed code is NOT rolled back — new spec version builds incrementally
- This aligns with the "atomic commit" principle: each commit is self-contained and valid

### SKILL.md Update (Sub-task)

Update `skills/SKILL.md:26` from:
```
spec.md / spec_final.md / SDD.md
```
to:
```
spec.md / spec_final.md / spec_final_v*.md / SDD.md
```

### Files

```
plan/quick_reference.md  # Modified: add new section + update FAQ reference
skills/SKILL.md          # Modified: update file discovery pattern (line 26)
```

---

## Task #6: Create Phase 0 Postmortem Template

### Problem

The planning workflow (Steps 1-5) has never been validated through real-world usage. There's no structured way to capture what worked, what didn't, and how many iterations were needed. Without this data, the workflow can't be improved.

### Acceptance Criteria

- [x] `plan/template_00_postmortem.md` created
- [x] Follows existing template conventions (4-line header block, Chinese with English terms)
- [x] Tracks: friction points, iteration counts, time per phase, convergence rounds
- [x] Includes structured output format (can be parsed later)
- [x] Covers all 5 workflow phases
- [x] Output saves to `spec/postmortem_v1.md`

### Proposed Template Structure

```markdown
# Template 00 — 项目复盘（Phase 0 Postmortem）
# 用途：完成项目后回顾规划流程的有效性，收集改进数据
# 使用对话：任意
# 新建对话：不需要

## 适用时机
- 项目完成后（推荐）
- 规划流程每执行一次后

## 复盘数据表

### 基本信息
| 字段 | 值 |
|------|---|
| 项目名 | |
| 完成日期 | |
| Spec 最终版本 | vN |

### 各阶段耗时
| 阶段 | 耗时 | 迭代次数 | 摩擦点 |
|------|------|---------|--------|
| Step 1 灵感捕获 | | 1 | |
| Step 2 SDD 生成 | | | |
| Step 3 压力测试 | | | |
| Step 4 反馈修正 | | | |
| Step 5 锁定执行 | | | |

### 收敛数据
| 指标 | 值 |
|------|---|
| 压力测试总轮数 | |
| 首轮高严重度问题数 | |
| 首轮中严重度问题数 | |
| 最终轮高严重度问题数 | 0 |
| 最终轮中严重度问题数 | |
| 变更请求次数（CR） | |
| 执行中歧义暂停次数 | |

### 开放式反馈
1. 最有价值的步骤是什么？为什么？
2. 最大的摩擦点在哪里？
3. 有哪些步骤感觉多余？
4. 如果重新来过，会跳过什么？
5. AI 输出质量如何？哪些步骤需要人工修正？
6. 对模板本身有什么修改建议？
```

### SpecFlow Gap Resolution: Template Conventions

| Question | Decision |
|----------|----------|
| Header line 3-4 (tool/conversation) | Use "任意" and "不需要" — postmortem is tool-agnostic |
| Phase 0 naming | "Phase 0" = meta-workflow evaluation phase, add comment explaining convention |
| Fill incrementally or retrospectively? | Default retrospective, but note "建议在每步完成时记录耗时" |
| Mandatory or optional? | Recommended, not mandatory — add "推荐" label |

### Research Insights

**Best Practices (from research):**
- Distinguish wall-clock time vs. active time — research shows people overestimate time-on-task by 45% (PMI 2018). Use wall-clock as default, note active time is optional
- Add "收敛速度" (convergence velocity) metric: track high/medium severity counts per iteration round to see if issues decrease
- Include "Start/Stop/Continue" framework for actionable feedback — more structured than open-ended questions
- Add an "行动项" (action items) section at the end — each feedback point must map to a concrete next step
- For solo developers, psychological safety isn't a concern, but framing questions as "the workflow's fault, not yours" encourages honest assessment (e.g., "哪个步骤的模板设计有问题？" vs. "你哪里做错了？")

### Files

```
plan/template_00_postmortem.md  # New file
```

---

## Implementation Phases

### Phase 1: Task #4 — scorecard_parser.py (Core)

1. Create `tools/` directory
2. Write `tools/test_scorecard.json` (sample data)
3. Write `tools/test_scorecard_parser.py` (TDD: tests first)
4. Write `tools/scorecard_parser.py` (implementation)
5. Run tests, verify CLI output matches expected format
6. Verify integration: `python tools/scorecard_parser.py tools/test_scorecard.json`

### Phase 2: Task #5 — Change Request Protocol (Documentation)

1. Read current `plan/quick_reference.md`
2. Add `## 变更请求流程（Change Request）` section before Claude Code launch command
3. Update existing FAQ answer to reference new section
4. Verify formatting consistency

### Phase 3: Task #6 — Postmortem Template (Documentation)

1. Create `plan/template_00_postmortem.md` following template conventions
2. Include all required sections: header block, usage steps, data tables, output path
3. Verify template numbering doesn't conflict

### Phase 4: Cross-verification

1. Grep for any remaining references to the non-existent parser tool
2. Verify `template_03` optional path command matches actual tool CLI
3. Ensure all new files follow project conventions (Chinese + English terms)

---

## Sources & References

### Internal References

- Scorecard JSON schema: `plan/template_03_stress_test.md:80-88`
- Manual table format: `plan/template_03_stress_test.md:111-129`
- Optional automation reference: `plan/template_03_stress_test.md:95-106`
- Existing FAQ on spec changes: `plan/quick_reference.md:63-64`
- Template header convention: `plan/template_01_inspiration.md:1-4`
- Convergence threshold: `plan/template_04_iteration.md:46-53`
- Tech stack (Python): `conductor/tech-stack.md`
