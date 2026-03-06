# SDD Standard Template (Software Design Document)

> Purpose: The Execution Agent uses this template to verify spec completeness before starting.
> If any Required chapter is missing, stop execution and inform the user.

---

## Document Header

```markdown
# [Project Name] - Software Design Document (SDD)
Version: v1.0
Status: Draft / Review / Final
Last Updated: YYYY-MM-DD
```

---

## 1. Project Overview [Required]

### 1.1 Goal
One sentence describing what problem this system solves.

### 1.2 Core User Scenarios
List 3-5 most important user stories:
- As a [user type], I want to [do something], so that [I gain value]

### 1.3 System Boundary
Explicitly list features that are **not** in scope for this implementation.

---

## 2. Tech Stack [Required]

| Layer | Technology | Version | Selection Rationale |
|-------|-----------|---------|-------------------|
| Language | | | |
| Framework | | | |
| Database | | | |
| Cache | | | |
| Message Queue | | | |
| Deployment | | | |

**Environment Variables:**
```
VARIABLE_NAME=Description (required/optional, default value)
```

---

## 3. System Architecture [Required]

### 3.1 Component Overview

```
[Diagram or text describing components and their relationships]
```

### 3.2 Component Details

Each component includes:

#### [Component Name]
- **Responsibility**: What this component does
- **Input**: What data/events it accepts
- **Output**: What data/events it produces
- **Dependencies**: Which other components it depends on
- **Not responsible for**: Explicit boundary

---

## 4. Interface Definitions [Required]

> Select variant 4.A (Web/API) or 4.B (CLI tool) based on project type. Do not mix.

### Variant 4.A: Web/API Interfaces

#### 4.A.1 External API

Each endpoint:
```
METHOD /path/to/endpoint
Description: What this endpoint does

Request:
  Headers: { Authorization: Bearer <token> }
  Body: {
    field_name: type  // description, required/optional
  }

Response:
  200: { ... }
  400: { error: string }
  401: { error: "Unauthorized" }

Side effects: What it triggers (send email, write to DB, etc.)
```

#### 4.A.2 Internal Interfaces / Function Signatures

```typescript
// functionName(param: Type): ReturnType
// Description: what it does, when it throws exceptions
```

### Variant 4.B: CLI Interfaces

#### 4.B.1 Command-Line Arguments

```
Usage: tool_name [options] <positional_args>

Positional arguments:
  input_path          Input file or directory path

Options:
  --flag VALUE        Description (default: X)
  --verbose           Enable detailed output
  -o, --output FILE   Output file path (default: stdout)

Environment variables:
  TOOL_ROOT           Project root directory override (default: auto-detect)
```

#### 4.B.2 stdin/stdout/stderr Contract

| Channel | Purpose | Format |
|---------|---------|--------|
| stdin | Pipe input (optional) | Mutually exclusive with positional args |
| stdout | Primary output (reports, data) | Human-readable (default) or JSON (`--format json`) |
| stderr | Diagnostics, errors, progress | Free-form, does not affect downstream pipes |

#### 4.B.3 Exit Code Semantics

| Exit Code | Meaning | Trigger Condition |
|-----------|---------|------------------|
| 0 | Success | All checks pass / normal completion |
| 1 | Validation failure | Input is valid but checks found issues |
| 2 | Usage error | Missing args, file not found, format error |

#### 4.B.4 POSIX Composability

Describe how the tool interacts with pipes and redirects:
- Supports `tool input.md | grep FAIL` pipe chains
- Supports `tool input.md > report.md` output redirection
- stderr does not interfere with downstream pipes

### 4.C Internal Interfaces / Function Signatures (All project types)

```python
# function_name(param: Type) -> ReturnType
# Description: what it does, when it raises exceptions
```

---

## 5. Data Model [Required]

Each entity:

```
Entity: [Name]
Fields:
  - id: UUID, primary key, auto-generated
  - field: type, constraints, description
Indexes:
  - (field1, field2): rationale
Associations:
  - Relationship type with [other entity]
```

---

## 6. Error Handling Strategy [Required]

### Error Classification
| Error Type | Handling | User Message |
|-----------|---------|-------------|
| Network timeout | Retry 3x then return error | "Please try again later" |
| Data validation failure | Return 400 immediately | Specific field error message |
| Internal service error | Log, return 500 | "System error, please contact support" |

---

## 7. Non-Functional Requirements [Optional but Recommended]

### Performance Requirements
- API response time: P99 < X ms
- Concurrent users: X

### Security Requirements
- Authentication method
- Data encryption requirements
- Sensitive data handling

---

## 8. Pattern Definition Constraints [Required for tools with pattern matching]

> Applicable to tools containing regex, glob patterns, or other matchers.

### Constraint Rules

1. **Exact regex**: All matchers must provide exact regex patterns. No vague phrasing like "or equivalent" or "similar patterns"
2. **Positive/negative validation**: Each regex must have at least 3 positive examples (should match) and 3 negative examples (should not match)
3. **Boundary documentation**: Note known false positives/negatives

### Template

```
Checker: [name]
Pattern: `regex`
Flags: re.MULTILINE / re.VERBOSE / ...

Positive examples (should match):
  1. [input] -> [expected match result]
  2. [input] -> [expected match result]
  3. [input] -> [expected match result]

Negative examples (should not match):
  1. [input] -> no match
  2. [input] -> no match
  3. [input] -> no match

Known boundaries (false positives/negatives):
  - False positive: [scenario] -> [why] -> [mitigation or accepted]
  - False negative: [scenario] -> [why] -> [mitigation or accepted]
```

---

## Spec Completeness Checklist

Execution Agent validates before starting:
- [ ] Chapters 1-6 all present
- [ ] Every component has clear responsibility description
- [ ] Every API endpoint has request/response format (4.A) or CLI args/exit codes (4.B)
- [ ] All environment variables listed
- [ ] No "TBD" or "to be determined" for key decisions
- [ ] Tools with pattern matching: Chapter 8 exists, each regex has 3+ positive + 3+ negative examples
- [ ] No vague phrasing like "or equivalent" or "similar patterns"

---

## spec_lint Format Quick Reference

> Check this before writing an SDD to avoid rework at the final stage.
> Corresponds to `scripts/spec_lint.py` check rules.

### Document Header (each must be on its own line)

```
Version: v1.0
Status: Draft
Last Updated: 2026-03-05
```

- Version format: `^Version:\s*v\d+\.\d+` (or `^版本:\s*v\d+\.\d+`)
- Status format: `^Status:\s*\S+` (Draft / Review / Final)
- Date format: `^Last Updated:\s*\d{4}-\d{2}-\d{2}`

### Section 8 Pattern Definitions (required for tools with regex/matchers)

- Checker block title: `### CheckerName`
- Positive examples format: `Positive examples (should match):`
- Negative examples format: `Negative examples (should not match):`
- Each group needs at least 3 numbered items: `1. ...`

### Common Pitfalls

- Version/Status/Last Updated cannot be combined into one line
- Section 8 positive/negative examples must use `1. ` format (number+dot+space), not `- ` lists
- Section numbering format: `## 1. Title` (number and title separated by `. `)
