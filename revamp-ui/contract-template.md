# contract-template.md

The template Phase 2 fills in and writes as `DESIGN-CONTRACT.md` into the target repo.
Keep it terse (a few hundred tokens): specific bans plus concrete alternatives, not prose.
It is persisted, re-read at the top of every later phase, user-editable (a hand-edited dial wins), and it updates the cross-project taste profile on completion.
Copy the structure below, replace every `<...>`, and delete this header block.

---

# DESIGN-CONTRACT: <project or page name>

_Revamp of an existing interface. Generated <date>. Edit any dial and it wins over the inferred value._

## Dials

| id | dial | value (1-10) | source | notes |
|---|---|---|---|---|
| D1 | master (spectacle<->simplicity) | <n> | interview / inferred | <interview scene chosen> |
| D2 | 3D | none / accent / core | interview / inferred | <why> |
| D3 | motion | <n> or "same as master" | interview / inferred | <divergence, if any> |
| D4 | density | <n> or "same as master" | interview / inferred | <divergence, if any> |

## Aesthetic family and signature

- **Family:** <named aesthetic direction, e.g. "editorial-restrained", "kinetic-brutalist">
- **Signature element (exactly one):** <the single memorable moment this design is known for>

## LOCKED (restyle allowed, remove/restructure NOT)

The anti-greenfield contract. Later phases may restyle these but must not drop or reorder them.

- **Brand colors:** <the palette that stays>
- **Working components kept:** <list from Phase 0 inventory>
- **Information architecture:** <the nav/page structure that stays>
- **SEO surface:** URLs <...>, heading semantics (`h1`/`h2` outline) <...>, meta <...>, structured data <...>

## Owner-vs-audience resolution

- **Audience:** <who the real users are>
- **Tension (if any):** <where owner taste conflicts with audience reality>
- **Resolution:** <what was decided and why>

## Banned slop defaults (with the alternative to use instead)

Name each and its concrete replacement. Anything from `gates.md`'s slop list NOT banned here is sanctioned for this brief (so the detector only counts the banned ones).

- <banned pattern> -> <concrete alternative>
- <banned pattern> -> <concrete alternative>
- <banned pattern> -> <concrete alternative>

## Performance budget (scales inversely with the dials; hard ceiling regardless)

- **LCP:** <= <target> s
- **CLS:** <= <target>
- **INP:** <= <target> ms
- **Bundle / weight posture:** <e.g. "strict, near-static" or "relaxed for motion, still capped">

## Degradation contract (first-class, tiered)

What each user actually gets. A spectacle that collapses to nothing for a reduced-motion user is a broken contract, not a graceful one.

| tier | what this user gets |
|---|---|
| Full | <the complete experience> |
| Reduced-motion (`prefers-reduced-motion`) | <static-but-complete equivalent, not an empty page> |
| No-JS / static | <server-rendered baseline that still works> |
| Low-end mobile | <what is trimmed and what is guaranteed> |

## Ledger

`D` rows persist in the repo's `.evidence/` ledger (evidence-protocol.md) so they survive compaction and can be audited by adversarial-verify.
Each dial and each locked commitment is an assertion; Phase 5's per-section scores update these rows from `proposed` to `verified` (delivered intensity matched the dial) or `refuted` (it missed).

| id | assertion | status | evidence | expiry | risk |
|---|---|---|---|---|---|
| D1 | master dial = <n>; delivered spectacle matches per-section | proposed | <Phase 5 scores> | stable | high |
| D3 | motion dial = <n>; floors met, ceilings respected | proposed | <Phase 5 scores + gates.md rows> | stable | high |
| ... | <one row per dial and per locked commitment> | proposed | | | |
