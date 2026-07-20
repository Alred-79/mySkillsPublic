# Phase 1 - Data audit (STRATOS IDA discipline)

The purpose of Phase 1 is to know what the data actually is before you compute anything on it. Initial Data Analysis (IDA) is the discipline of examining structure, quality, and cleaning consequences *separately from* answering the research question. The signature failure this phase prevents is the silent join fan-out - a merge that quietly multiplies rows and inflates every downstream count - together with silent type coercion and the day/month date swap.

Route through installed skills under the hybrid rule: `programmatic-eda` for profiling, `data-quality-audit` for validators. If neither is installed, the gates below are the procedure.

## Gates

| Gate | Requirement | The failure it prevents |
|---|---|---|
| **Per-step evidence printing** | After every load and transform, print: dtypes, null counts per column, row-count before/after, min/max of every date column, and a sample of rows. | Blind transforms hide their own damage. A row count that changed when you did not expect it is the whole bug, visible for free. |
| **Join audit on every merge** | Run `join_audit.py` (or the SQL equivalent) on **every** join: pre/post row counts, key uniqueness on both sides, dtype match on the keys, and a grain assertion. | Fan-out. If the right-side key is not unique, a left join multiplies rows and every sum, mean, and count afterward is wrong while looking plausible. This is the highest-frequency silent corruption in the pipeline. |
| **Day/month swap check** | For every date column, verify the parse against known-good anchors and check whether any day value exceeds 12 (proving DD/MM vs MM/DD). | `01/02/2024` is two different dates. A locale-flipped parse silently shifts a third of your rows and corrupts any time analysis. |
| **No silent coercion** | Never let a type coerce silently. Numbers arriving as strings, `"N/A"` becoming NaN, mixed types in a column - surface each and decide explicitly. | Silent `to_numeric(errors="coerce")` turns unparseable values into nulls you never see, changing every aggregate. |
| **Missing-data handling (per tier)** | quick-look: flag only. decision-grade: diagnose the mechanism (MCAR / MAR / MNAR) and multiply-impute if MAR. high-stakes: add an MNAR sensitivity analysis. See `references/missing-data-mechanisms.md`. | Dropping rows with missingness that is not MCAR biases the result. "Complete-case by default" is a silent, common error. |
| **IDA cleaning note** | Record every cleaning action that could change an interpretation (rows dropped and why, values recoded, outliers touched). | Cleaning is analysis. An undocumented filter is an unreproducible, unauditable decision baked into the result. |

## SQL-source variant

When the source is a database, the same gates hold but expressed in SQL:

- **Profile before you query for answers.** Read the schema and data dictionary first. Run `COUNT(*)`, `COUNT(DISTINCT key)`, null counts, and min/max per column as profiling queries before writing any analysis SQL. (Spider 2.0: real-schema text-to-SQL accuracy collapses to ~10% without this.)
- **Join audits as row-count assertions.** Before and after each join, assert the row count and the grain: `SELECT COUNT(*)` pre, `SELECT COUNT(*), COUNT(DISTINCT grain_key)` post. A post-join count above the pre-join count on a supposed 1:1 join is fan-out.

## End-of-run: write gotchas

Append any newly confirmed dataset trap to the repo's `data-gotchas.md` (grain, timezone, key duplication, definition quirk), so the next run greps it for free in Phase 0.
