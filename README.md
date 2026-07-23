# mySkillsPublic

A pack of Claude Code skills for the part of AI work that is actually hard now, trusting it.

The models write the code, the analysis, and the answer. What they will not do unprompted is prove any of it is right or admit what they could not check. Each skill here takes one spot where you would otherwise have to take an AI's word for something and replaces the word with grounded, cited evidence, so you can act on the output without getting burned.

Every skill encodes only the delta a frontier model will not produce on its own, names the well-known skill it improves on, and ships with its own evals and fixtures as proof.

## What makes them different

The gap this pack fills is not a longer prompt, it is what you can rely on afterward.

- **You can act on the output without re-checking it by hand.** Every skill emits an evidence ledger where each claim is tied to a real artifact, a code hunk, a command's output, a registry lookup, or an execution trace. You read a cited finding, not the model's recollection.
- **The skills check each other.** They share one assertion format, so adversarial-verify can audit any other skill's output directly. Verification is the ground the whole pack stands on, not a feature bolted onto one skill.
- **A skill is only as good as its evals.** So every skill ships its own, the seeded fixtures and the gates and a no-skill baseline to score against, in its evals/ folder. It has to beat that baseline to earn its place, it retires itself the day the base model closes the gap, and the evals reward real capability without punishing creative divergence. Each skill below names what its eval seeds and scores.
- **They point at what they could not verify.** An unchecked claim is surfaced as a finding, never smoothed into a confident sentence. What the model cannot confirm is where your risk lives, so the skills put it in front of you.

The shared discipline lives in [docs/specs/](docs/specs/), one evidence-protocol assertion format the skills share, an eval architecture per skill, and every finding checked against a primary source.

## Skills

Each skill names the familiar approach it starts from and earns its place by going past it.

**[adversarial-verify](adversarial-verify/).**
Where the usual verify-and-review skills like verification-before-completion and requesting-code-review check the work cooperatively, this runs a blind subagent that must re-derive the answer on its own and actively try to refute each claim, so agreement is earned rather than rubber-stamped.
It is built to catch the hallucinated citation, the stale fact, and the overconfident claim that a skim waves through.
Its eval seeds a document and a diff with a stale fact, a subtle logic bug, and an overclaim that a rubber-stamp would bless, and scores whether the blind verifier catches them.

**[fix-issue](fix-issue/).**
Where the well-known systematic-debugging approach works a single line of investigation at a time, this reproduces the bug the way a user hits it first, then escalates contested or multi-component bugs to a competing-hypotheses subagent swarm so it never anchors on the first plausible cause.
It fixes bugs in your own project, unlike Claude Code's built-in /debug, which debugs the CLI itself.
Its eval plants a multi-component bug behind a decoy red herring, and scores finding the true root cause and proving the fix holds.

**[statistician](statistician/).**
Where the data-scientist and EDA skills run the analysis you ask for, this gates the analysis on the mistakes LLMs reliably make, catching silent join fan-out, Simpson's paradox, uncorrected multiple testing, and leakage, and it picks each test from its own assumption checks rather than naming the test first.
It ships real scripts that replace judgment instead of narrating a method.
Its eval seeds datasets with the traps LLMs fall for, join fan-out, Simpson's paradox, uncorrected multiple testing, and leakage, and scores catching each while choosing the test from its assumption checks.

**[productionize](productionize/).**
Where a code audit or security review reads the source for correctness and security, this targets the operational failure modes that surface only under real traffic, like retry amplification across layers, liveness probes that ping the database, lock-queue-blocking migrations, and exit-now SIGTERM handlers.
It then writes runbooks, alert thresholds, and rollback triggers wired to the real code, and routes source security back to code-audit rather than duplicating it.
Its eval seeds a service with operational failures like a database-pinging liveness probe, a lock-queue migration, and an exit-now SIGTERM, plus clean decoys, and scores recall and false positives against a no-skill baseline.

**[cost-optimizer](cost-optimizer/).**
Where billing tools need a cloud account to report what you already spent, this reads code, IaC, and config statically and finds dollar-quantified waste before you deploy, including retry-storm math, NAT-egress topology, unbounded-agent-loop token cost, and warehouse scan cost.
It quantifies and fixes, and leaves live billing reconciliation to the tools that hold an account.
Its eval seeds a polyglot app with cost anti-patterns alongside reliability-critical decoys it must not cut, and scores recall, false positives, and a hard fail for any dollar figure lacking a dated rate and a volume assumption.

**[better-tools](better-tools/).**
Where a dependency bot bumps a package to its next version, this recommends the genuinely better library or successor, consolidates overlapping dependencies, and modernizes what is abandoned or EOL, with every recommendation grounded in a live registry and health check rather than model memory, so it never proposes a package that is hallucinated or dead.
It proposes with a re-runnable verification recipe and leaves the migration to a human.
Its eval mixes real swaps with poisoned bait, a permanently-invalid package name, an EOL dependency, and a trendy-but-immature one, and scores catching the real swaps, refusing the bait, and grounding every pick in a live registry check.

**[revamp-ui](revamp-ui/).**
Where a design skill applies taste directly and hopes you like the result, this runs a one-round interview to set numeric dials for spectacle versus simplicity, writes a persisted design contract, builds against both floors and ceilings, then screenshot-scores the delivered intensity back against that contract.
The taste target is made explicit and measured rather than assumed.
Its eval starts from a slop-ridden page carrying the banned AI defaults, and scores hitting the elicited spectacle-versus-simplicity contract, screenshot-checked against its floors and ceilings.

**[skill-sourcer](skill-sourcer/).**
Where Anthropic's skill-creator authors a new skill and a registry ranks candidates by popularity, this finds the best existing skill for your actual need, ranks it on relevance and safety rather than stars, and gates every candidate through a static scan for pipe-to-shell, credential exfiltration, destructive commands, and prompt injection.
An opt-in sandbox trial measures whether a skill actually helps, and it never clears one as safe.
Its eval seeds a skill pool with one right answer amid an abandoned skill, a hallucinated repo, a typosquatted owner, and four malicious skills, and scores ranking by relevance and safety while never clearing a malicious one, including the sandbox-aware skill that behaves during a trial.

**[explain-changes](explain-changes/).**
Where the built-in commit and PR drafters and the paid PR bots summarize the diff and restate your intent, this explains the change at ship time grounded strictly in the real diff and a real test run, scopes the true blast radius across the repo including the call sites it does not touch, and flags what it could not verify instead of smoothing it over.
It explains and de-risks the change you are shipping, where microworld is for deeply inhabiting a path and code-review is for hunting defects.
Its eval seeds a change with a subtly false commit claim and a caller a grep misses, and scores grounding every line in the diff or a real run. A paired trial named the honest limit, on a frontier model with a small diff the delta is discipline rather than catch-rate, which shows on weaker tiers or larger changes.

**[microworld](microworld/).**
This one has no close famous ancestor.
Where an explainer narrates what code does or simulates it, this turns a real Python path or commit into a prediction-first playable artifact built from real execution traces, where you predict before you see and every displayed number comes from a real trace rather than a simulation, closed by a comprehension gate.
It is the deep tier you escalate to from explain-changes when a brief is not enough and you want to watch the code run, grounded in what actually executed rather than what the tests claim.
Its eval seeds a Python repo with a surprising behavior next to a nondeterministic decoy that must fail capture, and scores grounding every value in a real deterministic trace and rejecting what it cannot capture.

explain-changes, microworld, and adversarial-verify form one pipeline. explain-changes briefs any change you ship, microworld lets you inhabit the ones worth a closer look, and adversarial-verify blind-audits the claims of either, so the deeper you go the harder the check.

## Install

Drop a skill folder into `~/.claude/skills/` (personal) or `.claude/skills/` (project), or install the repo as a plugin.
Claude loads a skill by its `SKILL.md`, and triggers it from the description when a matching task comes up.

## CLAUDE.md

[CLAUDE.md](CLAUDE.md) holds the authoring conventions these skills follow (writing style, planning with tradeoffs, asking clarifying questions when confidence is low).

## License

[MIT](LICENSE). Use, modify, and redistribute freely.
