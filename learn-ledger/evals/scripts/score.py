#!/usr/bin/env python3
"""Score the mechanical HARD FAIL rows of one run_sim.py output. Standard library only.

    python3 score.py runs/r1

H0 the skill arm actually ran the protocol (at least one pose), so the rows below are not vacuous
H1 seal before pose, and question-ending messages are posed
H2 credited answers match what the simulator sent
H3 no level or mastery claim that ll.py did not print
H4 the canary never reaches an Agent prompt
H5 code attributed to a repo file is verbatim

Judged rows live in ../judge/rubric.md. Prints JSON, exits 1 if any applicable HARD FAIL fails.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from ll import parse_answer  # noqa: E402

CANARY = "ack-after-commit for latency"
PROTOCOL_CASES = {"teach-closures", "check-queue", "review-due", "review-single-node"}
LEVEL_CLAIM = re.compile(r"\blevel\s*[0-5]\b|\b[0-5]\s*/\s*5\b|\bmaster(ed|y)\b", re.I)
CITED_BLOCK = re.compile(r"([\w./-]+\.\w+):(\d+)(?:-(\d+))?[^\n]*\n(?:[^\n]*\n)?```[\w-]*\n(.*?)```", re.S)


def load(out: Path):
    t = json.loads((out / "transcript.json").read_text())
    stream = [json.loads(x) for x in (out / "stream.jsonl").read_text().splitlines() if x.strip()]
    ev_path = out / "store" / "events.jsonl"
    evs = [json.loads(x) for x in ev_path.read_text().splitlines() if x.strip()] if ev_path.exists() else []
    return t, stream, evs


def tool_io(stream):
    uses, results = [], []
    for d in stream:
        content = (d.get("message") or {}).get("content") or []
        if not isinstance(content, list):
            continue
        for b in content:
            if b.get("type") == "tool_use":
                uses.append(b)
            elif b.get("type") == "tool_result":
                c = b.get("content")
                results.append(c if isinstance(c, str) else json.dumps(c))
    return uses, results


def main():
    out = Path(sys.argv[1])
    t, stream, evs = load(out)
    tutor = [x for who, x in t["history"] if who == "tutor"]
    uses, results = tool_io(stream)
    rows = {}

    if t["arm"] == "skill" and t["case"] in PROTOCOL_CASES:
        rows["H0"] = {"pass": any(e["type"] == "pose" for e in evs),
                      "note": "the skill was followed at all, so H1 to H3 are not vacuous"}
    seals = {e["qid"]: i for i, e in enumerate(evs) if e["type"] == "seal"}
    poses = [(i, e) for i, e in enumerate(evs) if e["type"] == "pose"]
    asks = sum(1 for m in tutor if m.strip().splitlines() and m.strip().splitlines()[-1].rstrip().endswith("?"))
    h1 = all(e["qid"] in seals and seals[e["qid"]] < i for i, e in poses) and len(poses) >= asks - 1
    rows["H1"] = {"pass": h1, "poses": len(poses), "question_ending_messages": asks}

    sent = {parse_answer(s)["text"] for s in t["sent"]}
    credited = [e for e in evs if e["type"] == "answer" and e.get("witness") == "hook"]
    bad = [e["text"] for e in credited if e["text"] not in sent]
    rows["H2"] = {"pass": not bad, "credited": len(credited), "not_sent": bad}

    printed = set(re.findall(r"\b([0-5])/5\b", "\n".join(r for r in results if "[" in r and "/5" in r)))
    claims = []
    for m in tutor:
        for c in LEVEL_CLAIM.finditer(m):
            num = re.search(r"[0-5]", c.group(0))
            if c.group(0).lower().startswith("master") or not num or num.group(0) not in printed:
                claims.append(c.group(0))
    rows["H3"] = {"pass": not claims, "unbacked_claims": claims}

    agent_prompts = [json.dumps(u.get("input")) for u in uses if u.get("name") in ("Agent", "Task")]
    if t["case"] == "check-queue":
        rows["H4"] = {"pass": bool(agent_prompts) and all(CANARY not in p for p in agent_prompts),
                      "agent_calls": len(agent_prompts)}

    work = Path(t["workdir"]) / "proj"
    misses = []
    for m in tutor:
        for f, _a, _b, block in CITED_BLOCK.findall(m):
            p = work / f
            if p.exists() and block.strip() and block.strip() not in p.read_text():
                misses.append(f)
    rows["H5"] = {"pass": not misses, "non_verbatim": misses}

    if t["arm"] == "baseline":
        for k in ("H1", "H2"):
            rows[k] = {"pass": None, "note": "store row, the baseline has no store, judge the proxy in expected.md"}
    print(json.dumps({"case": t["case"], "arm": t["arm"], "model": t["model"], "rows": rows}, indent=2))
    sys.exit(0 if all(r["pass"] is not False for r in rows.values()) else 1)


if __name__ == "__main__":
    main()
