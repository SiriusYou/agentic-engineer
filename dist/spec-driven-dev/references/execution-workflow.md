# Spec-Driven Execution Workflow (Step 5)

## Core Principle

> **The spec is the single source of truth. Code is a physical projection of the spec, not a creative act.**

Read the complete spec before starting execution. Never expand functionality on your own.
If you discover spec ambiguity, stop and ask - do not guess.

---

## Pre-Execution Checklist (All must be completed)

```
[ ] 1. Find and read the spec file (spec.md / spec_final.md / spec_final_v*.md / SDD.md)
[ ] 2. Confirm three major sections exist: Component Design / Interface Definitions / Tech Stack
[ ] 3. List all implementation modules, sorted by dependency order
[ ] 4. Identify all external dependencies (libraries, APIs, environment variables)
[ ] 5. Confirm no ambiguity points; if any, ask immediately - do not guess
```

If the spec file does not exist or is incomplete, **stop execution and inform the user**.
Do not start writing code.

---

## Execution Order (Build-First Principle)

```
Phase 1: Foundation
  -> Project initialization, directory structure, dependency installation
  -> Configuration files (.env.example, config)
  -> Data models / type definitions

Phase 2: Core
  -> Core modules defined in the spec
  -> Strict interface compliance - no additions, no omissions

Phase 3: Integration
  -> Inter-module connections
  -> External service integration

Phase 4: Runnable
  -> Make the system runnable (even if features are incomplete)
  -> Verify critical paths work

Phase 5: Polish
  -> Error handling
  -> Edge cases
  -> Logging and observability
```

**Principle: Commit after each Phase, ensuring every commit point is a working state.**

---

## Atomic Commit Convention

### Commit Granularity
Each commit does **one complete thing**:
- GOOD: `feat: add UserRepository with findById and save methods`
- GOOD: `feat: implement JWT authentication middleware`
- BAD: `feat: add users and auth and config and tests`

### Commit Message Format
```
<type>(<scope>): <what was done>

Spec section: <section name>
```

**Types:**
- `feat` - New feature implementation
- `fix` - Fix implementation error
- `refactor` - Restructure (no behavior change)
- `test` - Add tests
- `chore` - Configuration, dependencies

### When to Commit
Commit immediately after completing a **minimal complete functional unit**. Do not accumulate.

---

## Spec Deviation Handling

When encountering these situations during execution, **stop and report - do not decide on your own**:

| Situation | Action |
|-----------|--------|
| Unclear interface description in spec | Stop, list specific ambiguity, wait for confirmation |
| Tech stack conflict discovered in spec | Stop, describe conflict, provide two options |
| Feature "obviously needed" but not in spec | Stop, describe finding, ask whether to add |
| Logic gap discovered in spec | Stop, describe gap, do not self-fix |

**Prohibited behaviors:**
- Adding features not defined in the spec
- Changing spec-defined interface signatures
- Replacing spec-specified tech stack
- "I think this is better" style autonomous optimization

---

## Progress Report Format

After completing each module, output:

```
DONE: [Module Name]
  Spec section: <chapter name>
  Implementation: <one-sentence description>
  Commit: <first 7 chars of hash>

NEXT: [Next Module Name]
```

If blocked:

```
BLOCKED: [Module Name]
  Reason: <specific description>
  Need confirmation: <specific question>
  Waiting for response before continuing
```

---

## Completion Acceptance Criteria

After execution completes, output an acceptance report:

```markdown
## Execution Completion Report

### Spec Coverage
- Components: X/X implemented
- Interfaces: X/X implemented
- Tech stack: Per spec

### Commit History
- Total: X atomic commits
- Final runnable state: YES / NO

### Deviation Record
- Deviation count: X
- Deviation details: (if any)

### Unimplemented Items
- (if any, explain reasons)
```

---

## Quick Reference: Execution Launch Prompt

When the user provides a spec, start with:

```
I will process this task following the spec-driven execution workflow.

First, reading the spec file...
[after reading]

Spec analysis complete:
- Identified X components
- X interface definitions
- Tech stack: [list]

Execution order planned:
1. [Phase 1 content]
2. [Phase 2 content]
...

Questions requiring confirmation before starting: (if any)
- [question 1]

Ready to begin after confirmation.
```
