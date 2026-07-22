# The sandboxed trial (`--trial`): a utility probe, reject-only on safety

The full protocol for the opt-in deep mode. The trial runs a candidate in isolation to answer one question: **does it actually help.** That is the point of the trial and the only thing the bake-off ranks on.
It is opt-in because executing untrusted skill code is the riskiest thing in this pack, and this design is the result of a security review that cut the original "detonation is the strong safety gate" claim. Read the whole file before running it.

## The reject-only rule (verbatim, non-negotiable)

> The trial's safety observation is **reject-only**. Observed runtime misbehavior downgrades or rejects a candidate. Behaving well **never** clears a skill, **never** emits a "safe" or "passed" signal, and **never** adds positive weight to the ranking. Safety clearance rests on the static scan plus reputation and provenance plus the human confirm - never on the trial.

Everything below serves that rule. If any step ever reads as "it ran clean, therefore it is safe," the trial has broken its one constraint. Never report, or imply, "we ran it on your code and it is safe." The trial reports whether a skill *helped*, not whether it is safe.

## Contents

- [When it runs](#when-it-runs)
- [1. Synthetic task, never real source or secrets](#1-synthetic-task-never-real-source-or-secrets)
- [2. Named isolation bar, fail-closed against it](#2-named-isolation-bar-fail-closed-against-it)
- [3. Named observation substrate](#3-named-observation-substrate)
- [4. The two asymmetric lenses](#4-the-two-asymmetric-lenses)
- [5. The bake-off](#5-the-bake-off)
- [The trial ceiling](#the-trial-ceiling)
- [Honesty about what ships](#honesty-about-what-ships)

---

## When it runs

Only when the user passes `--trial`, and only after Phase 4 has ranked the candidates. The trial takes the top few by relevance and runs each in its own fresh sandbox. Default mode never reaches this file - it relies on the static-plus-reputation-plus-human path, which needs no sandbox tooling.

---

## 1. Synthetic task, never real source or secrets

Build a task that exercises the **same shape** as the user's need - the same types, the same call-site pattern, a seeded failure like the one the skill is meant to help with - out of **synthetic or redacted** code. The user's real proprietary source never enters the sandbox, and no real secret, token, key, or credential is ever placed there.

The reason is the ceiling below. On any run where a hidden payload slips the static scan and fires in the sandbox, whatever sits in that sandbox is what it can steal. So what sits there must not be worth stealing: a synthetic fixture and dummy values, never the real repo and never a live secret. This is a hard rule, not a default - if a faithful synthetic task cannot be built without real source or a real secret, the trial does not run that candidate.

---

## 2. Named isolation bar, fail-closed against it

Each candidate runs in its own **ephemeral microVM (default) or gVisor sandbox**, torn down after the run. The bar is named on purpose:

- **A plain shared-kernel container is explicitly disallowed for untrusted code.** "Container or VM" is not treated as equivalent - a container shares the host kernel, which is the wrong isolation boundary for code you are assuming is hostile. A bare `docker` being available is **not** sufficient and does not satisfy the bar.
- **Offline: no network.** This removes the exfil path. Stated honestly, it also limits utility-testing of skills whose value is network-dependent - those get a partial or no utility signal, and the report says so rather than pretending the offline run measured them fully.
- **Fail-closed is defined against this bar**, not against "some sandbox exists." If the required microVM/gVisor isolation cannot be established, or the observation substrate (next section) is unavailable, the trial **refuses to run** rather than executing under-isolated or unobserved. Refusing is the correct output; running degraded is not.

---

## 3. Named observation substrate

Runtime behavior is observed through a **concrete syscall or eBPF collector** - a seccomp-BPF / syscall-trace layer or an eBPF tracer that records process exec, file opens outside the declared scratch path, and network-connect attempts. It is not a hand-waved "log the network."

The three behaviors watched for are: **egress attempts**, **file writes outside the task scope**, and **credential or environment access**. Each is a concrete, collectable event, not an inference.

**If the substrate is unavailable, the safety observation is not performed and is not claimed.** The trial does not pretend to have watched. A run with no working collector can still produce a *utility* signal (did the synthetic task get helped), but it produces **no** safety observation at all, and the report states that the run was unobserved rather than implying it was clean. Under the fail-closed rule, a candidate is not trialed for safety without the collector present.

---

## 4. The two asymmetric lenses

The trial looks through two lenses, and they are deliberately asymmetric.

- **Utility - the point.** Did the candidate help the synthetic task, and how much. This is empirical fit evidence, and it is the **only** thing the bake-off ranks on. A candidate that measurably helps the synthetic task ranks above one that does not.
- **Safety - reject-only.** The collector's observations are read for misbehavior. Observed egress, out-of-scope writes, or credential access **downgrades or rejects** the candidate. Behaving well does the opposite of nothing to the ranking: it changes nothing. No "safe" flag is emitted, no "passed" status is recorded, no positive ranking weight is added. Misbehaving always downgrades; behaving well never upgrades.

The asymmetry is the safety model in one line: the trial can move a candidate **down** on observed misbehavior, and can never move it **up** on the absence of it.

---

## 5. The bake-off

With several candidates trialed, the bake-off compares them **on utility only**. Each runs in its own fresh isolated sandbox - no shared state between candidates, so one cannot influence another's result or observation.

The report labels the cost plainly: **N candidates trialed equals N times the residual execution risk.** Running more candidates buys more utility evidence at a linear cost in execution exposure, and the user sees that trade rather than having it hidden. The output ranks the candidates by demonstrated utility and states, for each, that its safety standing still rests on the static scan, reputation, and the human confirm - not on the trial.

---

## The trial ceiling

State this at parity with the static-scan ceiling, every trial run. Runtime detonation catches roughly **87% of malicious skills in the wild** and misses the rest (from the "Cloak and Detonate" evaluation of runtime skill auditing, arXiv 2607.02357; verify the figure at the source before quoting it as precise). The misses are structural, not fixable by trying harder:

- **A payload that does not fire on this task reads as clean.** The synthetic task exercises one shape; a payload gated on a different trigger never runs, so the collector sees nothing.
- **A sandbox-aware payload stays benign.** Code that detects the microVM, the absence of network, or the synthetic fixture can behave itself in the trial and attack only in production. A clean run is exactly what such a payload produces on purpose.
- **Prompt-injection can divert the agent** down a path the collector was not watching.
- **A single run cannot cover adversarially-gated behavior.** One execution is one sample of a program that may behave differently on the next input, the next day, or the next environment.

This is why the trial is reject-only and why it is **not the security boundary**. It is the same stance microworld takes when it disclaims its sandbox as "not the security boundary" and requires human review. A skill that behaves perfectly through an entire trial has earned exactly no safety clearance from it - it still requires the static scan, the reputation and provenance check, and the human confirm, precisely as if no trial had run.

---

## Honesty about what ships

Default mode works today with no external tooling. `--trial` does not: it depends on a real microVM-or-gVisor sandbox and a real syscall/eBPF collector, which are dependencies the user provides in their environment, not a runtime this skill bundles. Without them verified present, the trial fails closed and does not run. Do not claim the trial as an available capability when its substrate is absent - name the missing dependency and fall back to default mode, exactly as microworld records `isolation: NONE` rather than claiming a sandbox it did not establish.
