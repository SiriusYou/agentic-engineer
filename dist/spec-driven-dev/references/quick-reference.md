# Quick Reference Card
# High-frequency use version: read this one page each time you start a new project

---

## 5-Step Workflow Overview

```
Step 1  Idea Capture          Voice/text -> templates/step1 -> raw_requirements.md
          |
Step 2  SDD Generation        New Gemini -> templates/step2 -> spec_v1.md
          |                    (check references/sdd-template.md format guide first)
Step 3  Stress Test            Fresh Gemini (must be new) -> templates/step3
          |                    -> scorecard_v1.json + stress_test_v1.md
          |
          +-- Issues found -> Step 4
          +-- Converged (0 high + <=3 medium) -> Step 5
          |
Step 4  Iteration              Return to Step 2's Gemini -> templates/step4
          |                    -> spec_v2.md -> back to Step 3
          |
Step 5  Lock & Execute         spec_vN.md copied as spec_final.md -> Claude Code
```

---

## Which Conversation for Each Step

| Step | Tool | Conversation Requirement |
|------|------|--------------------------|
| Step 1 | Any AI | Any |
| Step 2 | Gemini | **New** conversation |
| Step 3 | Gemini | **Must be fresh** (fully isolated from Step 2), layered questions (5-20) |
| Step 4 | Gemini | Reuse Step 2's conversation |
| Step 5 | Claude Code | New project |

---

## File Naming Convention

```
project/spec/
  raw_requirements.md    Step 1 output
  spec_v1.md             Step 2 output
  scorecard_v1.json      Step 3 output (structured judgment data)
  stress_test_v1.md      Step 3 output (vulnerability record table)
  spec_v2.md             Step 4 output (if needed)
  scorecard_v2.json      Step 3 re-test (if needed)
  stress_test_v2.md      Step 3 re-test (if needed)
  spec_final.md          Final locked version, the only file handed to Claude Code
```

---

## Common Blockers

**Q: Step 2 SDD is missing a chapter**
-> Follow up in the same conversation, don't create a new one

**Q: Step 3 found many issues, feels like a lot to fix**
-> Normal - this means the stress test is working. Batch all issues and feed to Step 4 at once. Don't make small incremental fixes.

**Q: Step 4 revision re-tested, found new issues**
-> Normal - 2-3 rounds of iteration is expected. If it exceeds 5 rounds, the original requirements themselves are unclear. Go back to Step 1 to re-clarify.

**Q: Found an omission after spec_final.md was locked**
-> Follow the Change Request process below to create spec_final_v2.md

---

## Change Request Process

For modifications needed after `spec_final.md` is locked.

### Trigger Conditions
| Type | Example | Severity |
|------|---------|----------|
| Spec logic gap | Interface definition conflict found during execution | Must use CR |
| External requirement change | Client/product requests new feature | Must use CR |
| Missed issue | Scenario not covered by stress test | Must use CR |
| Typo correction | Spelling, formatting | Direct fix, no CR needed |

### Process
1. Create change description: one-sentence summary + list of affected spec sections
2. Assess scope: if >50% of sections affected, consider re-running from Step 1
3. Copy spec_final.md -> spec_final_v2.md
4. Modify spec_final_v2.md (only change necessary sections)
5. Fresh Gemini conversation: re-run Step 3 on complete spec_final_v2.md
6. Lock spec_final_v2.md when convergence threshold met (0 high + <=3 medium)
7. Notify Claude Code to switch to new version

### File Naming
spec_final.md -> spec_final_v2.md -> spec_final_v3.md
(accompanying artifacts: scorecard_final_v2.json, stress_test_final_v2.md)

### Principles
- Never modify an already-locked spec_final.md
- Each change has a clear trigger reason recorded
- Minimize modification scope - only change what's necessary
- Don't rollback committed code; make incremental changes on new spec version

---

## Project Postmortem (Phase 0)

After project completion, use `templates/step0_postmortem.md` to run a retrospective.
Record time per step, iteration rounds, severity decline curve, and process improvement data.

---

## Tool Command Reference

### scorecard_parser

```bash
# Default Markdown output
python3 scripts/scorecard_parser.py spec/scorecard_v1.json

# JSON structured output (for automation pipelines)
python3 scripts/scorecard_parser.py spec/scorecard_v1.json --format json

# Write to file
python3 scripts/scorecard_parser.py spec/scorecard_v1.json --output report.md
python3 scripts/scorecard_parser.py spec/scorecard_v1.json --format json --output report.json
```

### check_consistency

```bash
# Full report
python3 scripts/check_consistency.py

# Summary mode (for CI/hooks)
python3 scripts/check_consistency.py --format summary
```

---

## Claude Code Launch Command

```
Please follow the spec-driven-dev execution workflow to implement the system
defined in spec/spec_final.md. Use atomic commits, strictly aligned with spec
sections. Stop and report immediately if you find any ambiguity.
```
