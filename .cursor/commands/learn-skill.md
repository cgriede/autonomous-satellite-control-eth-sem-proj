# Learn skill

Read and follow **`.cursor/skills/learn-skill/SKILL.md`** end to end.

## General rule

| User input | Primary source |
|------------|----------------|
| **Specific topic** after `/learn-skill` (e.g. "backlog xlsx", "forgot to ask") | Search the conversation for that match |
| **Bare** `/learn-skill` | The **three latest messages** (user + assistant) for breakthroughs and anti-patterns |

Then: pending rows in **`.cursor/memory/learnings.md`**.

## Steps

1. Collect learnings per the general rule above.
2. Append any **new** learning to `learnings.md` before editing other files.
3. Sweep **every** `.cursor/skills/**/SKILL.md` and **every** `.cursor/rules/*.mdc` — rubric in `learn-skill/reference.md`; no silent skips.
4. Apply minimal UPDATE / POINTER edits; mark learnings `applied` with `Applied to` filled in.
5. Reply with the **Learn-skill summary** template from the skill (include **Context used**).

Do not commit unless asked.
