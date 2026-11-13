#!/usr/bin/env python3
"""learn-ledger store tool. Standard library only, Python 3.10+.

The only writer of the learning store. Levels, the review queue, offer limits
and the Obsidian view are all computed here from the append-only event log,
never by the model. See ../references/ledger.md for the rules.

Environment
  LEARN_LEDGER_HOME       store directory (default ~/.learn-ledger)
  CLAUDE_CODE_SESSION_ID  set by Claude Code in Bash and hook subprocesses
  LL_NOW                  ISO timestamp override, for tests and evals only
  LL_CLAUDE_PROJECTS      transcript root override (default ~/.claude/projects)
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fnmatch
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import fcntl  # POSIX
except ImportError:  # pragma: no cover, Windows has no fcntl
    fcntl = None

V = 1
KINDS = ["K1", "K2", "K3", "K4", "K5", "predict"]
VERDICTS = ["pass", "partial", "fail"]
MISS_CLASSES = ["cue", "discrimination", "execution", "careless", "structural"]
DEFAULTS = {
    "vault_path": None,
    "ladder": [1, 3, 7, 16, 35, 75],
    "review_size": 8,
    "hint_max_qualify": 2,
    "min_changed_lines": 15,
    "max_offers_per_day": 3,
    "decline_backoff_hours": 72,
    "reminder_min_due": 3,
    "similar_threshold": 0.8,
    "ignore_globs": [
        "*.md", "*.rst", "*.txt", "docs/*", "doc/*", "*test*", "*spec*",
        "*.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock",
        "Cargo.lock", "go.sum", "*.min.js", "dist/*", "build/*", "vendor/*",
        "*_pb2.py", "*.generated.*", "generated/*",
    ],
}
FOOTER = ("Levels count sealed, witnessed, graded answers on separate days. "
          "Open book, so a witnessed answer may still have had outside help.")


class LLError(Exception):
    """A refused or invalid call. Printed to stderr, exit code 2."""


# ---------------------------------------------------------------- basics

def home() -> Path:
    return Path(os.environ.get("LEARN_LEDGER_HOME") or Path.home() / ".learn-ledger")


def now() -> dt.datetime:
    v = os.environ.get("LL_NOW")
    if v:
        t = dt.datetime.fromisoformat(v)
        return t if t.tzinfo else t.astimezone()
    return dt.datetime.now().astimezone()


def today() -> dt.date:
    return now().date()


def session_id() -> str:
    return os.environ.get("CLAUDE_CODE_SESSION_ID") or "no-session"


def parse_ts(s: str) -> dt.datetime:
    s = s.replace("Z", "+00:00")
    t = dt.datetime.fromisoformat(s)
    return t if t.tzinfo else t.astimezone()


def to_day(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def norm_text(s: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", s.lower()))


ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


def check_id(i: str) -> str:
    if not ID_RE.match(i or ""):
        raise LLError(f"id {i!r} must match [A-Za-z0-9_-]{{1,32}}")
    return i


def yaml_scalar(v) -> str:
    """A JSON string is a valid YAML scalar, so no value can open a new key."""
    return json.dumps(re.sub(r"[\r\n]+", " ", str(v)), ensure_ascii=False)


def write_inside(root: Path, rel: str, text: str) -> None:
    p = (root / rel).resolve()
    if root.resolve() not in p.parents:
        raise LLError(f"refusing to write {rel!r} outside {root}")
    p.write_text(text, encoding="utf-8")


def slugify(s: str, n: int = 48) -> str:
    out = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return (out[:n].rstrip("-")) or "x"


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    p = home() / "config.json"
    if p.exists():
        cfg.update(json.loads(p.read_text()))
    return cfg


@contextlib.contextmanager
def locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+", encoding="utf-8") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield f
        finally:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_UN)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise LLError(f"{path.name} line {i} is not valid JSON ({e})")
    return out


def events() -> list[dict]:
    evs = read_jsonl(home() / "events.jsonl")
    for i, e in enumerate(evs):
        e["_i"] = i
    return evs


def append_event(type_: str, mode: str | None = None, **fields) -> dict:
    """Append one event under an exclusive lock. Ids are sequential, so time-ordered."""
    path = home() / "events.jsonl"
    t = now()
    with locked(path) as f:
        f.seek(0)
        n = sum(1 for line in f if line.strip())
        ev = {"v": V, "id": f"e{n + 1:06d}", "ts": t.isoformat(timespec="seconds"),
              "day": t.date().isoformat(), "session": session_id(), "mode": mode or "teach",
              "type": type_}
        ev.update({k: v for k, v in fields.items()})
        f.seek(0, os.SEEK_END)
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        f.flush()
    return ev


def append_line(path: Path, rec: dict) -> None:
    with locked(path) as f:
        f.seek(0, os.SEEK_END)
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()


def require_store() -> None:
    if not (home() / "config.json").exists():
        raise LLError(f"no store at {home()}. Run `ll.py init` first.")


# ---------------------------------------------------------------- attempts

class Attempt:
    """Everything logged for one qid, in log order."""

    def __init__(self, seal: dict):
        self.seal = seal
        self.qid = seal["qid"]
        self.node = seal["node"]
        self.kind = seal["kind"]
        self.pose = None
        self.answers: list[dict] = []
        self.reveals: list[dict] = []
        self.grade = None
        self.dispute = None
        self.verifies: dict[str, str] = {}

    # order rule: seal < pose < first answer < first reveal < grade, hash ok
    def valid_order(self) -> bool:
        if not (self.pose and self.answers and self.reveals and self.grade):
            return False
        s, p, a, r, g = (self.seal["_i"], self.pose["_i"], self.answers[0]["_i"],
                         self.reveals[0]["_i"], self.grade["_i"])
        if not (s < p < a < r < g):
            return False
        return all(x.get("hash_ok") for x in self.reveals if x["_i"] < g)

    def last_answer(self) -> dict | None:
        if not self.answers:
            return None
        if self.grade:
            before = [a for a in self.answers if a["_i"] < self.grade["_i"]]
            return before[-1] if before else None
        return self.answers[-1]

    def witness_state(self, ans: dict) -> str:
        return self.verifies.get(ans["id"], ans.get("witness", "pending"))

    def counted(self) -> bool:
        return self.valid_order() and not self.dispute

    @property
    def day(self) -> dt.date:
        return to_day(self.grade["day"])

    @property
    def verdict(self) -> str:
        return self.grade["verdict"]

    def dont_know(self) -> bool:
        a = self.last_answer()
        return bool(a and a.get("dont_know"))

    def witnessed(self) -> bool:
        a = self.last_answer()
        return bool(a) and self.witness_state(a) in ("hook", "witnessed")

    def hint_max(self) -> int:
        return int(self.grade.get("hint_max") or 0)

    def non_passing(self) -> bool:
        return self.verdict != "pass" or self.dont_know()

    def sched_qualifies(self, cfg) -> bool:
        """Qualifying pass for the review schedule (no cold requirement)."""
        return (self.verdict == "pass" and not self.dont_know() and self.witnessed()
                and self.hint_max() <= cfg["hint_max_qualify"])


def build_attempts(evs: list[dict]) -> dict[str, Attempt]:
    att: dict[str, Attempt] = {}
    for e in evs:
        t = e["type"]
        if t == "seal":
            att[e["qid"]] = Attempt(e)
            continue
        q = e.get("qid")
        a = att.get(q)
        if t == "verify" and q in att:
            att[q].verifies[e["answer"]] = e["witness"]
            continue
        if a is None:
            continue
        if t == "pose" and a.pose is None:
            a.pose = e
        elif t == "answer":
            a.answers.append(e)
        elif t == "reveal":
            a.reveals.append(e)
        elif t == "grade" and a.grade is None:
            a.grade = e
        elif t == "dispute":
            a.dispute = e
    return att


def is_cold(a: Attempt, evs: list[dict], seals: dict[str, dict]) -> bool:
    """No teach on the node and no reveal of another question on the node earlier this session."""
    p = a.pose
    for e in evs[: p["_i"]]:
        if e.get("session") != p.get("session"):
            continue
        if e["type"] == "teach" and e.get("node") == a.node:
            return False
        if (e["type"] == "reveal" and e.get("qid") != a.qid
                and seals.get(e.get("qid"), {}).get("node") == a.node):
            return False
    return True


def kind_status(node: str, kind: str, atts: list[Attempt], evs, seals, cfg) -> dict:
    mine = sorted([x for x in atts if x.node == node and x.kind == kind and x.counted()],
                  key=lambda x: x.grade["_i"])
    last_bad = max((i for i, x in enumerate(mine) if x.non_passing()), default=-1)
    after = mine[last_bad + 1:]
    qual = []
    for x in after:
        ok = (x.verdict == "pass" and x.witnessed() and not x.dont_know()
              and x.hint_max() <= cfg["hint_max_qualify"])
        if ok and kind == "K1":
            ok = is_cold(x, evs, seals)
        if ok:
            qual.append(x)
    met = any(qual[i].seal["prompt_hash"] != qual[j].seal["prompt_hash"] and qual[i].day != qual[j].day
              for i in range(len(qual)) for j in range(i + 1, len(qual)))
    return {"met": met, "qualifying": len(qual), "days": sorted({str(x.day) for x in qual}),
            "reset": last_bad >= 0}


def compute_levels(evs=None, cfg=None) -> dict[str, dict]:
    evs = events() if evs is None else evs
    cfg = cfg or load_config()
    att = build_attempts(evs)
    seals = {a.qid: a.seal for a in att.values()}
    nodes = {}
    for e in evs:
        if e["type"] == "node":
            nodes.setdefault(e["node"], {"topic": e.get("topic"), "title": e.get("title")})
    for a in att.values():
        nodes.setdefault(a.node, {"topic": a.seal.get("topic"), "title": a.node})
    out = {}
    alist = list(att.values())
    for n, meta in nodes.items():
        kinds = {k: kind_status(n, k, alist, evs, seals, cfg) for k in KINDS[:5]}
        level = 0
        for L in range(1, 6):
            if all(kinds[f"K{j}"]["met"] for j in range(1, L + 1)):
                level = L
            else:
                break
        out[n] = {"topic": meta.get("topic"), "title": meta.get("title"), "level": level, "kinds": kinds}
    return out


def render_levels(levels: dict, topic: str | None = None) -> str:
    rows = []
    by_topic: dict[str, list] = {}
    for n, d in levels.items():
        if topic and d.get("topic") != topic:
            continue
        by_topic.setdefault(d.get("topic") or "(no topic)", []).append((n, d))
    if not by_topic:
        return "no nodes yet"
    w = max(len(n) for ns in by_topic.values() for n, _ in ns)
    for t in sorted(by_topic):
        rows.append(f"topic: {t}")
        for n, d in sorted(by_topic[t]):
            L = d["level"]
            bar = "#" * L + "." * (5 - L)
            ks = " ".join(f"{k}{'+' if d['kinds'][k]['met'] else '-'}" for k in KINDS[:5])
            rows.append(f"  {n.ljust(w)}  [{bar}] {L}/5  {ks}")
    rows.append("legend  K1 recall  K2 explain or predict  K3 apply  K4 analyze  K5 edge case and teach-back;  + met, - not yet")
    return "\n".join(rows)


# ---------------------------------------------------------------- review schedule

def schedule(evs=None, cfg=None, on: dt.date | None = None) -> list[dict]:
    evs = events() if evs is None else evs
    cfg = cfg or load_config()
    on = on or today()
    ladder = cfg["ladder"]
    att = [a for a in build_attempts(evs).values() if a.counted() and a.kind in KINDS[:5]]
    items: dict[tuple, list[Attempt]] = {}
    for a in att:
        items.setdefault((a.node, a.kind), []).append(a)
    chain_count = premise_counts(evs)
    out = []
    for (node, kind), xs in items.items():
        xs.sort(key=lambda x: x.grade["_i"])
        if not any(x.sched_qualifies(cfg) for x in xs):
            continue
        n, anchor = 0, None
        for x in xs:
            if not x.sched_qualifies(cfg):
                n, anchor = 0, x.day
            else:
                need = math.ceil(ladder[min(n, len(ladder) - 1)] / 2)
                if anchor is None or (x.day - anchor).days >= need:
                    n, anchor = n + 1, x.day
        due = anchor + dt.timedelta(days=ladder[min(n, len(ladder) - 1)])
        last = xs[-1]
        out.append({"node": node, "kind": kind, "n": n, "anchor": str(anchor), "due_day": str(due),
                    "due": on >= due, "last_ok": last.sched_qualifies(cfg), "last_day": str(last.day),
                    "premise_of": chain_count.get(node, 0), "topic": last.seal.get("topic")})
    return out


def weakest_key(it: dict):
    return (it["last_ok"], it["n"], it["kind"], -it["premise_of"], it["last_day"], it["node"])


def arrangeable(pool: list[dict], prev: str | None) -> bool:
    """True when pool can be ordered with no two adjacent nodes equal and a first node unlike prev."""
    counts: dict[str, int] = {}
    for x in pool:
        counts[x["node"]] = counts.get(x["node"], 0) + 1
    n = len(pool)
    return all(c <= (n // 2 if node == prev else (n + 1) // 2) for node, c in counts.items())


def interleave(items: list[dict]) -> list[dict]:
    """Weakest first, never two of a node in a row when any order allows it."""
    pool = sorted(items, key=weakest_key)
    out = []
    while pool:
        prev = out[-1]["node"] if out else None
        rest = lambda x: [y for y in pool if y is not x]  # noqa: E731
        pick = (next((x for x in pool if x["node"] != prev and arrangeable(rest(x), x["node"])), None)
                or next((x for x in pool if x["node"] != prev), None) or pool[0])
        pool.remove(pick)
        out.append(pick)
    return out


def can_interleave(items: list[dict]) -> bool:
    return arrangeable(items, None)


def due_queue(size: int | None = None, evs=None, cfg=None, on=None) -> dict:
    cfg = cfg or load_config()
    size = size or cfg["review_size"]
    sched = schedule(evs, cfg, on)
    due = sorted([x for x in sched if x["due"]], key=weakest_key)[:size]
    note = None
    if due:
        others = sorted([x for x in sched if not x["due"]], key=lambda x: (x["due_day"], weakest_key(x)))
        while len(due) < size and (len({y["node"] for y in due}) < 2 or not can_interleave(due)):
            counts: dict[str, int] = {}
            for y in due:
                counts[y["node"]] = counts.get(y["node"], 0) + 1
            top = max(counts, key=counts.get)
            pad = next((x for x in others if x["node"] != top), None)
            if pad is None:
                break
            others.remove(pad)
            due.append(dict(pad, padded=True))
        if len({y["node"] for y in due}) < 2:
            note = "single node, so run it without interleaving and vary the surface of each question"
    q = interleave(due)
    next_due = min((x["due_day"] for x in sched if not x["due"]), default=None)
    return {"queue": q, "note": note, "next_due": next_due, "due_count": sum(1 for x in sched if x["due"])}


# ---------------------------------------------------------------- propositions and chains

def merged(path: Path, id_key: str = "id") -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in read_jsonl(path):
        i = r[id_key]
        if i not in out:
            r = dict(r)
            r["provenance"] = list(r.get("provenance") or [])
            r["aliases"] = list(r.get("aliases") or [])
            out[i] = r
        else:
            cur = out[i]
            for p in r.get("provenance") or []:
                if p not in cur["provenance"]:
                    cur["provenance"].append(p)
            for p in r.get("aliases") or []:
                if p not in cur["aliases"]:
                    cur["aliases"].append(p)
    return out


def props() -> dict[str, dict]:
    return merged(home() / "propositions.jsonl")


def chains() -> dict[str, dict]:
    return merged(home() / "chains.jsonl")


def prop_nodes(evs) -> dict[str, set]:
    """Map proposition id to the nodes it was taught on."""
    teach = {e["id"]: e for e in evs if e["type"] == "teach"}
    out: dict[str, set] = {}
    for e in teach.values():
        for p in e.get("props") or []:
            out.setdefault(p, set()).add(e["node"])
    for pid, p in props().items():
        for ev_id in p.get("provenance") or []:
            if ev_id in teach:
                out.setdefault(pid, set()).add(teach[ev_id]["node"])
    return out


def premise_counts(evs) -> dict[str, int]:
    pn = prop_nodes(evs)
    out: dict[str, int] = {}
    for c in chains().values():
        nodes = set()
        for p in c.get("premises") or []:
            nodes |= pn.get(p, set())
        for n in nodes:
            out[n] = out.get(n, 0) + 1
    return out


def overlap(a: str, b: str) -> float:
    A, B = set(norm_text(a).split()), set(norm_text(b).split())
    if not A or not B:
        return 0.0
    return len(A & B) / max(len(A), len(B))


# ---------------------------------------------------------------- witness and transcript

def parse_answer(text: str) -> dict:
    t = text.strip()
    conf = None
    m = re.search(r"(?:^|\s)@\s?(\d{1,3})\s*%?\s*$", t)
    if m:
        conf = max(0, min(100, int(m.group(1))))
        t = t[: m.start()].rstrip()
    dk = t.lower() in ("idk", "?", "i don't know", "i dont know", "skip")
    if dk:
        conf = None
    return {"text": t, "confidence": conf, "dont_know": dk}


def open_question(evs, session: str) -> dict | None:
    """The latest posed, ungraded, undisputed qid in this session."""
    att = build_attempts(evs)
    open_ = [a for a in att.values() if a.pose and not a.grade and not a.dispute
             and a.pose.get("session") == session]
    return max(open_, key=lambda a: a.pose["_i"]).pose if open_ else None


def transcript_files(session: str) -> list[Path]:
    root = Path(os.environ.get("LL_CLAUDE_PROJECTS") or Path.home() / ".claude" / "projects")
    return sorted(root.glob(f"*/{session}.jsonl")) if root.exists() else []


def transcript_user_texts(path: Path) -> list[tuple[dt.datetime, str]]:
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") != "user" or d.get("isMeta"):
            continue
        c = (d.get("message") or {}).get("content")
        if isinstance(c, list):
            c = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
        if isinstance(c, str) and d.get("timestamp"):
            out.append((parse_ts(d["timestamp"]), c))
    return out


def run_verify(quiet: bool = False) -> list[str]:
    evs = events()
    att = build_attempts(evs)
    msgs = []
    for a in att.values():
        for ans in a.answers:
            if a.witness_state(ans) != "pending":
                continue
            files = transcript_files(ans["session"])
            pose_t = parse_ts(a.pose["ts"])
            want = norm_text(ans["text"])
            question = norm_text(json.loads((home() / "sealed" / f"{a.qid}.json").read_text()).get("question", "")) \
                if (home() / "sealed" / f"{a.qid}.json").exists() else ""
            found = None
            if want and want not in question:
                for f in files:
                    try:
                        for t, txt in transcript_user_texts(f):
                            if t >= pose_t - dt.timedelta(seconds=1) and norm_text(parse_answer(txt)["text"]) == want:
                                found = {"file": f.name, "ts": t.isoformat()}
                                break
                    except OSError:
                        continue
                    if found:
                        break
            age = now() - parse_ts(ans["ts"])
            if found:
                state = "witnessed"
            elif ans["session"] == session_id() and age < dt.timedelta(minutes=10):
                continue  # the transcript is written asynchronously, try again later
            else:
                state = "unwitnessed"
            append_event("verify", a.seal.get("mode"), qid=a.qid, answer=ans["id"], witness=state, matched=found)
            msgs.append(f"{a.qid} answer {ans['id']}: {state}")
    if not quiet:
        print("\n".join(msgs) if msgs else "nothing pending")
    return msgs


# ---------------------------------------------------------------- git helpers

def git(cwd: str, *args: str) -> str:
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        raise LLError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def repo_root(cwd: str) -> str | None:
    try:
        return git(cwd, "rev-parse", "--show-toplevel").strip()
    except (LLError, OSError, subprocess.SubprocessError):
        return None


def changed_lines(cwd: str, sha: str, ignore: list[str]) -> int:
    total = 0
    for line in git(cwd, "show", "--numstat", "--format=", sha).splitlines():
        parts = line.split("\t")
        if len(parts) != 3 or parts[0] == "-":
            continue
        path = parts[2]
        if any(fnmatch.fnmatch(path, g) or fnmatch.fnmatch(Path(path).name, g) for g in ignore):
            continue
        total += int(parts[0]) + int(parts[1])
    return total


# ---------------------------------------------------------------- commands

def cmd_init(a):
    h = home()
    (h / "sealed").mkdir(parents=True, exist_ok=True)
    p = h / "config.json"
    cfg = json.loads(p.read_text()) if p.exists() else {}
    for k, v in DEFAULTS.items():
        cfg.setdefault(k, v)
    if a.vault:
        cfg["vault_path"] = str(Path(a.vault).expanduser())
    p.write_text(json.dumps(cfg, indent=2) + "\n")
    for f in ("events.jsonl", "witness.jsonl", "propositions.jsonl", "chains.jsonl"):
        (h / f).touch()
    print(f"store ready at {h}" + (f", vault {cfg['vault_path']}" if cfg.get("vault_path") else ", no vault set"))


def cmd_node_add(a):
    require_store()
    parents = [x for x in (a.parents or "").split(",") if x]
    append_event("node", a.mode, node=a.id, topic=a.topic, title=a.title, parents=parents)
    print(f"node {a.id} added to {a.topic}")


def cmd_teach(a):
    require_store()
    text = sys.stdin.read() if a.file == "-" else Path(a.file).read_text(encoding="utf-8")
    if not text.strip():
        raise LLError("teach step is empty")
    ps = [x for x in (a.props or "").split(",") if x]
    ev = append_event("teach", a.mode, node=a.node, text=text.strip(), props=ps)
    print(f"teach step {ev['id']} logged on {a.node}")


def validate_packet(p: dict, kind: str) -> None:
    if not isinstance(p, dict) or not str(p.get("question", "")).strip():
        raise LLError("each packet needs a non-empty question")
    if kind == "K5":
        r = p.get("rubric")
        if not isinstance(r, list) or not r:
            raise LLError("K5 packets need a rubric, a list of must-criteria")
    elif kind != "predict" and not str(p.get("answer", "")).strip():
        raise LLError(f"{kind} packets need a reference answer")
    if kind in ("K4",) and not p.get("wrong_models"):
        raise LLError("K4 packets need wrong_models, the named wrong options")


def cmd_seal(a):
    require_store()
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise LLError(f"packet is not valid JSON ({e})")
    packets = data if isinstance(data, list) else [data]
    evs = events()
    topics = {e["node"]: e.get("topic") for e in evs if e["type"] == "node"}
    out = []
    for p in packets:
        node = p.get("node") or a.node
        kind = p.get("kind") or a.kind
        if not node or kind not in KINDS:
            raise LLError(f"packet needs a node and a kind in {KINDS}")
        validate_packet(p, kind)
        out.append((node, kind, p))
    for node, kind, p in out:
        n = len(read_jsonl(home() / "events.jsonl"))
        qid = f"q{n + 1:06d}"
        body = {"qid": qid, "node": node, "kind": kind, "question": p["question"].strip(),
                "answer": p.get("answer"), "rubric": p.get("rubric"),
                "wrong_models": p.get("wrong_models") or [], "citations": p.get("citations") or [],
                "backup_of": p.get("backup_of")}
        f = home() / "sealed" / f"{qid}.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(body, indent=2, ensure_ascii=False).encode()
        f.write_bytes(data)
        append_event("seal", a.mode, qid=qid, node=node, kind=kind, topic=p.get("topic") or topics.get(node),
                     sha256=sha256_bytes(data), prompt_hash=sha256_bytes(norm_text(body["question"]).encode())[:16],
                     repo=a.repo, rev=a.rev, backup_of=body["backup_of"])
        print(f"{qid}  [{kind}] {body['question']}" + (f"  (backup of {body['backup_of']})" if body["backup_of"] else ""))


def get_attempt(qid: str) -> tuple[Attempt, list[dict]]:
    evs = events()
    att = build_attempts(evs)
    if qid not in att:
        raise LLError(f"{qid} has no seal event. Seal the question before posing it.")
    return att[qid], evs


def cmd_pose(a):
    require_store()
    at, _ = get_attempt(a.qid)
    if at.pose:
        raise LLError(f"{a.qid} was already posed. Pose a fresh question instead of re-asking.")
    append_event("pose", at.seal.get("mode"), qid=a.qid)
    body = json.loads((home() / "sealed" / f"{a.qid}.json").read_text())
    print(f"posed {a.qid}. Show the learner exactly this, then end the message:\n{body['question']}")


def cmd_answer(a):
    require_store()
    at, evs = get_attempt(a.qid)
    if not at.pose:
        raise LLError(f"{a.qid} was never posed.")
    if at.grade:
        raise LLError(f"{a.qid} is already graded.")
    if at.answers and not at.reveals:
        raise LLError(f"{a.qid} already has an answer. Reveal it before logging a hint-rung retry.")
    if a.text is not None:
        parsed = parse_answer(a.text)
        ev = append_event("answer", at.seal.get("mode"), qid=a.qid, witness="pending", witness_id=None, **parsed)
        print(f"answer {ev['id']} logged as pending. `ll.py verify` checks it against the session transcript later.")
        return
    used = {x.get("witness_id") for x in at.answers}
    pose_t = parse_ts(at.pose["ts"])
    since = at.answers[-1]["ts"] if at.answers else at.pose["ts"]
    since_t = parse_ts(since)
    cands = [w for w in read_jsonl(home() / "witness.jsonl")
             if w.get("session") == at.pose["session"] and parse_ts(w["ts"]) >= pose_t
             and parse_ts(w["ts"]) >= since_t and w["id"] not in used]
    if not cands:
        raise LLError(
            f"no witnessed prompt in session {at.pose['session']} since {a.qid} was posed. "
            "The witness hook registers when the skill is invoked and does not survive --resume or a restart. "
            "Re-invoke /learn-ledger, ask the learner to resend the answer, or log it with --text (pending, no credit until verified).")
    if a.witness:
        pick = next((w for w in cands if w["id"] == a.witness), None)
        if not pick:
            raise LLError(f"{a.witness} is not a witnessed prompt for {a.qid}. Candidates: {', '.join(w['id'] for w in cands)}")
    elif len(cands) > 1:
        lines = [f"  {w['id']}  {w['ts']}  {w['prompt'][:80]!r}" for w in cands]
        raise LLError("more than one prompt was witnessed since the pose. Pick the learner's answer with --witness ID:\n"
                      + "\n".join(lines))
    else:
        pick = cands[0]
    parsed = parse_answer(pick["prompt"])
    ev = append_event("answer", at.seal.get("mode"), qid=a.qid, witness="hook", witness_id=pick["id"], **parsed)
    conf = "none" if parsed["confidence"] is None else f"{parsed['confidence']}%"
    print(f"answer {ev['id']} logged from witness {pick['id']}, confidence {conf}"
          + (", don't-know" if parsed["dont_know"] else "") + f":\n{parsed['text']}")


def cmd_reveal(a):
    require_store()
    at, _ = get_attempt(a.qid)
    if not at.answers:
        raise LLError(f"{a.qid} has no answer yet. Reveal only after the learner answers.")
    f = home() / "sealed" / f"{a.qid}.json"
    data = f.read_bytes() if f.exists() else b""
    ok = sha256_bytes(data) == at.seal["sha256"]
    append_event("reveal", at.seal.get("mode"), qid=a.qid, hash_ok=ok)
    if not ok:
        print(f"HASH MISMATCH. sealed/{a.qid}.json changed after it was sealed, so {a.qid} cannot be graded.",
              file=sys.stderr)
        sys.exit(3)
    body = json.loads(data)
    print(json.dumps({k: body[k] for k in ("qid", "kind", "question", "answer", "rubric", "wrong_models", "citations")
                      if body.get(k) not in (None, [])}, indent=2, ensure_ascii=False))


def cmd_grade(a):
    require_store()
    at, _ = get_attempt(a.qid)
    if at.grade:
        raise LLError(f"{a.qid} is already graded.")
    if not (at.pose and at.answers and at.reveals):
        raise LLError(f"{a.qid} needs seal, pose, answer and reveal before grade.")
    s, p, an, r = at.seal["_i"], at.pose["_i"], at.answers[0]["_i"], at.reveals[0]["_i"]
    if not (s < p < an < r):
        raise LLError(f"{a.qid} events are out of order (seal, pose, answer, reveal required).")
    if not all(x.get("hash_ok") for x in at.reveals):
        raise LLError(f"{a.qid} failed its hash check at reveal and cannot be graded.")
    if a.verdict == "pass" and at.answers[-1].get("dont_know"):
        raise LLError("a don't-know answer cannot be graded pass.")
    ev = append_event("grade", at.seal.get("mode"), qid=a.qid, verdict=a.verdict, miss_class=a.miss_class,
                      wrong_model=a.wrong_model, hint_max=a.hint_max)
    print(f"graded {a.qid} {a.verdict} (event {ev['id']})")


def cmd_dispute(a):
    require_store()
    at, _ = get_attempt(a.qid)
    append_event("dispute", at.seal.get("mode"), qid=a.qid, reason=a.reason)
    print(f"{a.qid} disputed and dropped from levels. Run adversarial-verify on `ll.py ledger` to settle the key.")


def cmd_levels(a):
    require_store()
    run_verify(quiet=True)
    print(render_levels(compute_levels(), a.topic))
    print(FOOTER)


def cmd_due(a):
    require_store()
    run_verify(quiet=True)
    d = due_queue(a.size)
    if a.json:
        print(json.dumps(d, indent=2))
        return
    if not d["queue"]:
        print("nothing due" + (f", next item due {d['next_due']}" if d["next_due"] else ""))
        return
    pm = props()
    pn = prop_nodes(events())
    for i, x in enumerate(d["queue"], 1):
        ps = [pid for pid, ns in pn.items() if x["node"] in ns and pid in pm]
        tag = " (padded, not yet due)" if x.get("padded") else ""
        print(f"{i}. {x['node']} {x['kind']}  n={x['n']} due {x['due_day']} last {'pass' if x['last_ok'] else 'miss'}"
              f"{tag}  props {','.join(ps) or '-'}")
    if d["note"]:
        print(f"note: {d['note']}")


def cmd_verify(a):
    require_store()
    run_verify()


def cmd_status(a):
    require_store()
    run_verify(quiet=True)
    evs = events()
    cfg = load_config()
    s = session_id()
    print(f"learn-ledger store {home()}  session {s}")
    oq = open_question(evs, s)
    if oq:
        at = build_attempts(evs)[oq["qid"]]
        body = json.loads((home() / "sealed" / f"{oq['qid']}.json").read_text())
        stage = "answered, reveal next" if at.answers and not at.reveals else (
            "revealed, grade or give the next hint rung" if at.reveals else "waiting for the learner's answer")
        print(f"open question {oq['qid']} [{at.kind}] on {at.node}, {stage}:\n  {body['question']}")
    else:
        print("no open question")
    mine = [e for e in evs if e.get("session") == s and e["type"] in ("node", "teach", "seal")]
    if mine:
        print(f"current node {mine[-1].get('node')} ({mine[-1].get('mode')} mode)")
    root = repo_root(os.getcwd())
    checked = [e["rev"] for e in evs if e["type"] == "seal" and root and e.get("repo") == root and e.get("rev")]
    if checked:
        print(f"last check in this repo {checked[-1]}, so check mode defaults to {checked[-1]}..HEAD")
    lv = compute_levels(evs, cfg)
    if lv:
        print(render_levels(lv))
    d = due_queue(evs=evs, cfg=cfg)
    print(f"due now {d['due_count']}" + (f", next due {d['next_due']}" if d["next_due"] else ""))
    pend = sum(1 for at in build_attempts(evs).values() for x in at.answers if at.witness_state(x) == "pending")
    if pend:
        print(f"{pend} answer(s) pending transcript verification")
    print(f"vault {cfg.get('vault_path') or 'not set'}")
    print(FOOTER)


def cmd_prop(a):
    require_store()
    if a.action == "similar":
        th = a.threshold if a.threshold is not None else load_config()["similar_threshold"]
        hits = sorted(((overlap(a.statement, p["statement"]), pid, p["statement"]) for pid, p in props().items()),
                      reverse=True)
        hits = [h for h in hits if h[0] >= th]
        print("\n".join(f"{pid}  {sc:.2f}  {st}" for sc, pid, st in hits) or "no similar proposition")
        return
    existing = props()
    pid = check_id(a.id or f"p{len(existing) + 1:04d}")
    if pid not in existing and not a.force:
        th = load_config()["similar_threshold"]
        near = [(i, p["statement"]) for i, p in existing.items() if overlap(a.statement, p["statement"]) >= th]
        if near:
            raise LLError("near-duplicate of " + "; ".join(f"{i} {s!r}" for i, s in near)
                          + ". Merge with --id ID, or pass --force with a reason the new one differs.")
    rec = {"id": pid, "topic": a.topic, "statement": a.statement,
           "aliases": [x for x in (a.aliases or "").split(",") if x], "source": a.source or "model-asserted",
           "provenance": [x for x in (a.provenance or "").split(",") if x]}
    if a.force and a.reason:
        rec["differs_because"] = a.reason
    append_line(home() / "propositions.jsonl", rec)
    print(f"{pid} {'merged' if pid in existing else 'added'}")


def cmd_chain(a):
    require_store()
    pm = props()
    prem = [x for x in a.premises.split(",") if x]
    for p in prem + [a.conclusion]:
        if p not in pm:
            raise LLError(f"unknown proposition {p}")
    if len(prem) < 1 or a.conclusion in prem:
        raise LLError("a chain needs premises that do not include its conclusion")
    cid = check_id(a.id or f"c{len(chains()) + 1:04d}")
    append_line(home() / "chains.jsonl", {"id": cid, "premises": prem, "conclusion": a.conclusion,
                                          "provenance": [x for x in (a.provenance or "").split(",") if x]})
    print(f"{cid} added")


def cmd_distill_input(a):
    require_store()
    evs = events()
    if a.done:
        ids = [x for x in a.done.split(",") if x]
        append_event("distilled", "teach", teach_ids=ids, props=[x for x in (a.props or "").split(",") if x],
                     chains=[x for x in (a.chains or "").split(",") if x])
        print(f"marked {len(ids)} teach step(s) distilled")
        return
    done = {i for e in evs if e["type"] == "distilled" for i in e.get("teach_ids", [])}
    topics = {e["node"]: e.get("topic") for e in evs if e["type"] == "node"}
    todo = [{"id": e["id"], "node": e["node"], "topic": topics.get(e["node"]), "day": e["day"], "text": e["text"],
             "props": e.get("props", [])} for e in evs if e["type"] == "teach" and e["id"] not in done]
    if a.topic:
        todo = [t for t in todo if t["topic"] == a.topic]
    print(json.dumps({"teach_steps": todo,
                      "existing_propositions": [{"id": i, "statement": p["statement"], "topic": p.get("topic")}
                                                for i, p in props().items()]}, indent=2, ensure_ascii=False))


SNIP = re.compile(r"^(?P<file>.+?):(?P<a>\d+)(?:-(?P<b>\d+))?(?:@(?P<rev>[\w./-]+))?$")


def read_snippet(spec: str, rev: str | None, cwd: str) -> tuple[str, list[str], str]:
    m = SNIP.match(spec)
    if not m:
        raise LLError("snippet spec is FILE:START-END")
    rev = rev or m.group("rev")
    f, start = m.group("file"), int(m.group("a"))
    end = int(m.group("b") or start)
    if os.path.isabs(f):
        raise LLError("snippet takes a path relative to the repo, not an absolute path")
    root = Path(repo_root(cwd) or cwd).resolve()
    target = (Path(cwd) / f).resolve()
    if root not in target.parents or home().resolve() in [target, *target.parents]:
        raise LLError(f"{f} is outside the repo or inside the learn-ledger store")
    rel = str(target.relative_to(root))
    if rev:
        text = git(str(root), "show", f"{rev}:{rel}")
    else:
        text = target.read_text(encoding="utf-8")
    lines = text.splitlines()
    if start < 1 or end > len(lines) or start > end:
        raise LLError(f"{f} has {len(lines)} lines, so {start}-{end} is out of range")
    return f, lines[start - 1:end], rev or "worktree"


def cmd_snippet(a):
    f, lines, rev = read_snippet(a.spec, a.rev, os.getcwd())
    body = "\n".join(lines)
    start = int(SNIP.match(a.spec).group("a"))
    print(f"{f}:{start}-{start + len(lines) - 1}@{rev} sha256={sha256_bytes(body.encode())[:16]}")
    print(body)


def cite_status(cite: str, cwd: str) -> str:
    try:
        read_snippet(cite, None, cwd)
        return "verified"
    except (LLError, OSError, subprocess.SubprocessError):
        return "unverifiable"


def cmd_ledger(a):
    require_store()
    evs = events()
    att = build_attempts(evs)
    rows = []
    for pid, p in sorted(props().items()):
        if a.topic and p.get("topic") != a.topic:
            continue
        src = p.get("source") or "model-asserted"
        if src == "model-asserted":
            status, ev = "unverifiable", "model-asserted, no source"
        elif re.match(r"https?://", src):
            status, ev = "proposed", src
        else:
            status, ev = cite_status(src, a.repo or os.getcwd()), src
        exp = p.get("expiry") or "stable"
        rows.append((f"L-{pid}", p["statement"], status, ev, exp))
    for at in att.values():
        if at.seal.get("mode") != "check" or not at.reveals:
            continue
        if a.topic and at.seal.get("topic") not in (a.topic, None):
            continue
        body = json.loads((home() / "sealed" / f"{at.qid}.json").read_text())
        cites = body.get("citations") or []
        repo = at.seal.get("repo") or a.repo or os.getcwd()
        if at.dispute:
            status = "disputed"
        elif cites and all(cite_status(c if "@" in c or not at.seal.get("rev") else f"{c}@{at.seal['rev']}", repo)
                           == "verified" for c in cites):
            status = "verified"
        else:
            status = "unverifiable"
        rows.append((f"L-{at.qid}", f"{body['question']} -> {body.get('answer')}", status,
                     ", ".join(cites) or "no citation", f"until {at.seal.get('rev') or 'code changes'}"))
    print("| id | assertion | status | evidence | expiry | risk |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        cells = [str(c).replace("|", "\\|").replace("\n", " ") for c in r]
        print(f"| {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} | {cells[4]} | medium |")


EXPORT_MARK = "<!-- generated by learn-ledger -->"


def cmd_export(a):
    require_store()
    cfg = load_config()
    vault = a.vault or cfg.get("vault_path")
    if not vault:
        raise LLError("no vault path. Pass --vault PATH or run `ll.py init --vault PATH`.")
    vault = Path(vault).expanduser()
    if not vault.is_dir():
        raise LLError(f"vault {vault} is not an existing directory")
    out = vault / "learn-ledger"
    if out.exists():
        readme = out / "README.md"
        if not (readme.exists() and EXPORT_MARK in readme.read_text(encoding="utf-8")):
            raise LLError(f"{out} exists but was not generated by learn-ledger, so it is left untouched")
        shutil.rmtree(out)
    for d in ("topics", "propositions", "chains"):
        (out / d).mkdir(parents=True, exist_ok=True)
    run_verify(quiet=True)
    evs = events()
    pm, cm = props(), chains()
    names = {pid: f"{slugify(pid, 32)}-{slugify(p['statement'])}" for pid, p in pm.items()}
    cnames = {cid: slugify(cid, 32) for cid in cm}
    (out / "README.md").write_text(
        f"{EXPORT_MARK}\n# learn-ledger\n\nThis folder is a generated view. Edits here are overwritten on the next export.\n"
        f"The source of truth is the event log in `{home()}`.\n", encoding="utf-8")
    lv = compute_levels(evs, cfg)
    d = due_queue(evs=evs, cfg=cfg)
    qlines = [f"{i}. {x['node']} {x['kind']}, due {x['due_day']}" for i, x in enumerate(d["queue"], 1)]
    (out / "_progress.md").write_text(
        f"{EXPORT_MARK}\n# Progress\n\n```\n{render_levels(lv)}\n```\n\n## Due for review\n\n"
        + ("\n".join(qlines) if qlines else "Nothing due.") + f"\n\n{FOOTER}\n", encoding="utf-8")
    premise_of: dict[str, list[str]] = {}
    for cid, c in cm.items():
        for p in c["premises"]:
            premise_of.setdefault(p, []).append(cid)
    by_topic: dict[str, list[str]] = {}
    for pid, p in pm.items():
        by_topic.setdefault(p.get("topic") or "untopiced", []).append(pid)
        fm = ["---", f"id: {yaml_scalar(pid)}", f"topic: {yaml_scalar(p.get('topic') or '')}",
              f"source: {yaml_scalar(p.get('source') or 'model-asserted')}"]
        if p.get("aliases"):
            fm.append("aliases:")
            fm += [f"  - {yaml_scalar(x)}" for x in p["aliases"]]
        fm.append("---")
        body = [p["statement"], "", f"Source: {p.get('source') or 'model-asserted'}",
                f"Provenance: {', '.join(p.get('provenance') or []) or 'none recorded'}"]
        for cid in premise_of.get(pid, []):
            body.append(f"Premise of [[{cnames[cid]}]]")
        write_inside(out, f"propositions/{names[pid]}.md", "\n".join(fm + [""] + body) + "\n")
    for cid, c in cm.items():
        prem = "; ".join(pm[p]["statement"] for p in c["premises"] if p in pm)
        concl = names.get(c["conclusion"], c["conclusion"])
        text = (f"---\nid: {yaml_scalar(cid)}\n---\nPremises, used together: {prem}\n\n"
                f"These jointly imply [[{concl}]]\n\nProvenance: {', '.join(c.get('provenance') or []) or 'none recorded'}\n")
        write_inside(out, f"chains/{cnames[cid]}.md", text)
    for t, pids in by_topic.items():
        links = "\n".join(f"- [[{names[p]}]]" for p in sorted(pids))
        write_inside(out, f"topics/{slugify(t)}.md", f"# {t}\n\n{links}\n")
    print(f"exported {len(pm)} propositions, {len(cm)} chains, {len(by_topic)} topics to {out}")


def cmd_optin(a):
    require_store()
    if a.pause:
        m = re.fullmatch(r"(\d+)d", a.pause)
        if not m:
            raise LLError("--pause takes days, like 7d")
        until = (today() + dt.timedelta(days=int(m.group(1)))).isoformat()
        append_event("pause", "check", until=until)
        print(f"offers paused until {until}")
    elif a.off:
        append_event("pause", "check", until="off")
        print("offers off until `ll.py optin --on`")
    else:
        append_event("pause", "check", until="on")
        print("offers on")


def cmd_offer(a):
    require_store()
    append_event(a.response, "check", rev=a.rev, repo=repo_root(os.getcwd()))
    print(f"{a.response} logged")


def offer_blocked(evs, cfg, sess: str, repo: str, sha: str) -> str | None:
    t = now()
    offers = [e for e in evs if e["type"] == "offer"]
    if any(e["session"] == sess for e in offers):
        return "already offered this session"
    if sum(1 for e in offers if e["day"] == t.date().isoformat()) >= cfg["max_offers_per_day"]:
        return "daily offer limit reached"
    if any(e["type"] == "seal" and e.get("repo") == repo and e.get("rev") and
           (str(e["rev"]).startswith(sha) or sha.startswith(str(e["rev"]))) for e in evs):
        return "this commit was already checked"
    if any(e["type"] == "decline" and e["session"] == sess for e in evs):
        return "declined this session"
    responses = [e for e in evs if e["type"] in ("accept", "decline")]
    if len(responses) >= 2 and all(r["type"] == "decline" for r in responses[-2:]):
        if t - parse_ts(responses[-1]["ts"]) < dt.timedelta(hours=cfg["decline_backoff_hours"]):
            return "two declines in a row, backing off"
    pauses = [e for e in evs if e["type"] == "pause"]
    if pauses:
        u = pauses[-1]["until"]
        if u == "off" or (u not in ("on", "off") and t.date() < to_day(u)):
            return "paused"
    return None


def hook_post_commit(data: dict) -> None:
    if data.get("agent_id"):
        return
    cmd = ((data.get("tool_input") or {}).get("command") or "")
    if not re.search(r"\bgit\b[^\n;&|]*\bcommit\b", cmd):
        return
    resp = data.get("tool_response") or {}
    stdout = resp.get("stdout") if isinstance(resp, dict) else str(resp)
    m = re.search(r"^\[[^\]\s]+(?: \(root-commit\))? ([0-9a-f]{7,40})\]", stdout or "", re.M)
    if not m:
        return
    sha = m.group(1)
    cwd = data.get("cwd") or os.getcwd()
    repo = repo_root(cwd)
    if not repo or not (home() / "config.json").exists():
        return
    cfg = load_config()
    if changed_lines(repo, sha, cfg["ignore_globs"]) < cfg["min_changed_lines"]:
        return
    sess = data.get("session_id") or session_id()
    os.environ["CLAUDE_CODE_SESSION_ID"] = sess
    if offer_blocked(events(), cfg, sess, repo, sha):
        return
    append_event("offer", "check", repo=repo, rev=sha)
    msg = (f"learn-ledger: commit {sha} is big enough to learn from. Finish the user's current request first. "
           "Then ask one short sentence, such as 'Want a quick check on what that commit does? (yes/no)', and stop. "
           f"If yes, run `ll.py offer accept --rev {sha}` and invoke the learn-ledger skill in check mode for {sha}. "
           f"If no, run `ll.py offer decline --rev {sha}` and do not raise it again this session.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


def hook_witness(data: dict) -> None:
    if data.get("agent_id") or not (home() / "config.json").exists():
        return
    sess = data.get("session_id") or session_id()
    prompt = data.get("prompt")
    if not isinstance(prompt, str) or prompt.lstrip().startswith("/"):
        return  # a slash command, such as the /learn-ledger invocation itself, is never an answer
    oq = open_question(events(), sess)
    if not oq:
        return
    wpath = home() / "witness.jsonl"
    with locked(wpath) as f:
        f.seek(0)
        n = sum(1 for line in f if line.strip())
        rec = {"id": f"w{n + 1:06d}", "session": sess, "ts": now().isoformat(timespec="seconds"),
               "qid": oq["qid"], "prompt": prompt}
        f.seek(0, os.SEEK_END)
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def hook_session_start(data: dict) -> None:
    if data.get("source") != "startup" or not (home() / "config.json").exists():
        return
    cfg = load_config()
    evs = events()
    if any(e["type"] == "reminder" and e["day"] == today().isoformat() for e in evs):
        return
    d = due_queue(evs=evs, cfg=cfg)
    if d["due_count"] < cfg["reminder_min_due"]:
        return
    os.environ["CLAUDE_CODE_SESSION_ID"] = data.get("session_id") or session_id()
    append_event("reminder", "review", until=None)
    print(json.dumps({"systemMessage": f"learn-ledger: {d['due_count']} items are due for review. "
                                        "Say 'what's due' whenever you want them."}))


def cmd_hook(a):
    if a.event == "install":
        if not a.print:
            raise LLError("the skill never edits settings. Use `ll.py hook install --print` and add the output yourself.")
        me = Path(__file__).resolve()
        cmd = f'python3 "{me}"'
        snippet = {"hooks": {
            "PostToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "if": "Bash(git commit *)", "command": f"{cmd} hook post-commit", "timeout": 20}]}],
            "SessionStart": [{"matcher": "startup", "hooks": [
                {"type": "command", "command": f"{cmd} hook session-start", "timeout": 10}]}],
        }}
        print("# Merge into ~/.claude/settings.json. PostToolUse enables commit offers, SessionStart the due reminder.\n"
              "# Keep only the one you want. The witness hook needs no settings, the skill declares it.")
        print(json.dumps(snippet, indent=2))
        return
    # Hooks must never block or crash the session. Any failure is silent.
    try:
        data = json.loads(sys.stdin.read() or "{}")
        {"witness": hook_witness, "post-commit": hook_post_commit, "session-start": hook_session_start}[a.event](data)
    except Exception as e:  # noqa: BLE001, a hook must exit 0
        if os.environ.get("LL_DEBUG"):
            print(f"learn-ledger hook error: {e!r}", file=sys.stderr)
    sys.exit(0)


# ---------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(prog="ll.py", description="learn-ledger store tool")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("init"); p.add_argument("--vault"); p.set_defaults(f=cmd_init)
    p = sp.add_parser("status"); p.set_defaults(f=cmd_status)
    p = sp.add_parser("node"); p.add_argument("action", choices=["add"]); p.add_argument("--topic", required=True)
    p.add_argument("--id", required=True); p.add_argument("--title", required=True); p.add_argument("--parents")
    p.add_argument("--mode", default="teach"); p.set_defaults(f=cmd_node_add)
    p = sp.add_parser("teach"); p.add_argument("--node", required=True); p.add_argument("--file", required=True)
    p.add_argument("--props"); p.add_argument("--mode", default="teach"); p.set_defaults(f=cmd_teach)
    p = sp.add_parser("seal"); p.add_argument("--node"); p.add_argument("--kind", choices=KINDS)
    p.add_argument("--mode", default="teach", choices=["teach", "review", "check"])
    p.add_argument("--repo"); p.add_argument("--rev"); p.set_defaults(f=cmd_seal)
    p = sp.add_parser("pose"); p.add_argument("qid"); p.set_defaults(f=cmd_pose)
    p = sp.add_parser("answer"); p.add_argument("qid"); g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--from-witness", action="store_true"); g.add_argument("--text")
    p.add_argument("--witness"); p.set_defaults(f=cmd_answer)
    p = sp.add_parser("reveal"); p.add_argument("qid"); p.set_defaults(f=cmd_reveal)
    p = sp.add_parser("grade"); p.add_argument("qid"); p.add_argument("--verdict", required=True, choices=VERDICTS)
    p.add_argument("--miss-class", choices=MISS_CLASSES); p.add_argument("--wrong-model")
    p.add_argument("--hint-max", type=int, default=0, choices=range(0, 6)); p.set_defaults(f=cmd_grade)
    p = sp.add_parser("dispute"); p.add_argument("qid"); p.add_argument("--reason", required=True)
    p.set_defaults(f=cmd_dispute)
    p = sp.add_parser("levels"); p.add_argument("--topic"); p.set_defaults(f=cmd_levels)
    p = sp.add_parser("due"); p.add_argument("--size", type=int); p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_due)
    p = sp.add_parser("verify"); p.set_defaults(f=cmd_verify)
    p = sp.add_parser("prop"); p.add_argument("action", choices=["add", "similar"]); p.add_argument("statement")
    p.add_argument("--topic"); p.add_argument("--id"); p.add_argument("--aliases"); p.add_argument("--source")
    p.add_argument("--provenance"); p.add_argument("--threshold", type=float); p.add_argument("--force", action="store_true")
    p.add_argument("--reason"); p.set_defaults(f=cmd_prop)
    p = sp.add_parser("chain"); p.add_argument("action", choices=["add"]); p.add_argument("--premises", required=True)
    p.add_argument("--conclusion", required=True); p.add_argument("--id"); p.add_argument("--provenance")
    p.set_defaults(f=cmd_chain)
    p = sp.add_parser("distill-input"); p.add_argument("--topic"); p.add_argument("--done"); p.add_argument("--props")
    p.add_argument("--chains"); p.set_defaults(f=cmd_distill_input)
    p = sp.add_parser("snippet"); p.add_argument("spec"); p.add_argument("--rev"); p.set_defaults(f=cmd_snippet)
    p = sp.add_parser("ledger"); p.add_argument("--topic"); p.add_argument("--repo"); p.set_defaults(f=cmd_ledger)
    p = sp.add_parser("export"); p.add_argument("--vault"); p.set_defaults(f=cmd_export)
    p = sp.add_parser("optin"); g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--pause"); g.add_argument("--off", action="store_true"); g.add_argument("--on", action="store_true")
    p.set_defaults(f=cmd_optin)
    p = sp.add_parser("offer"); p.add_argument("response", choices=["accept", "decline"]); p.add_argument("--rev")
    p.set_defaults(f=cmd_offer)
    p = sp.add_parser("hook"); p.add_argument("event", choices=["witness", "post-commit", "session-start", "install"])
    p.add_argument("--print", action="store_true"); p.set_defaults(f=cmd_hook)

    a = ap.parse_args(argv)
    try:
        a.f(a)
    except LLError as e:
        print(f"refused: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
