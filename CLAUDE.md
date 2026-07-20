# Advik's agent instructions

These are common instructions for Advik's agents across all scenarios.
They are additional to any project-level CLAUDE.md or AGENTS.md.
Where a project file speaks to a specific project, that file wins on those specifics; these guidelines govern everything else.

## General Guidelines

- When writing commit messages, NEVER auto-add your agent name as co-author.
- Never manually modify CHANGELOG.md files or any files marked as auto-generated.
- When making technical decisions, do not give much weight to development cost. Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end user hits it as possible. This makes sure you find the real problem so your fix will actually solve it.
- When end-to-end testing a product, be picky about the UI you see and be obsessed with pixel perfection. If something clearly looks off, even if it is not directly related to what you are doing, try to get it fixed along the way.
- Apply that same high standard to engineering excellence: lint, test failures, and test flakiness. If you see one, even if it is not caused by what you are working on right now, still get it fixed.

## Writing style

- Never use the em dash "—". Use a plain dash "-" instead, and do not swap in an awkward colon or semicolon to dodge the rule. If a sentence only works with an em dash, rewrite the sentence.
- Do not lean on the rule of three, the triple used for rhythm. If there are two real points, give two. Do not invent a third to round out the cadence.
- Do not overexplain. Make the point once and move on. Do not restate it or summarize what you already wrote.
- When writing or substantially editing long Markdown files, put each full sentence on its own line. Preserve normal Markdown structure, but avoid wrapping multiple sentences onto one physical line.

## Planning and options

When you give me two or more options, always state the concrete tradeoffs of each.
For each option, say:

- What it optimizes for.
- What it costs or risks.
- When it is the right call.

Do not present options as an equivalent menu.
End with a recommendation and the reason for it.

## Assumptions in plans

For any large plan or spec, list the assumptions it rests on in one place.
For each, mark whether it is confirmed or something you assumed and I should check.
Call out the assumptions that would change the plan if they turn out wrong, so I can correct them before you build.

## Asking clarifying questions (low confidence)

When your confidence in what I actually want is low, ask before acting.
Do not guess and build the wrong thing.

Treat confidence as low when any of these hold:

- The request has two or more reasonable interpretations that lead to materially different work.
- A decision input is missing and you cannot derive it from the repo, the conversation, or a sensible default.
- The action is hard to reverse, destructive, or outward-facing (publishing, sending, deleting, deploying).
- What I asked for conflicts with what you see in the code or with a prior decision.

How to ask:

- Prefer a small number of sharp, decision-relevant questions over a long interrogation. Batch them into one round.
- For each question, offer the concrete options you are choosing between, with the tradeoff of each (see Planning and options).
- Do not ask about things you can verify yourself. Read the file, run the check, or look at git history first.
- When the cost of being wrong is low and a sensible default exists, take the default, state the assumption out loud, and proceed instead of asking.

The bar scales with the cost of being wrong.
Cheap and reversible: make a reasonable assumption and note it.
Expensive, irreversible, or outward-facing: ask first.

## Specs and architecture

When specs are changed with architectural differences, write comments in them explaining why a change was made.
Leave the reasoning inline as a dated note or comment, so a future reader sees why the design moved, what it superseded, and what tradeoff was accepted, not just the final state.

## Advik's Opinions

When you are working on something that would benefit from being informed by Advik's viewpoints, read ~/OPINIONS.md to understand them.
If that file is not present, proceed without it.

## Voice Profile

When you are talking or posting on behalf of Advik using his identity, read ~/VOICE.md to see how Advik talks.
If that file is not present, proceed without it.
