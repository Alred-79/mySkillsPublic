# Registries: per-language existence + health endpoints

The exact live API calls that ground gates 1 (existence) and 2 (freshness/health) in `guardrails.md`.
SKILL.md Phase 2 reads this file before issuing a call, so the right endpoint is hit and the right field is read.
Every endpoint below is public HTTP; hit it with Bash (`curl`) or WebFetch. No API key is required for the calls listed.

## Contents

- [Citation-hygiene rule](#citation-hygiene-rule)
- [The four distinct not-found signals](#the-four-distinct-not-found-signals)
- [Existence endpoints (gate 1)](#existence-endpoints-gate-1)
  - [npm](#npm)
  - [PyPI](#pypi)
  - [crates.io](#cratesio)
  - [Go (pkg.go.dev + module proxy)](#go-pkggodev--module-proxy)
  - [Maven Central](#maven-central)
- [Health endpoints (gate 2)](#health-endpoints-gate-2)
  - [deps.dev](#depsdev)
  - [OpenSSF Scorecard](#openssf-scorecard)
  - [ecosyste.ms](#ecosystems)
  - [Socket](#socket)

---

## Citation-hygiene rule

Every maintenance, health, or adoption claim shown to the user cites the live source it came from, with the access date and the observed value. Never assert a package's status from model memory - that memory is the staleness bug (SKILL.md, "model memory is stale by construction"). If a live call cannot be run, the claim is `unverifiable` (a finding, never a pass), and per gate 1 an existence-unverifiable *name* is suppressed, not shown.

A citation is not a URL. It is the URL plus the field and value you read: "`https://api.deps.dev/v3/systems/npm/packages/left-pad` -> latest version 1.3.0, published 2018-... (fetched 2026-07-20)". A bare URL with no observed value is a ghost citation and does not satisfy this rule.

---

## The four distinct not-found signals

The single most important operational fact in this file: **"the package does not exist" looks different on each registry.** A recommender that only knows how to read a 404 will mis-read Maven's "found nothing" (which is a 200) as "exists" and leak a hallucination. Handle all four:

| Signal | Where | How to read it |
|---|---|---|
| **HTTP 404** | npm, PyPI, crates.io, pkg.go.dev, Go proxy, deps.dev | Non-existent name returns 404. A 200 with a body is existence. |
| **`numFound: 0`** | Maven Central (Solr search) | The request returns **HTTP 200** with `response.numFound == 0`. The status code is useless here; you must parse the JSON and read `numFound`. `numFound >= 1` is existence. |
| **Empty version list** | Go module proxy `@v/list` | A module *path* can resolve while having no tagged versions: the `@v/list` endpoint returns 200 with an **empty body**. Treat "resolves but zero versions" as not-usable (nothing to depend on), distinct from a 404. |
| **Any non-200 that isn't a clean 404** | all (rate-limit 429, 5xx, timeout) | This is NOT a not-found. It is *unverified*. Do not read it as "does not exist" and do not read it as "exists." Per gate 1, if you cannot get a clean answer, suppress the name and report the registry as unreachable. |

The asymmetry that matters: a 404 is positive evidence of non-existence (suppress the name outright). A non-200-non-404 is absence of evidence (suppress the name for this run and say the registry was unreachable). Never collapse the second into "exists."

---

## Existence endpoints (gate 1)

For each: the call, the existence signal, and the not-found signal. All verified live 2026-07-20.

### npm

- **Call:** `GET https://registry.npmjs.org/<package>`
- **Exists:** HTTP 200 with a JSON body (has `dist-tags`, `versions`).
- **Not found:** HTTP 404.
- Scoped packages: URL-encode the slash, `@scope/name` -> `@scope%2Fname`.

### PyPI

- **Call:** `GET https://pypi.org/pypi/<package>/json`
- **Exists:** HTTP 200 with `info` and `releases`.
- **Not found:** HTTP 404.
- Name normalization matters: PyPI treats `-`, `_`, and `.` as equivalent and lowercases. Query the normalized name; a "not found" on a weird-cased name may just be normalization, so retry normalized before concluding non-existence.

### crates.io

- **Call:** `GET https://crates.io/api/v1/crates/<crate>`
- **Exists:** HTTP 200 with a `crate` object.
- **Not found:** HTTP 404.
- crates.io asks for a descriptive `User-Agent`; set one (`-A "better-tools-skill (contact)"`) or the request may be rejected.

### Go (pkg.go.dev + module proxy)

Two complementary checks; the proxy is the authoritative one.

- **Human page:** `GET https://pkg.go.dev/<module-path>` - 200 exists, 404 not found. Good for a quick check, but pages can lag.
- **Authoritative - module proxy version list:** `GET https://proxy.golang.org/<module-path>/@v/list`
  - **Exists with usable versions:** HTTP 200 with a newline-separated list of versions in the body.
  - **Path resolves, no tagged versions:** HTTP 200 with an **empty body** (the "empty version list" signal - real path, nothing to pin).
  - **Not found:** HTTP 404.
  - Module paths are case-encoded (uppercase letters become `!` + lowercase); for typical lowercase paths this is a non-issue.

### Maven Central

- **Call:** `GET https://search.maven.org/solrsearch/select?q=g:<groupId>+AND+a:<artifactId>&rows=1&wt=json`
- **Exists:** HTTP 200 with `response.numFound >= 1`.
- **Not found:** HTTP 200 with **`response.numFound == 0`** (this is the `numFound:0` signal - the status code is 200 either way, so you MUST parse the JSON).
- Both `groupId` and `artifactId` are required to disambiguate; a group-only query finds many artifacts and does not confirm the specific one you mean.

---

## Health endpoints (gate 2)

Once a name has passed gate 1, these establish whether it is alive. Capture the observed value (last-release date, archived flag, dependents count) - it is the receipt Phase 3 carries and adversarial-verify re-checks.

### deps.dev

Google's cross-ecosystem dependency graph. Systems: `npm`, `pypi`, `cargo`, `go`, `maven`, `nuget`.

- **Package:** `GET https://api.deps.dev/v3/systems/<system>/packages/<name>` - returns the `versions` array (read the latest and its `publishedAt`), default version, and links.
- **Version detail (incl. OpenSSF Scorecard):** `GET https://api.deps.dev/v3/systems/<system>/packages/<name>/versions/<version>` - includes `advisoryKeys`, license, and a `projects` link that carries the Scorecard result.
- **Not found:** HTTP 404.
- Maven names use `<groupId>:<artifactId>` as `<name>` (URL-encode the colon).

### OpenSSF Scorecard

Automated repository health and security-practice score (0-10) over checks like Maintained, Code-Review, Branch-Protection, Dangerous-Workflow.

- **Via deps.dev:** the version-detail `projects` link above returns the Scorecard result inline - preferred, one fewer call.
- **Direct:** `GET https://api.securityscorecards.dev/projects/github.com/<owner>/<repo>` - returns `score` and per-`check` scores with reasons.
- Use the **Maintained** check and the overall score for the freshness decision; low Maintained is a strong abandonment signal. Cite the specific check score, not just the composite.

### ecosyste.ms

Broad, free package metadata across dozens of registries - the best single source for the freshness fields.

- **Package:** `GET https://packages.ecosyste.ms/api/v1/registries/<registry-host>/packages/<name>`
  - Registry hosts: `npmjs.org`, `pypi.org`, `crates.io`, `proxy.golang.org`, `repo1.maven.org`.
  - **Read:** `latest_release_published_at` (staleness), `status` (e.g. a deprecation/removal status when set), `dependent_packages_count` and `dependent_repos_count` (adoption, feeds gate 6), and the repository `archived` flag where present.
- A `latest_release_published_at` years in the past, a non-null removal/deprecation `status`, or `archived: true` each fail or flag gate 2. Quote the value and its date.

### Socket

Behavioral supply-chain risk (install scripts, obfuscation, network access, capability changes) - risk signals the other sources do not model.

- **Package score:** `GET https://api.socket.dev/v0/npm/<name>/<version>/score` (npm; other ecosystems via their API) - returns supply-chain, maintenance, and quality sub-scores.
- Socket's free API requires an API key for most endpoints. If no key is configured, **skip Socket and record it as an un-run check** (an `unverifiable` note on that dimension) rather than asserting a clean bill from its absence. The deps.dev + Scorecard + ecosyste.ms trio already covers existence, maintenance, and adoption; Socket adds behavioral risk on top and is not a prerequisite.
