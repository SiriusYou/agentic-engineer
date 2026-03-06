# Planning Workflow (Steps 1-4)

> This documents the human planning phase before Claude Code execution.
> Claude Code does not directly execute these steps, but can reference them when users ask.

---

## Overview

```
Human                  Planning AI             Execution Agent
  |                        |                        |
  v                        |                        |
Idea Capture               |                        |
(Voice/Text)               |                        |
  |                        |                        |
  +----------------------->                         |
                     AI Structuring                  |
                   (Generate SDD v1)                 |
                          |                          |
                   +------v------+                   |
                   | Adversarial |                    |
                   | Stress Test |                    |
                   +------+------+                   |
                   Issues |         Spec Converged   |
                          |<-----------------+       |
                   Fix &  |                  |       |
                   Iterate+------------------+       |
                          |                          |
                          +------------------------->
                                              Unattended Execution
                                              (Claude Code)
```

---

## Step 1: Idea Capture (Human)

**Duration:** 20-60 minutes

**Tool:** WisprFlow or any voice/text tool

**What to do:**
- Freely dump all ideas without self-censorship
- Cover: feature requirements, user stories, technical intuitions, edge cases, known risks
- No structure needed - the rawer the better

**Output:** Raw requirements text (500-2000 words)

**Note:** This is the only phase requiring deep human creative involvement. Quality here determines all downstream outputs.

---

## Step 2: AI Structuring (Planning AI Round 1)

**Tool:** New Gemini conversation

**Input prompt template:** `templates/step2_sdd_gen.md`

```
Based on the following requirements description, generate a complete
Software Design Document (SDD).

Requirements:
[paste raw requirements text]

The SDD must include these sections:
1. Project Overview (goal, core user scenarios, system boundary)
2. Tech Stack (with selection rationale)
3. System Architecture (component breakdown, responsibilities, dependencies)
4. Interface Definitions (all API endpoints with request/response formats)
5. Data Model (entity definitions, field types, index strategy)
6. Error Handling Strategy

Ensure each section is detailed enough for a developer to implement
without further communication.
```

**Output:** `spec_v1.md`

---

## Step 3: Adversarial Stress Test (Planning AI Round 2)

**Tool:** Brand new Gemini conversation (MUST be fresh, cannot reuse Step 2's)

**Steps:**
1. Paste complete `spec_v1.md`
2. Select question layers by project type (see `references/stress-test-prompts.md`)
3. Record each discovered vulnerability, collect JSON scorecard

**Judgment:**
- Vulnerabilities found -> proceed to Step 4
- No major issues -> proceed to convergence

---

## Step 4: Iteration Loop

**Trigger:** Stress test found issues

**Process:**
1. Compile all discovered issues into a list
2. Feed back to Planning AI (can reuse Step 2's conversation), request revisions
3. Output `spec_v2.md`
4. Re-run stress test (with a new conversation)
5. Loop until convergence threshold is met

**Exit criteria:** Convergence threshold: 0 high-severity + <=3 medium-severity

**Output:** `spec_final.md` (locked, no further modifications)

---

## Step 5: Handoff to Execution

Hand `spec_final.md` to Claude Code, following the execution workflow in `references/execution-workflow.md`.
Launch command: see `references/quick-reference.md`.

---

## Supplementary Processes

- **Phase 0 Postmortem:** After project completion, use `templates/step0_postmortem.md` to review the full Step 1-5 process
- **Change Request (CR):** Process for modifying `spec_final.md` after lock, see `references/quick-reference.md`
