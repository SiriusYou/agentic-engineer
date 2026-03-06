# Template 01 — Inspiration Capture (灵感整理)
# Purpose: Organize raw ideas (voice transcripts / codebase exploration) into structured requirements text
# Conversation: Any AI (Claude / Gemini both work)
# New conversation required: No, reusable

---

## Steps

1. Start a new conversation
2. Choose the appropriate Prompt template based on your input source (A or B)
3. Save the output as `raw_requirements.md`

---

## Prompt A — Voice Transcript Input

Use when: You have scattered ideas from voice recording tools like WisprFlow

```
I have a raw voice transcript of ideas about a product/feature. The content is fairly scattered.
Please organize it into structured requirements text. Do not add anything I didn't mention,
and do not remove any ideas I did mention — only restructure.

Format the output as follows:
1. Core objective (what problem does this product/feature solve)
2. Target users (who will use it)
3. Core feature list (use "Users can..." phrasing)
4. Known constraints (technical, time, budget limitations, etc.)
5. Known risks (concerns or uncertainties I mentioned)
6. Explicit non-goals (boundaries I mentioned)

Raw ideas:
[Paste WisprFlow transcript here]
```

## Prompt B — Codebase Exploration Input

Use when: You've analyzed an existing project and want to add a new feature to it

```
I've analyzed an existing project's codebase and want to add a new feature to it.
Below is the project overview and feature idea. Please organize it into structured requirements text.
Do not add anything I didn't mention, and do not remove any ideas I did mention — only restructure.

Format the output as follows:
1. Core objective (what problem does this feature solve)
2. Target users (who will use it)
3. Core feature list (use "Users can..." phrasing)
4. Known constraints (target project's tech stack, architectural constraints, etc.)
5. Known risks (concerns or uncertainties I mentioned)
6. Explicit non-goals (boundaries I mentioned)

Project overview and feature idea:
[Paste codebase analysis results and feature ideas here]
```

---

## Completion Criteria

The output is ready for Phase 2 when:
- [ ] Core objective can be stated in one sentence
- [ ] Core feature list has 3 or more items
- [ ] No critical decisions left as "TBD"

---

## Output Storage

Save the organized output as:
```
project-dir/
└── spec/
    └── raw_requirements.md
```
