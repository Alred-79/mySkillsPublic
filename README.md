# mySkillsPublic

A pack of Claude Code skills that encode only the delta a frontier model will not produce on its own.
Each skill is research-backed, adversarially verified, and ships with its own evals and fixtures.

## Skills

| Skill | What it does |
|---|---|
| [adversarial-verify](adversarial-verify/) | Stress-test or red-team a previous agent's output with a blind verifier subagent that must re-derive and try to refute each claim, not skim and agree. |
| [fix-issue](fix-issue/) | Debug a reported bug end to end: reproduce, find the true root cause, patch, prove the fix holds. Escalates hard bugs to a competing-hypotheses swarm so it does not anchor on the first plausible cause. |
| [revamp-ui](revamp-ui/) | Complete UI revamp of an existing site, conditioned on a one-round interview about your tolerance for spectacle vs simplicity, then scored back against the contract. |
| [statistician](statistician/) | Rigorous EDA and inference with gates that catch the mistakes LLMs reliably make (applicability errors, silent join fan-out, Simpson's paradox, uncorrected multiple testing, leakage). Ships real scripts that replace judgment. |
| [productionize](productionize/) | Take a working codebase to production-grade: audit for the operational failure modes frontier LLMs miss, apply fixes, generate runbooks and rollback triggers. |
| [cost-optimizer](cost-optimizer/) | Read code, IaC, and config statically and find dollar-quantified cost waste across cloud, LLM, runtime, and data, then fix and estimate. |
| [better-tools](better-tools/) | Scan a whole app and recommend genuinely better libraries and tooling, with every recommendation grounded in a live registry and health check rather than model memory. |
| [microworld](microworld/) | Turn a real Python code path or commit into a validated, prediction-first, playable learning artifact so a human can understand what AI-written code actually does. Every displayed value comes from a real trace, never a simulation. |

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
