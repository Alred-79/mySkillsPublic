# Operational artifact templates

Templates for the Phase 3 deliverables: runbooks, alert definitions, rollback triggers.
Generate these **from the audited code**, not by filling in placeholders with plausible-sounding values.
Every command, dependency name, metric, and threshold must trace to a `P` ledger row (file:line or command output); see the provenance gate at the bottom. An artifact that cites something the code does not contain is worse than no artifact, because it will be trusted during an incident.

## Contents

- [Runbook template](#runbook-template)
- [Alert-definition template](#alert-definition-template)
- [Rollback-trigger template](#rollback-trigger-template)
- [Provenance gate](#provenance-gate)

---

## Runbook template

Generate one runbook per failure scenario the tier calls for. At `standard`, cover at least: won't-start, a key-dependency-down, and rollback. Fill every bracket from the audit; if a value has no `P`-row source, do not invent it. Mark it `UNKNOWN (no source)` and flag it.

```markdown
# Runbook: <scenario, e.g. "Payments API will not start">

**Service:** <service name from the repo>
**Tier:** <experimental | standard | critical>
**Owner / on-call:** <from config or CODEOWNERS; UNKNOWN if absent>

## Symptoms
- <what the operator sees: alert name, error string, dashboard signal - each traceable>

## Likely causes (most to least common)
1. <cause> - evidence: <P-row: file:line or command output>
2. ...

## Diagnosis
Run these, in order. Each command is real and was checked at generation time.
- `<command>`; expected healthy output: `<...>`; failure looks like: `<...>`
- ...

## Resolution
1. <step with the exact command>
2. ...

## If resolution fails
- Escalate to: <owner>
- Rollback trigger for this scenario: <link to the rollback-trigger doc>
```

## Alert-definition template

One row per alert. Every threshold must be tied to a limit the audit actually established (pool size, `max_connections`, replication lag bound, cert-expiry window), not a round number picked for looking reasonable.

```markdown
# Alerts: <service>

| Alert | Condition (metric + threshold) | Threshold source (P-row) | Why this number | Runbook |
|---|---|---|---|---|
| Pool near exhaustion | active_connections / pool_size > 0.9 for 2m | B9 audit: pool_size=<n> at <file:line> | headroom before acquisition-timeout errors | <link> |
| Replication lag high | replica_lag_seconds > <n> | B8 audit: WAL bound at <file:line> | slot backpressure before disk pressure | <link> |
| Cert expiring | days_to_expiry < 30 | B11 inventory: cert <name>, expiry <date> | renewal lead time | <link> |
```

Rules:
- No alert on a metric the service does not emit. If the metric is aspirational, the fix is to emit it (B13), not to alert on a ghost.
- A threshold with no audited source is a finding, not an alert.

## Rollback-trigger template

The point of a rollback trigger is that the decision is made **before** deploy, in a calm moment, not argued during the incident. Each trigger is a precommitted "if X within Y, roll back."

```markdown
# Rollback triggers: <release / change>

**Deploy vs release:** <are these separable via flags? at `critical`, this must be answered>

| Trigger (observable) | Window | Action | Who can pull it |
|---|---|---|---|
| Error rate > <baseline + n%> | 10 min post-deploy | automatic rollback | on-call, no approval needed |
| p99 latency > <audited limit> | 10 min | roll back | on-call |
| <migration> lock held > 2s | during migration | abort migration (lock_timeout fires) | automatic |

**Pre-committed:** these are agreed now. During the incident, you execute; you do not deliberate.
```

At `critical` tier, also produce migration-rollback rehearsal steps (the exact expand-contract reversal for each risky migration) and record the deploy≠release separation as a `P` row.

---

## Provenance gate

Deterministic, run at generation time, before any artifact ships:

1. **Tokenize** every command, unit/service name, metric name, and numeric threshold in each generated artifact.
2. **Require a citation** for each: a `P` ledger row pointing at a file:line or a captured command output. Grep the artifacts for command and metric tokens; any token without a backing `P` row is flagged.
3. **Dry-run where safe** as additional evidence: `--help`, `-n`/`--dry-run`, `--syntax-check`, `systemctl cat <unit>` to confirm the unit exists. Capture the output into the citing `P` row.
4. **Fail closed.** A runbook that references a nonexistent systemd unit, or an alert on a never-emitted metric, must be impossible to ship silently; it blocks until the token is either sourced or removed.

This gate is what separates a generated-from-code artifact from a plausible-looking template. Plausible is the failure mode; sourced is the bar.
