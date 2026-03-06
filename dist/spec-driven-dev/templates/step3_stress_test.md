# Template 03 — Adversarial Stress Test (对抗性压力测试)
# Purpose: Use layered adversarial questions (5-20 questions, assembled by project type) to find design flaws in the SDD
# Conversation: Gemini (must be a brand new conversation, completely isolated from the SDD-writing conversation)
# New conversation required: Yes — this is a hard requirement

---

## Why a New Conversation Is Required

The AI that wrote the SDD has "attachment" to its own design and will tend to defend flaws.
A fresh conversation has no baggage and can find issues more objectively.

---

## Steps

1. **Start a new** Gemini conversation (close the previous window)
2. Determine the question set based on project type (see the project type selection table in `references/stress-test-prompts.md`)
3. Paste the "Context Setup Prompt" first
4. Then paste the questions for the corresponding layers one by one (can batch or submit individually)
5. Collect the structured Scorecard and generate the vulnerability log (see Step 3: manual by default, automation optional)

---

## Step 1: Context Setup Prompt

```
I have a Software Design Document (SDD) that I need you to rigorously review in an adversarial manner.
Your role is "the nitpicky architect" — your goal is to find design flaws, risks, and unconsidered scenarios.
No need to be polite. No need to acknowledge strengths. Only find problems.

Here is the full SDD:

[Paste full content of spec_v1.md here]

---

Document loaded. I will ask you questions one by one — please answer with reference to this specific design document.

Answer format requirements:
1. First provide a detailed natural-language analysis of the issue (keep your reasoning visible)
2. End every answer with a structured JSON verdict in this format:

```json
{"question_id": "U1", "passed": true, "severity": "none", "vulnerability": "none"}
```

- passed: true means the design adequately covers this scenario, or the scenario is not applicable to this project (`severity: "n/a"`); false means a vulnerability exists
- severity: "none" (passed) / "low" / "medium" / "high" / "n/a" (not applicable)
- vulnerability: one sentence describing the issue found (write "none" when passed)

Strictly follow this format — every answer must end with this JSON line.
```

---

## Step 2: Questions by Project Type

Select the questions for the corresponding layers from `references/stress-test-prompts.md` and submit them one by one.

### Project Type Quick Reference

| Project Type | Question Set | Count |
|--------------|--------------|-------|
| Stateless CLI tool (linter, formatter, checker) | C1-C5 | 5 |
| Stateful CLI / pure logic library | U1-U10 | 10 |
| Feature-level MVP (no independent persistence) | U1-U10 | 10 |
| Web application / API service | U1-U10 + W1-W5 | 15 |
| Data-intensive system | U1-U10 + D1-D5 | 15 |
| Full-stack Web + data system | U1-U10 + W1-W5 + D1-D5 | 20 |

> **Stateless CLI determination:** No persistent state, no network I/O, input only from filesystem/stdin, output only to stdout/stderr + exit code. Use C1-C5 instead of the general layer only when ALL conditions are met.

> **Feature-level MVP upgrade conditions:** Only append W1-W5 (→15 questions) if the MVP feature itself includes HTTP interfaces, or append D1-D5 (→15 questions) if it includes persistence. If both a web interface and persistence are needed, classify as "Full-stack Web + data system" using the 20-question standard set (U10+W5+D5) — do not use the feature-level MVP path.

> **Layer skip vs. single-question N/A distinction:**
> - **Layer skip** (recommended): If the MVP feature as a whole doesn't involve a layer (e.g. no persistence → skip D1-D5), simply don't ask that layer's questions. Those question IDs won't appear in the scorecard, and total question count decreases accordingly.
> - **Single-question N/A**: Within an applicable layer, if individual questions don't apply due to project characteristics, still record the question and mark `severity: "n/a"`.
> - **Primary rule**: Prefer layer skip; only use single-question n/a when "the layer as a whole applies but individual questions don't."

Full question list is in `references/stress-test-prompts.md`.

> **Note**: Replace `[bracketed placeholders]` in each question with the specific entity names from your project.

---

## Step 3: Collect Structured Scorecard

Extract the JSON line from the end of each AI answer and aggregate into a scorecard array:

```json
[
  {"question_id": "U1", "passed": true, "severity": "none", "vulnerability": "none"},
  {"question_id": "U2", "passed": false, "severity": "high", "vulnerability": "No concurrency control — two simultaneous edits will cause data overwrite"},
  {"question_id": "W1", "passed": false, "severity": "medium", "vulnerability": "Database connection pool has no upper limit — may exhaust connections at peak load"},
  ...
]
```

Save as `spec/scorecard_v1.json`.

### Default Path: Manual Vulnerability Log

Fill in the following log table manually based on scorecard data:

### Optional Path: Automated Parsing (requires tools/scorecard_parser.py)

> When `tools/scorecard_parser.py` is ready, you can switch to the automated path:
>
> ```bash
> python tools/scorecard_parser.py spec/scorecard_v1.json
> ```
>
> The tool will output:
> 1. **Vulnerability log** (Markdown format, ready to save as `stress_test_v1.md`)
> 2. **Convergence verdict** (convergence threshold (收敛阈值): 0 high-severity + ≤3 medium-severity = converged)

---

## Manual Log Table

```markdown
## Stress Test Vulnerability Log
Date:
Spec Version: v1.0

| ID  | Passed | Issue Description | Severity |
|-----|--------|-------------------|----------|
| U1  | ✅ / ⚠️ | | none/low/medium/high/n/a |
| U2  | | | |
| ...  | | | |
| [last question] | | | |

High-severity issue count: X
Medium-severity issue count: X

Convergence verdict (收敛判断):
□ Converged (0 high + ≤3 medium) → Lock spec, proceed to Step 5
□ Not converged → Proceed to Template 04 for revision
```

---

## Output Storage

```
project-dir/
└── spec/
    ├── raw_requirements.md
    ├── spec_v1.md
    ├── scorecard_v1.json      (output of this step: structured verdict data)
    └── stress_test_v1.md      (generated from scorecard: vulnerability log + convergence verdict)
```
