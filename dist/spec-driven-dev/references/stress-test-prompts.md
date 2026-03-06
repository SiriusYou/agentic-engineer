# Adversarial Stress Test Question Bank

> Purpose: After completing the SDD, use a brand new AI conversation to ask these questions
> and find design vulnerabilities. Feed issues back to the Planning AI to revise the spec
> until convergence threshold is met.

**How to use:**
1. Open a brand new AI conversation (do NOT reuse the SDD-writing session)
2. Paste the complete SDD, then select questions by project type
3. Record each finding, collect the JSON scorecard

---

## Project Type Selection

Select question set combinations based on project characteristics:

| Project Type | Question Sets | Total |
|---|---|---|
| Stateless CLI tool (lint, formatter, checker) | CLI Layer | 5 |
| Stateful CLI / pure logic library | Universal Layer | 10 |
| Feature-level MVP (no independent persistence) | Universal Layer (U1-U10) | 10 |
| Web app / API service | Universal + Web/API Layer | 15 |
| Data-intensive system | Universal + Data Layer | 15 |
| Full-stack Web + Data system | Universal + Web/API + Data Layer | 20 |

> **Feature-level MVP upgrade conditions:** Only add W1-W5 when the MVP itself includes HTTP interfaces (->15 questions), or add D1-D5 when it includes persistence (->15 questions). If both web interface and persistence are needed, classify as "Full-stack Web + Data" and use the full 20-question set.

> **Layer skip vs single-question N/A:**
> - **Layer skip** (recommended): If the MVP doesn't involve a layer at all (e.g., no persistence -> skip D1-D5), don't ask that layer. Those question IDs don't appear in the scorecard.
> - **Single-question N/A**: Within an applicable layer, mark individual inapplicable questions with `severity: "n/a"`.
> - **Primary rule**: Prefer layer skip; only use single-question n/a when "the layer applies but a specific question doesn't."

> **CLI tool determination:** Use the CLI Layer instead of Universal if ALL of:
> - No persistent state (no database, no sessions)
> - No network I/O (no external API calls, no server)
> - Input only from filesystem and stdin
> - Output via stdout/stderr + exit code

---

## 0. CLI Layer (Stateless CLI Tools, 5 questions)

Questions designed for stateless command-line tools (linters, formatters, checkers).
Replaces Universal Layer U1-U10 for tools that don't apply.

**C1. Input Boundaries**
> Is the tool's behavior explicitly defined for: (a) Empty files (0 bytes) (b) Very large files (100MB+) (c) Non-UTF-8 encoded files (e.g., Latin-1, binary) (d) UTF-8 files with BOM header? Which cases should error out, and which should be gracefully skipped?

**C2. Regex/Matcher Robustness**
> Where are the false positive and false negative boundaries for each regex or matcher in the tool? Provide a reasonable input that causes an unexpected match (false positive) or misses something that should match (false negative).

**C3. Empty Directory / No Matching Files**
> If the target directory is empty, or no files match the glob/filter conditions, does the tool silently return success (exit 0), or report a "no files found" warning? Which behavior is correct? How does the user distinguish "all passed" from "nothing was checked"?

**C4. Path Resolution Ambiguity**
> Are all of these path scenarios explicitly handled? (a) Relative vs absolute paths (b) Symlink targets (c) Paths containing spaces or special characters (d) Priority when `--root` parameter conflicts with cwd.

**C5. Output Format & Exit Code Correctness**
> Can stdout output be correctly parsed by downstream pipes (e.g., `tool | grep FAIL`)? Does stderr pollute stdout? Do exit codes strictly distinguish "checks passed" (0), "checks found issues" (1), and "tool itself errored" (2)?

---

## 1. Universal Layer (Required for all projects, 10 questions)

Questions testing fundamental robustness that any software system must have.

**U1. Resource Leaks**
> If a user's operation is interrupted mid-way by a network disconnection, will the system produce orphaned resources (unclosed connections, unreleased locks, half-completed transactions)?

**U2. Concurrent Write Conflicts**
> When two users simultaneously modify the same [entity] data, whose modification wins? Does the current design have optimistic or pessimistic locking?

**U3. Distributed Transaction Boundaries**
> [Operation A] and [Operation B] must complete atomically, but they span two different modules/services. If A succeeds but B fails, what state is the data in? How to recover?

**U4. Keys & Sensitive Data**
> Where are keys, tokens, and passwords stored in the system? How are they transmitted? Could they appear in logs? What scenarios might cause key leakage?

**U5. External Dependency Unavailable**
> If [third-party service/API] goes down for 30 minutes, which system features become completely unavailable? Is there a degradation strategy? What does the user see?

**U6. Data Loss Scenarios**
> Under what circumstances might the system lose user data? What data loss risks do database crashes, server restarts, and deployment rollbacks each create?

**U7. Error State Recovery**
> If the system enters an "error state" (e.g., a record stuck in "processing" status), how do operations staff discover and fix it? Is there an admin console or recovery tool?

**U8. Empty State Handling**
> Is the behavior explicitly defined for all list-type interfaces when returning empty results? Will the frontend correctly handle empty arrays or crash?

**U9. Extreme Input Values**
> A user submits a request with 100MB content, or a field with 10,000 characters, or uploads a 0-byte file - how does the system respond?

**U10. Production Issue Investigation**
> A user reports "some operation occasionally fails" with no error message. How long would it take operations staff to find the cause, and through what means? Are the current logging, tracing, and monitoring/alerting designs sufficient?

---

## 2. Web/API Additional Layer (Add for Web apps and API services, 5 questions)

Questions targeting systems with HTTP interfaces, user authentication, and browser interaction.

**W1. Peak Concurrency**
> If [core system operation] is triggered simultaneously by 1000 users, where will the system fail first? Database connection pool, message queue, or a single-point service?

**W2. Horizontal Privilege Escalation**
> Can User A access User B's private data by modifying the ID parameter in a request? At which layer are permission checks implemented?

**W3. Authentication Bypass**
> Which API endpoints lack authentication? Is their public access intentional? Is there a path to indirectly affect system state through unauthenticated endpoints?

**W4. Input Injection**
> In what form does user input ultimately appear in: SQL queries, shell commands, HTML rendering, third-party API calls? Does each path have corresponding filtering/escaping?

**W5. Interface Extensibility**
> In 6 months, [core interface] needs 3 new fields - how will existing clients be affected? Does this interface have a versioning strategy?

---

## 3. Data-Intensive Additional Layer (Add for data-intensive systems, 5 questions)

Questions targeting systems involving large-scale data storage, querying, migration, and caching.

**D1. Slow Query Time Bomb**
> When the [core table] in the database grows to 10 million rows, which interfaces will start noticeably slowing down? Can the current index design support this?

**D2. Cache Consistency**
> If caching is used and data is modified directly in the database, when does the cache invalidate? Before invalidation, will users read stale data?

**D3. Database Schema Changes**
> If a non-nullable field addition or field type change is needed on [core table], can it be done without downtime?

**D4. Adding New Service Providers**
> If a second external data source/service provider needs to be integrated in 3 months, which parts of the current architecture need changes? Is the change scope local or global?

**D5. Timezone & Time**
> For time-related logic (expiration checks, sorting, display), is behavior consistent across users in different timezones? Does the database store UTC or local time?

---

## Scorecard Format

Each AI answer must end with a structured JSON judgment:

```json
{"question_id": "U1", "passed": true, "severity": "none", "vulnerability": "None"}
```

- `passed`: true = design adequately covers this scenario (or n/a); false = vulnerability found
- `severity`: "none" (passed) / "low" / "medium" / "high" / "n/a" (not applicable)
- `vulnerability`: One-sentence description (use "None" when passed)

Collect all JSON lines into a scorecard array and save as `spec/scorecard_v1.json`.

Use `scripts/scorecard_parser.py` to generate the vulnerability report and convergence judgment.
