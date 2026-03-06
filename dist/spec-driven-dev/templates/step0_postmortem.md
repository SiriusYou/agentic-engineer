# Template 00 — Project Postmortem (Phase 0 Postmortem)
# Purpose: Review the planning workflow after project completion, collect improvement data
# Conversation: Any
# New conversation required: No

> Phase 0 = Meta-workflow evaluation phase. Numbered 00 to indicate this is a retrospective on the entire Step 1-5 process itself.
> Recommended after each project completion, not mandatory.

---

## When to Use

- After project completion (recommended)
- After each execution of the planning workflow
- Suggested: record time spent at each step completion, fill in other fields during postmortem

---

## Steps

1. Copy this template to `spec/postmortem_v1.md`
2. Fill in basic information and time spent per phase (wall-clock time by default, active time optionally noted)
3. Fill in convergence data (收敛数据)
4. Fill in Start/Stop/Continue feedback
5. Assign at least one action item to each feedback point

---

## Postmortem Data Tables

### Basic Information
| Field | Value |
|-------|-------|
| Project Name | |
| Completion Date | |
| Spec Final Version | vN |
| Total Time (wall-clock) | |

### Time Spent per Phase
| Phase | Time | Iterations | Friction Points (摩擦点) |
|-------|------|------------|--------------------------|
| Step 1 Inspiration Capture | | 1 | |
| Step 2 SDD Generation | | | |
| Step 3 Stress Test | | | |
| Step 4 Feedback Revision | | | |
| Step 5 Lock & Execute | | | |

### Convergence Data (收敛数据)
| Metric | Value |
|--------|-------|
| Total stress test rounds | |
| Round 1 high-severity issues | |
| Round 1 medium-severity issues | |
| Final round high-severity issues | 0 |
| Final round medium-severity issues | |
| Change requests (CR) | |
| Ambiguity pauses during execution | |

### Convergence Speed — Severity Trend per Round
| Round | High Severity | Medium Severity | Low Severity |
|-------|---------------|-----------------|--------------|
| Round 1 | | | |
| Round 2 | | | |
| Round 3 | | | |

---

## Start / Stop / Continue Feedback

> This framework produces more actionable improvement suggestions than open-ended questions.
> Answer from the perspective of the workflow and templates, not self-evaluation.

### Start (things to start doing)
| Suggestion | Reason |
|------------|--------|
| | |

### Stop (things to stop doing)
| Suggestion | Reason |
|------------|--------|
| | |

### Continue (things to keep doing)
| Suggestion | Reason |
|------------|--------|
| | |

---

## Open-Ended Feedback

1. Which step's template design was most helpful? Why?
2. Which step's template design had problems? How would you improve it?
3. How was the AI output quality? Which steps required the most manual correction?
4. If starting over, what would you change?
5. Any improvement suggestions for the toolchain (WisprFlow / Gemini / Claude Code)?

---

## Action Items

> Each Start/Stop/Continue feedback point must have at least one corresponding action item.

| # | Action Item | Source | Owner | Due Date | Status |
|---|-------------|--------|-------|----------|--------|
| 1 | | Start/Stop/Continue #N | | | □ Pending |
| 2 | | | | | □ Pending |
| 3 | | | | | □ Pending |

---

## Output Storage

```
project-dir/
└── spec/
    └── postmortem_v1.md
```
