# Template 04 — Feedback Revision (Iteration Loop)
# Purpose: Feed stress test findings back to AI to revise the SDD
# Conversation: Return to the Gemini conversation used for SDD writing (the Phase 2 conversation)
# New conversation required: No — reuse the Phase 2 conversation

---

## Steps

1. Return to the Phase 2 Gemini conversation (which still has the SDD context)
2. Paste the Prompt below, filling in the vulnerability list
3. Save the output as `spec_v2.md` (increment version number)
4. Re-run Template 03 (new conversation, re-test)
5. Loop until the convergence threshold (收敛阈值) is met: 0 high-severity + ≤3 medium-severity

---

## Prompt

```
The stress test found the following design issues. Please revise the corresponding SDD sections for each issue.

Issues found:
[Paste the entries marked "⚠️" from the vulnerability log, in this format]

Issue 1 (from W2, high-severity):
The current design only checks resource ownership at the business layer, not the data layer.
An attacker could bypass the business layer and call data access functions directly.

Issue 2 (from U5, medium-severity):
When the third-party payment service is unavailable, the system has no defined degradation strategy.
Users will see no response rather than a clear error message.

[Continue listing other issues...]

---

Revision requirements:
1. Only modify the sections with issues — do not change other parts
2. For each revision, explain "what it was" and "what it changed to"
3. After revisions are complete, output the full new version of the SDD
```

---

## Convergence Criteria

| Situation | Action |
|-----------|--------|
| High-severity issues > 0 | Must revise and re-test — cannot skip |
| Medium-severity issues > 3 | Recommend revising and re-testing |
| Medium-severity issues ≤ 3, low-severity only | Optional: revise before executing, or record as known debt |
| 0 high + 0 medium (all passed) | Lock spec, proceed to execution |

---

## Version Management

Increment version number with each revision:

```
project-dir/
└── spec/
    ├── raw_requirements.md
    ├── spec_v1.md
    ├── scorecard_v1.json       (structured verdict data)
    ├── stress_test_v1.md
    ├── spec_v2.md              (after revision)
    ├── scorecard_v2.json       (re-test verdict data)
    ├── stress_test_v2.md       (re-test log)
    ├── spec_v3.md              (if another revision is needed)
    └── spec_final.md           (final locked version, copied from last vN)
```

**Once `spec_final.md` is created, it is never modified.**
This is the sole input handed to Claude Code for execution.

---

## Handoff to Execution

When `spec_final.md` is locked, enter this in Claude Code:

```
Please implement the system defined in spec/spec_final.md following the spec-driven-dev execution spec.
Atomic commits, strictly corresponding to Spec sections. Stop and report immediately if any ambiguity is found.
```
