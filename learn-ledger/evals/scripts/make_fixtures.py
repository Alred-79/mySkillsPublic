#!/usr/bin/env python3
"""Write the forged event logs and seeded stores under evals/fixtures/.

Each log is built from whole attempts (seal, pose, answer, reveal, grade) so the
expected levels and queues can be computed by hand. Run this after changing a
case, then rerun test_ll.py. Standard library only.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


class Log:
    def __init__(self):
        self.ev = []
        self.q = 0

    def add(self, type_, day, session, mode="review", hhmm="10:00", **f):
        e = {"v": 1, "id": f"e{len(self.ev) + 1:06d}", "ts": f"{day}T{hhmm}:00-05:00", "day": day,
             "session": session, "mode": mode, "type": type_}
        e.update(f)
        self.ev.append(e)
        return e

    def node(self, node, topic, day="2026-02-01"):
        self.add("node", day, "s-setup", mode="teach", node=node, topic=topic, title=node, parents=[])

    def teach(self, node, day, session, props=()):
        self.add("teach", day, session, mode="teach", node=node, text=f"a step on {node}", props=list(props))

    def attempt(self, node, kind, day, verdict, session, witness="hook", hint=0, dk=False, dispute=False,
                hhmm="10:00", topic=None, verify=None):
        self.q += 1
        qid = f"q{self.q:04d}"
        self.add("seal", day, session, hhmm=hhmm, qid=qid, node=node, kind=kind, topic=topic,
                 sha256="0" * 64, prompt_hash=f"h{self.q:04d}", repo=None, rev=None, backup_of=None)
        self.add("pose", day, session, hhmm=hhmm, qid=qid)
        a = self.add("answer", day, session, hhmm=hhmm, qid=qid, text="an answer", confidence=70,
                     dont_know=dk, witness=witness, witness_id=None)
        if verify:
            self.add("verify", day, session, hhmm=hhmm, qid=qid, answer=a["id"], witness=verify)
        self.add("reveal", day, session, hhmm=hhmm, qid=qid, hash_ok=True)
        self.add("grade", day, session, hhmm=hhmm, qid=qid, verdict=verdict, miss_class=None,
                 wrong_model=None, hint_max=hint)
        if dispute:
            self.add("dispute", day, session, hhmm=hhmm, qid=qid, reason="key was wrong")
        return qid

    def write(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(e) + "\n" for e in self.ev))


def levels_logs():
    out = {}
    T = "closures"

    L = Log(); L.node("n", T)
    L.attempt("n", "K1", "2026-02-02", "pass", "s1", hhmm="09:00")
    L.attempt("n", "K1", "2026-02-02", "pass", "s2", hhmm="15:00")
    out["same-day"] = L

    L = Log(); L.node("n", T)
    L.attempt("n", "K1", "2026-02-02", "pass", "s1")
    L.attempt("n", "K1", "2026-02-03", "pass", "s2")
    out["two-days"] = L

    L = Log(); L.node("n", T)
    L.attempt("n", "K1", "2026-02-02", "pass", "s1")
    L.attempt("n", "K1", "2026-02-03", "pass", "s2", hint=3)
    out["hint3"] = L

    L = Log(); L.node("n", T)
    L.attempt("n", "K1", "2026-02-02", "pass", "s1")
    L.attempt("n", "K1", "2026-02-03", "pass", "s2", witness="pending", verify="unwitnessed")
    out["unwitnessed"] = L

    L = Log(); L.node("n", T)
    L.attempt("n", "K1", "2026-02-02", "pass", "s1")
    L.teach("n", "2026-02-03", "s2")
    L.attempt("n", "K1", "2026-02-03", "pass", "s2")
    out["warm-k1"] = L

    L = Log(); L.node("n", T)
    L.attempt("n", "K1", "2026-02-02", "pass", "s1")
    L.attempt("n", "K1", "2026-02-03", "pass", "s2")
    L.attempt("n", "K1", "2026-02-04", "fail", "s3")
    out["fail-reset"] = L

    L = Log(); L.node("n", T)
    L.attempt("n", "K1", "2026-02-02", "pass", "s1")
    L.attempt("n", "K1", "2026-02-03", "pass", "s2")
    L.attempt("n", "K1", "2026-02-04", "fail", "s3", witness="pending", verify="unwitnessed")
    out["unwitnessed-fail"] = L

    L = Log(); L.node("n", T)
    L.attempt("n", "K1", "2026-02-02", "pass", "s1")
    L.attempt("n", "K1", "2026-02-03", "pass", "s2")
    L.attempt("n", "K1", "2026-02-04", "fail", "s3", dispute=True)
    out["disputed"] = L

    L = Log(); L.node("n", T)
    for k in ("K1", "K2", "K4"):
        L.attempt("n", k, "2026-02-02", "pass", f"a-{k}")
        L.attempt("n", k, "2026-02-05", "pass", f"b-{k}")
    L.attempt("n", "K3", "2026-02-02", "pass", "a-K3")
    out["gap-at-k3"] = L

    L = Log(); L.node("n", T)
    for k in ("K1", "K2", "K3", "K4"):
        L.attempt("n", k, "2026-02-02", "pass", f"a-{k}")
        L.attempt("n", k, "2026-02-05", "pass", f"b-{k}")
    L.attempt("n", "K5", "2026-02-06", "pass", "a-K5")
    out["level-4"] = L
    return out


def review_store():
    """Five nodes on 2026-03-10. left-join failed yesterday, semi-join and cross-join due, two not due."""
    T = "sql-joins"
    L = Log()
    for n in ("inner-join", "left-join", "anti-join", "semi-join", "cross-join"):
        L.node(n, T)
    L.attempt("inner-join", "K2", "2026-03-01", "pass", "r1", topic=T)
    L.attempt("inner-join", "K2", "2026-03-04", "pass", "r2", topic=T)
    L.attempt("left-join", "K2", "2026-03-01", "pass", "r1", topic=T, hhmm="11:00")
    L.attempt("left-join", "K2", "2026-03-09", "fail", "r5", topic=T)
    L.attempt("anti-join", "K3", "2026-03-02", "pass", "r6", topic=T)
    L.attempt("anti-join", "K3", "2026-03-05", "pass", "r3", topic=T)
    L.attempt("semi-join", "K2", "2026-03-03", "pass", "r7", topic=T)
    L.attempt("cross-join", "K3", "2026-02-20", "pass", "r8", topic=T)
    L.attempt("cross-join", "K3", "2026-02-24", "pass", "r9", topic=T)
    return L


def single_node_store():
    T = "sql-joins"
    L = Log(); L.node("left-join", T)
    L.attempt("left-join", "K2", "2026-03-01", "pass", "r1", topic=T)
    L.attempt("left-join", "K2", "2026-03-09", "fail", "r2", topic=T)
    L.attempt("left-join", "K3", "2026-03-08", "pass", "r3", topic=T)
    return L


PROPS = [
    {"id": "p0001", "topic": "sql-joins", "statement": "A LEFT JOIN keeps every row of the left table, filling unmatched right columns with NULL", "aliases": [], "source": "model-asserted", "provenance": []},
    {"id": "p0002", "topic": "sql-joins", "statement": "A filter on a right-table column in WHERE removes the NULL-filled rows a LEFT JOIN produced", "aliases": [], "source": "model-asserted", "provenance": []},
    {"id": "p0003", "topic": "sql-joins", "statement": "Putting a right-table filter in WHERE turns a LEFT JOIN into an inner join in effect", "aliases": [], "source": "model-asserted", "provenance": []},
    {"id": "p0004", "topic": "sql-joins", "statement": "A semi join returns each left row at most once when any right row matches", "aliases": [], "source": "model-asserted", "provenance": []},
    {"id": "p0005", "topic": "sql-joins", "statement": "A cross join pairs every left row with every right row, so row counts multiply", "aliases": [], "source": "model-asserted", "provenance": []},
]
CHAINS = [{"id": "c0001", "premises": ["p0001", "p0002"], "conclusion": "p0003", "provenance": []}]
TEACH_PROPS = {"left-join": ["p0001", "p0002", "p0003"], "semi-join": ["p0004"], "cross-join": ["p0005"]}


def write_store(L, path, with_props=True):
    for node, ps in TEACH_PROPS.items():
        if any(e.get("node") == node and e["type"] == "node" for e in L.ev):
            L.teach(node, "2026-02-01", "s-setup", props=ps)
    path.mkdir(parents=True, exist_ok=True)
    L.write(path / "events.jsonl")
    (path / "sealed").mkdir(exist_ok=True)
    (path / "sealed" / ".keep").write_text("")
    (path / "witness.jsonl").write_text("")
    (path / "config.json").write_text(json.dumps({"vault_path": None}, indent=2) + "\n")
    (path / "propositions.jsonl").write_text("".join(json.dumps(p) + "\n" for p in PROPS) if with_props else "")
    (path / "chains.jsonl").write_text("".join(json.dumps(c) + "\n" for c in CHAINS) if with_props else "")


if __name__ == "__main__":
    for name, L in levels_logs().items():
        L.write(ROOT / "logs" / f"{name}.jsonl")
    write_store(review_store(), ROOT / "review-due" / "store")
    write_store(single_node_store(), ROOT / "review-due" / "store-single-node")
    print(f"wrote fixtures under {ROOT}")
