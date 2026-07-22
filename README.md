# mySkillsPublic

A pack of Claude Code skills that encode only the delta a frontier model will not produce on its own, and that the well-known skills do not already cover.
Every skill is research-backed, adversarially verified, and ships with its own evals and fixtures.

## Skills

Each skill names the familiar approach it starts from and earns its place by going past it.

**[adversarial-verify](adversarial-verify/).**
Where the usual verify-and-review skills like verification-before-completion and requesting-code-review check the work cooperatively, this runs a blind subagent that must re-derive the answer on its own and actively try to refute each claim, so agreement is earned rather than rubber-stamped.
It is built to catch the hallucinated citation, the stale fact, and the overconfident claim that a skim waves through.

**[fix-issue](fix-issue/).**
Where the well-known systematic-debugging approach works a single line of investigation at a time, this reproduces the bug the way a user hits it first, then escalates contested or multi-component bugs to a competing-hypotheses subagent swarm so it never anchors on the first plausible cause.
It fixes bugs in your own project, unlike Claude Code's built-in /debug, which debugs the CLI itself.

**[statistician](statistician/).**
Where the data-scientist and EDA skills run the analysis you ask for, this gates the analysis on the mistakes LLMs reliably make, catching silent join fan-out, Simpson's paradox, uncorrected multiple testing, and leakage, and it picks each test from its own assumption checks rather than naming the test first.
It ships real scripts that replace judgment instead of narrating a method.

**[productionize](productionize/).**
Where a code audit or security review reads the source for correctness and security, this targets the operational failure modes that surface only under real traffic, like retry amplification across layers, liveness probes that ping the database, lock-queue-blocking migrations, and exit-now SIGTERM handlers.
It then writes runbooks, alert thresholds, and rollback triggers wired to the real code, and routes source security back to code-audit rather than duplicating it.

**[cost-optimizer](cost-optimizer/).**
Where billing tools need a cloud account to report what you already spent, this reads code, IaC, and config statically and finds dollar-quantified waste before you deploy, including retry-storm math, NAT-egress topology, unbounded-agent-loop token cost, and warehouse scan cost.
It quantifies and fixes, and leaves live billing reconciliation to the tools that hold an account.

**[better-tools](better-tools/).**
Where a dependency bot bumps a package to its next version, this recommends the genuinely better library or successor, consolidates overlapping dependencies, and modernizes what is abandoned or EOL, with every recommendation grounded in a live registry and health check rather than model memory, so it never proposes a package that is hallucinated or dead.
It proposes with a re-runnable verification recipe and leaves the migration to a human.

**[revamp-ui](revamp-ui/).**
Where a design skill applies taste directly and hopes you like the result, this runs a one-round interview to set numeric dials for spectacle versus simplicity, writes a persisted design contract, builds against both floors and ceilings, then screenshot-scores the delivered intensity back against that contract.
The taste target is made explicit and measured rather than assumed.

**[skill-sourcer](skill-sourcer/).**
Where Anthropic's skill-creator authors a new skill and a registry ranks candidates by popularity, this finds the best existing skill for your actual need, ranks it on relevance and safety rather than stars, and gates every candidate through a static scan for pipe-to-shell, credential exfiltration, destructive commands, and prompt injection.
An opt-in sandbox trial measures whether a skill actually helps, and it never clears one as safe.

**[microworld](microworld/).**
This one has no close famous ancestor.
Where an explainer narrates what code does or simulates it, this turns a real Python path or commit into a prediction-first playable artifact built from real execution traces, where you predict before you see and every displayed number comes from a real trace rather than a simulation, closed by a comprehension gate.
It is for grasping what an AI-written diff actually does at runtime, not what its tests claim.

## Install

Drop a skill folder into `~/.claude/skills/` (personal) or `.claude/skills/` (project), or install the repo as a plugin.
Claude loads a skill by its `SKILL.md`, and triggers it from the description when a matching task comes up.

## How these are built

Every skill follows a shared discipline, documented in [docs/specs/](docs/specs/):

- **evidence-protocol** gives all skills one assertion-ledger format, so a skill can audit another skill's output.
- **No skill ships without an eval.** Each skill folder carries `evals/` with fixtures and expected outcomes, designed to reward real capability without punishing creative divergence.
- Findings and citations are verified against primary sources, and each skill encodes only what a frontier model will not already do unprompted.

## CLAUDE.md

[CLAUDE.md](CLAUDE.md) holds the authoring conventions these skills follow (writing style, planning with tradeoffs, asking clarifying questions when confidence is low).

## License

[MIT](LICENSE). Use, modify, and redistribute freely.
