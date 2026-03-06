---
name: spec-driven-dev
description: >
  Use when the user wants to plan a software project before coding, when they mention
  "spec driven", "SDD", "design doc", "stress test the spec", "spec lint", "adversarial review",
  "60/40 workflow", or when they say "execute the spec", "build from spec", "implement this design".
  Also use when a spec file (spec.md, spec_final.md, SDD) is present and the user asks to implement it.
---

# Spec-Driven Development

A methodology for turning ideas into reliable software through structured planning
and adversarial stress testing. Validated across 7 project tracks with measurable results:
single-round convergence, 5.1% spec deviation rate, and 0.75x coding-to-planning time ratio.

**Core philosophy:** 60% planning / 40% execution. Find design flaws before writing code.

## Quick Start

**Planning a new project (Steps 1-4):**
1. Capture your idea with `templates/step1_inspiration.md`
2. Generate an SDD with `templates/step2_sdd_gen.md`
3. Stress test with `templates/step3_stress_test.md`
4. Iterate until convergence: 0 high-severity + <=3 medium-severity issues

**Executing from a spec (Step 5):**
1. Read the spec completely before writing any code
2. Follow build-first ordering (foundation -> core -> integration -> runnable -> polish)
3. Atomic commits, one complete unit per commit
4. Stop and ask on any ambiguity. Never deviate from spec without approval.

## The 5-Step Workflow

```
Step 1: Idea Capture          Voice/text -> structured requirements
Step 2: SDD Generation        AI generates Software Design Document v1
Step 3: Stress Test           Fresh AI session, adversarial review (5-20 questions)
Step 4: Iteration             Fix issues, re-test until convergence
Step 5: Execution             Claude Code implements from locked spec
```

### Step 1: Idea Capture (Inspiration)

**Duration:** 20-60 minutes | **Tool:** Any AI or voice transcription

Freely dump all ideas without self-censorship. Cover: features, user stories,
technical intuitions, edge cases, known risks. Raw is better than polished.

**Output:** `spec/raw_requirements.md`

**Prompt template:** `templates/step1_inspiration.md`

### Step 2: SDD Generation

**Tool:** New Gemini conversation (fresh context)

Feed structured requirements to AI with the SDD template. The output must contain
all 6 required chapters (see SDD Template below).

**Output:** `spec/spec_v1.md`

**Prompt template:** `templates/step2_sdd_gen.md`
**Structure reference:** `references/sdd-template.md`

### Step 3: Adversarial Stress Test

**Tool:** Brand new AI conversation (MUST be isolated from Step 2)

The AI that wrote the SDD has emotional attachment to its design and will defend
flaws. A fresh session provides objective scrutiny.

Select question layers by project type:

| Project Type | Question Set | Count |
|---|---|---|
| Stateless CLI tool | C1-C5 | 5 |
| Stateful CLI / logic library | U1-U10 | 10 |
| Feature-level MVP | U1-U10 | 10 |
| Web app / API service | U1-U10 + W1-W5 | 15 |
| Data-intensive system | U1-U10 + D1-D5 | 15 |
| Full-stack Web + Data | U1-U10 + W1-W5 + D1-D5 | 20 |

**Output:** `spec/scorecard_v1.json` + `spec/stress_test_v1.md`

**Prompt template:** `templates/step3_stress_test.md`
**Question bank:** `references/stress-test-prompts.md`

### Step 4: Iteration Loop

**Tool:** Return to Step 2's conversation (has SDD context)

Feed all discovered issues back. AI revises only affected sections.
Re-test with a fresh conversation. Loop until convergence.

**Convergence threshold:** 0 high-severity + <=3 medium-severity issues

**Output:** `spec/spec_v2.md` -> re-test -> ... -> `spec/spec_final.md`

**Prompt template:** `templates/step4_iteration.md`

### Step 5: Spec-Driven Execution

**Tool:** Claude Code

The spec is the single source of truth. Code is a physical projection of the spec,
not a creative act. Read the full spec before writing any code.

**Execution order (build-first):**
```
Phase 1: Foundation  -> Project init, directory structure, dependencies, data models
Phase 2: Core        -> Core modules per spec, strict interface compliance
Phase 3: Integration -> Module connections, external service integration
Phase 4: Runnable    -> Make the system run (even if incomplete)
Phase 5: Polish      -> Error handling, edge cases, logging
```

**Key rules:**
- Each phase ends with a working-state commit
- One complete unit per commit: `feat: add UserRepository with findById and save`
- Stop and report on any spec ambiguity, conflict, or gap
- Never add features not in the spec
- Never change spec-defined interfaces
- Never replace spec-specified tech stack

**Deviation handling:**

| Situation | Action |
|---|---|
| Unclear interface description | Stop, list specific ambiguity, wait for confirmation |
| Tech stack conflict in spec | Stop, describe conflict, provide two options |
| "Obviously needed" feature not in spec | Stop, describe finding, ask whether to add |
| Logic gap discovered in spec | Stop, describe gap, do not self-fix |

**Full execution reference:** `references/execution-workflow.md`

## File Naming Convention

```
project/spec/
  raw_requirements.md        Step 1 output
  spec_v1.md                 Step 2 output
  scorecard_v1.json          Step 3 output (structured judgment)
  stress_test_v1.md          Step 3 output (vulnerability record)
  spec_v2.md                 Step 4 output (if needed)
  scorecard_v2.json          Re-test (if needed)
  spec_final.md              Locked version for execution
  postmortem_v1.md           Phase 0 retrospective
```

## Quality Gates

### Convergence Threshold

A spec is ready for execution when the stress test scorecard shows:
- **0** high-severity issues
- **<=3** medium-severity issues

Use `scripts/scorecard_parser.py` to automate convergence checking.

### SDD Completeness

All 6 required chapters must be present:
1. Project Overview (goal, user scenarios, system boundary)
2. Tech Stack (with selection rationale)
3. System Architecture (components, responsibilities, dependencies)
4. Interface Definitions (API endpoints or CLI args with full contracts)
5. Data Model (entities, fields, constraints, indexes)
6. Error Handling Strategy (error types, handling, user messages)

Use `scripts/spec_lint.py` to validate SDD structure.

### Spec Lint Format Quick Reference

**Document header** (each on its own line):
```
Version: v1.0
Status: Draft
Last Updated: 2026-03-05
```

**Section numbering:** `## 1. Title` (number + dot + space before title)

**Pattern definitions (Section 8, if applicable):**
- Each checker needs 3+ positive examples and 3+ negative examples
- Use numbered items: `1. [input] -> [expected result]`

## Tool Reference

### scorecard_parser.py

Parse stress test scorecards into vulnerability reports with convergence judgment.

```bash
# Markdown report (default)
python3 scripts/scorecard_parser.py spec/scorecard_v1.json

# JSON structured output (for automation)
python3 scripts/scorecard_parser.py spec/scorecard_v1.json --format json

# Write to file
python3 scripts/scorecard_parser.py spec/scorecard_v1.json --output report.md
```

### spec_lint.py

Validate SDD document structural completeness.

```bash
# Quick check
python3 scripts/spec_lint.py spec/spec_final.md

# Detailed Markdown report
python3 scripts/spec_lint.py spec/spec_final.md --format markdown

# JSON output
python3 scripts/spec_lint.py spec/spec_final.md --format json

# Run specific checkers only
python3 scripts/spec_lint.py spec/spec_final.md --check section_presence,tbd_marker
```

### check_consistency.py

Validate cross-file references and spec directory naming conventions.

```bash
# Check current project
python3 scripts/check_consistency.py

# Summary mode
python3 scripts/check_consistency.py --format summary
```

## Project Type Adaptation

### CLI Tools
- Use C1-C5 stress test questions (replace U1-U10)
- SDD Section 4 uses variant 4.B (CLI interface: args, stdin/stdout, exit codes)
- Exit codes: 0=success, 1=validation failure, 2=usage error

### Web Applications / API Services
- Use U1-U10 + W1-W5 stress test questions
- SDD Section 4 uses variant 4.A (REST API: endpoints, request/response, status codes)
- Address authentication, authorization, CORS, rate limiting

### Full-Stack Systems
- Use U1-U10 + W1-W5 + D1-D5 (full 20-question set)
- SDD needs both 4.A and 4.B variants if applicable
- Address caching, database migrations, query performance

### Feature-Level MVP
- Use U1-U10 (universal questions only)
- Upgrade to 15 questions if MVP includes HTTP interface (add W1-W5)
  or persistence (add D1-D5)
- If both, classify as full-stack (20 questions)

## Change Request Process

After `spec_final.md` is locked, changes follow this process:
1. Document the change reason and affected spec sections
2. Copy `spec_final.md` -> `spec_final_v2.md`
3. Modify only necessary sections
4. Re-run full stress test on the new version
5. Lock when convergence threshold is met
6. Never modify an already-locked spec file

## Postmortem (Phase 0)

After project completion, use `templates/step0_postmortem.md` to capture:
- Time spent per step and iteration count
- Convergence data (severity trends across rounds)
- Start/Stop/Continue feedback with action items

## Reference Documents

- `references/planning-workflow.md` - Detailed Steps 1-4 flow
- `references/sdd-template.md` - SDD 6-chapter structure template
- `references/stress-test-prompts.md` - Full stress test question bank
- `references/execution-workflow.md` - Step 5 execution rules
- `references/quick-reference.md` - One-page quick reference card
