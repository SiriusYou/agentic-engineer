# Template 02 — SDD Generation (SDD 生成)
# Purpose: Have AI transform structured requirements text into a complete Software Design Document
# Conversation: Gemini (new conversation, fresh context)
# New conversation required: Yes — do not reuse any prior conversation

---

## Steps

1. **Start a new** Gemini conversation
2. Determine the tech stack constraint source (see note below)
3. Paste the Prompt below, replacing `[requirements text]` with the full content of `raw_requirements.md`
4. Save the output as `spec_v1.md`

> **Tech stack constraint source:** If adding a feature to an **existing project**, the tech stack constraints should be inherited from the target project's codebase, not read from `conductor/tech-stack.md`. Replace the tech stack section in the Prompt with: `Inherited from [project name] existing codebase: [actual stack]`

---

## Prompt

```
Based on the requirements description below, generate a complete Software Design Document (SDD).
Requirements: each section must be detailed enough to hand directly to a developer for implementation, with no further clarification needed.

Tech stack constraints (choose from the allowed options below; do not use technologies outside this list):
[New project: extract from conductor/tech-stack.md; Existing project: inherit from target project codebase]
- Primary language: [e.g. TypeScript, Python] (choose what fits this project)
- Frontend framework: [e.g. React, Vue, Next.js] (choose what fits this project)
- Backend framework: [e.g. Django / FastAPI] (choose what fits this project)
- Database: [e.g. PostgreSQL, SQLite] (choose what fits this project)
- Infrastructure: [write "TBD" if not yet decided]

Design principle constraints (must be reflected in architecture decisions):
- Style tone: [extract from conductor/product-guidelines.md, e.g. Professional and technical]
- Core principles: [extract from conductor/product-guidelines.md, e.g. Performance first]

If any feature in the requirements conflicts with the above constraints, explicitly flag the conflict — do not silently substitute the tech stack.

Requirements:
[Paste full content of raw_requirements.md here]

---

Please output the SDD with the following structure:

# [Project Name] — Software Design Document
Version: v1.0
Status: Draft
Last Updated: [YYYY-MM-DD]

## 1. Project Overview
### 1.1 Objective (one sentence)
### 1.2 Core User Scenarios (3-5 user stories, format: As a... I want to... So that...)
### 1.3 System Boundaries (explicitly list features NOT in scope for this implementation)

## 2. Tech Stack
Table format: Layer | Technology | Version | Rationale
Also list all environment variables

## 3. System Architecture
### 3.1 Component Overview (text or ASCII diagram describing component relationships)
### 3.2 Details for Each Component
Each component includes: Responsibility / Input / Output / Dependencies / Explicit non-responsibilities

## 4. Interface Definitions
Each API endpoint includes:
- METHOD + path
- Description
- Request (Headers + Body, with field types and required/optional)
- Response (structure for each status code)
- Side effects

## 5. Data Model
Each entity includes: Field name / Type / Constraints / Description / Index strategy / Entity relationships

## 6. Error Handling Strategy
Table format: Error type | Handling approach | User-facing message
```

---

## Completion Criteria

After receiving output, verify:
- [ ] All sections 1-6 are present
- [ ] All interfaces have request/response formats
- [ ] Tech stack table is filled in
- [ ] Tech stack is consistent with the chosen constraint source (no unauthorized substitutions of language/framework/database)
- [ ] No "TBD", "pending", or "to be confirmed" text appears

> **Note:** Before writing the SDD, read the **spec_lint format reference** at the end of `references/sdd-template.md` to avoid reformatting work in the final stage.

If anything is missing, follow up in the **same conversation**:
```
Section [X] [specific section name] is not detailed enough. Please add: [specific missing content]
```

---

## Output Storage

```
project-dir/
└── spec/
    ├── raw_requirements.md  (already exists)
    └── spec_v1.md           (output of this step)
```
