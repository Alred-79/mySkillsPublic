# Sources: where skills live and how to query each

The discovery surface for Phase 1. Each source below states what it indexes, the exact way to query it, and the one operational caveat that bites if you skip it.
Registries are the primary index; GitHub code search is a bounded supplement. Read this file before issuing calls so you hit the right endpoint and stay inside the GitHub budget.

## Contents

- [Ordering rule](#ordering-rule)
- [Registries (the primary index)](#registries-the-primary-index)
  - [skills.sh via npx skills](#skillssh-via-npx-skills)
  - [claudemarketplaces](#claudemarketplaces)
  - [ClaudePluginHub](#claudepluginhub)
  - [Smithery](#smithery)
- [GitHub code search (bounded supplement)](#github-code-search-bounded-supplement)
- [Curated directories](#curated-directories)
- [Dedupe rules](#dedupe-rules)

---

## Ordering rule

Query the registries first, always. They are curated and indexed, so they are the cheapest wide reach and they carry the provenance fields (owner, stars, last update) that Phase 3 needs. GitHub code search is the supplement that fills the gap for repos no registry has indexed, and it is rate-capped, so it is spent last and sparingly. Do not open with a GitHub sweep - it burns the budget before the cheap sources have run.

Every candidate that survives to Phase 3 must resolve to a concrete `<owner>/<repo>` so existence, freshness, and provenance can be checked. A hit with no resolvable repo is not a candidate; it is a lead to resolve or drop.

---

## Registries (the primary index)

### skills.sh via npx skills

The skills.sh index, reachable from the CLI. This is the first call.

- **Search:** `npx skills find <terms>` - returns matching skills with their `<owner>/<repo>` and a one-line description.
- **Install (Phase 6 only, never here):** `npx skills add <owner>/<repo>` places the repo's `SKILL.md` into the agent skills directory. Discovery never installs; the add command is quoted for Phase 6.
- **Caveat:** the CLI's ranking is its own, and it is not the relevance ranking this skill uses. Treat `npx skills find` as a *discovery* source that produces candidates, and re-rank everything it returns under Phase 4 against the parsed requirements. Never inherit its order as if it were relevance.

### claudemarketplaces

A web directory of Claude Code marketplaces and the skills they list.

- **Query:** fetch the directory and its per-marketplace listings with WebFetch; extract each skill's `<owner>/<repo>`, description, and any freshness or install-count field shown.
- **Caveat:** it aggregates marketplaces, so the same skill appears under several marketplaces. Resolve each to its source repo and dedupe (see below) before counting it as a distinct candidate. Install counts shown here are a popularity signal - carry them for the Phase 4 tiebreaker only, never for the relevance score.

### ClaudePluginHub

A directory of Claude Code plugins and skills.

- **Query:** fetch the hub listing with WebFetch; extract `<owner>/<repo>`, description, and last-updated where shown.
- **Caveat:** hub entries can lag the source repo. The entry is a lead; the source repo is the truth. Phase 3 re-checks existence and freshness against the repo itself, not the hub card.

### Smithery

A registry oriented at MCP servers that also surfaces skills.

- **Query:** search Smithery for skills matching the ask; extract the source repo for each.
- **Caveat:** most Smithery entries are MCP servers, which are **out of scope** for this skill (it ranks skills, not servers). Filter to actual agent skills, and if the user's real need is a server, say so and point them at the registry rather than forcing a skill.

---

## GitHub code search (bounded supplement)

GitHub code search finds `SKILL.md` files in repos no registry has indexed. It works, but it is bounded, and the bounds are the whole reason it is a supplement and not the primary firehose.

- **Query:** the REST code search API with `filename:SKILL.md`, narrowed by the ask's terms (for example `filename:SKILL.md sql migration`). Add `in:file` term matches to tighten relevance.
- **The budget, respect it:**
  - **Auth required.** Code search needs an authenticated token; unauthenticated calls are rejected.
  - **~10 requests per minute.** The code search endpoint is rate-limited well below the normal REST limit. Batch terms, do not spray one query per candidate.
  - **1,000 results per query, max.** The API will not page past the first 1,000 matches. A broad `filename:SKILL.md` alone returns far more than that, so the first 1,000 are an arbitrary slice, not the best 1,000. Always narrow with the ask's terms so the slice you can see is the relevant one.
  - **Legacy engine.** The REST search runs the old engine. The modern relevance ranker and the `pathname:` operator are **web-UI only** and are not available through the API, so do not design queries around them.
- **Caveat:** because the result slice is capped and unranked-for-relevance, treat GitHub hits as raw leads that must clear Phase 2's pre-filter and Phase 3's gate like any other. A GitHub hit carries no curation, so its provenance check in Phase 3 matters more, not less.

---

## Curated directories

Human-maintained lists of vetted skills (awesome-lists and similar).

- **Query:** fetch the list with WebFetch; extract `<owner>/<repo>` for each entry.
- **Caveat:** "curated" is not "verified for your ask." Curation raises the prior on quality, but every entry still runs the full Phase 3 gate and Phase 5 scan. A vetted list can still carry an abandoned or since-compromised repo.

---

## Dedupe rules

The same skill surfaces on several indexes, so dedupe before counting candidates or the pre-filter cap is spent on duplicates.

- **Key on the source repo, `<owner>/<repo>`.** One repo is one candidate, no matter how many registries list it. Resolve every listing (marketplace card, hub entry, Smithery result) down to its source repo before comparing.
- **A fork is not the original.** When a fork and its upstream both appear, keep the upstream as the candidate unless the fork is demonstrably the maintained line (upstream archived, fork active). Record which one and why - it feeds the Phase 3 provenance check.
- **Count breadth of listing as a weak signal only.** A skill appearing on many registries is a popularity signal, not a relevance signal. It carries to the Phase 4 tiebreaker at most, never into the relevance score.
- **After dedupe**, each surviving candidate is one row carrying every index it was found on, its resolved source repo, and whatever provenance fields the indexes supplied - the starting receipts Phase 3 verifies against the repo itself.
