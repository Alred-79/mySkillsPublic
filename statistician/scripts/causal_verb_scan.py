#!/usr/bin/env python3
"""causal_verb_scan.py - flag causal verbs in a draft that lack a declared identification strategy.

Observational correlation does not earn "causes". Causal language slips into prose even when the
analysis was careful, so this greps a report draft for causal verbs and flags each one unless the
draft also declares an identification strategy that would license causal claims (a randomized
experiment, diff-in-diff, RDD, IV, or a controlled design with a stated DAG).

Behavior:
  - If NO identification strategy phrase is found in the draft, every causal-verb hit is flagged.
  - If a strategy IS declared, hits are reported as 'review' (the strategy may or may not cover
    that specific sentence - a human judges), and the exit code stays 0.
This asymmetry is deliberate: the common failure is a causal claim with no strategy at all, and
that case is caught hard.

CLI:
  python causal_verb_scan.py report.md
  python causal_verb_scan.py report.md --list      # just print the verb/strategy lists

Exit code is non-zero when causal verbs are found with no declared strategy.
Deps: none (Python standard library only). Verb and strategy lists mirror
references/causal-verb-list.md.
"""
from __future__ import annotations

import argparse
import re
import sys

CAUSAL_VERBS = [
    r"drives?", r"driver of", r"driven by",
    r"causes?", r"caused by", r"causal",
    r"leads? to", r"led to",
    r"results? in", r"resulting in",
    r"because of", r"due to",
    r"impact of", r"effect of", r"effects? on",
    r"influences?", r"influenced by",
    r"makes? .{0,20}(happen|increase|decrease|rise|fall|go up|go down)",
    r"(increase|decrease|raise|lower|boost|reduce)(?:s|d|ed)?\b",  # present or past: X moves Y
]

# Phrases that indicate a genuine identification strategy is in play.
STRATEGY_PHRASES = [
    r"random(ly)? assign", r"randomi[sz]ed", r"\bA/?B test\b", r"\bRCT\b",
    r"difference[- ]in[- ]difference", r"\bdiff[- ]in[- ]diff\b", r"\bDiD\b",
    r"regression discontinuity", r"\bRDD?\b",
    r"instrumental variable", r"\binstrument\b", r"\bIV\b",
    r"\bDAG\b", r"backdoor", r"causal (graph|diagram|identification)",
    r"identification strategy", r"natural experiment",
]


def scan(text):
    lines = text.splitlines()
    strat_found = []
    for pat in STRATEGY_PHRASES:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            strat_found.append(m.group(0))
    has_strategy = len(strat_found) > 0

    hits = []
    for i, line in enumerate(lines, 1):
        for pat in CAUSAL_VERBS:
            for m in re.finditer(pat, line, flags=re.IGNORECASE):
                hits.append((i, m.group(0), line.strip()))
    return hits, has_strategy, sorted(set(strat_found))


def report(hits, has_strategy, strat_found):
    print("=" * 72)
    print("CAUSAL-VERB SCAN")
    print("=" * 72)
    if has_strategy:
        print(f"  identification strategy declared: yes  ({', '.join(strat_found)})")
    else:
        print("  identification strategy declared: NO")
    print(f"  causal-verb occurrences: {len(hits)}")
    print("-" * 72)

    if not hits:
        print("VERDICT: OK - no causal verbs found. (Associational language throughout.)")
        return 0

    tag = "REVIEW" if has_strategy else "FLAG"
    for lineno, verb, line in hits:
        shown = line if len(line) <= 90 else line[:87] + "..."
        print(f"  [{tag}] L{lineno}: '{verb}'  |  {shown}")
    print("-" * 72)
    if has_strategy:
        print("VERDICT: REVIEW - a strategy is declared, but confirm it actually licenses each "
              "sentence above. Rewrite any not covered to associational wording.")
        return 0
    print("VERDICT: FAIL - causal verbs with NO declared identification strategy. Rewrite to "
          "associational language (see references/causal-verb-list.md) or declare a strategy.")
    return 1


def main(argv=None):
    p = argparse.ArgumentParser(description="Flag causal verbs lacking an identification strategy.")
    p.add_argument("report", nargs="?", help="report draft (markdown/text)")
    p.add_argument("--list", action="store_true", help="print the verb and strategy lists and exit")
    args = p.parse_args(argv)

    if args.list:
        print("Causal verbs (flagged without a strategy):")
        for v in CAUSAL_VERBS:
            print(f"  - {v}")
        print("\nStrategy phrases (license causal claims):")
        for s in STRATEGY_PHRASES:
            print(f"  - {s}")
        return 0

    if not args.report:
        p.error("provide a report file, or --list")
    try:
        text = open(args.report, "r", encoding="utf-8").read()
    except FileNotFoundError:
        sys.stderr.write(f"[causal_verb_scan] report not found: {args.report}\n")
        raise SystemExit(2)
    hits, has_strategy, strat_found = scan(text)
    return report(hits, has_strategy, strat_found)


if __name__ == "__main__":
    raise SystemExit(main())
