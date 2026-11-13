#!/usr/bin/env python3
"""Drive one learn-ledger eval case against a simulated learner. Standard library only.

    python3 run_sim.py --case teach-closures --arm skill --model sonnet --sim-model haiku --out runs/r1

The skill session is one `claude -p --input-format stream-json` process, and each
learner reply is sent only after the previous turn's result arrives. Both matter.
Skill hooks do not survive `--resume`, and a message queued mid-turn may not reach
the witness hook, so either shortcut would silently drop the witness.

The simulator is a separate `claude -p` call per turn that sees only the assistant's
messages and the learner profile. User settings are left out with
`--setting-sources project,local`, so the owner's personal skills cannot leak into
either arm. Writes transcript.json, the session's stream, and a copy of the store
into --out for score.py.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVALS = HERE.parent
SKILL = EVALS.parent
END = "<<END>>"
ALLOWED = ["Skill", "Bash", "Read", "Grep", "Glob", "Agent", "Write", "Edit"]

SIM_PROMPT = """You are role-playing a learner in an evaluation. Stay in character.
Profile, as JSON. It fixes what you know, your one misconception, your confidence, and scripted lines.
{profile}

Rules.
- Reply as the learner to the tutor's latest message only, in one to three short sentences.
- When asked a question, answer from the profile. If a misconception's trigger matches, give its exact wrong_answer.
- End every answer with your confidence as @NN unless the profile says you omit it.
- When the scripted list has an entry for this question number, say that line instead.
- Never use tools. Never mention that you are simulated.
- When the tutor wraps up and asks nothing more, or after {max_turns} replies, output exactly {end}."""


def case_by_name(name):
    data = json.loads((EVALS / "evals.json").read_text())
    for c in data["evals"]:
        if c["name"] == name:
            return c
    sys.exit(f"no case {name}")


def setup(case, arm, work: Path):
    proj = work / "proj"
    proj.mkdir(parents=True)
    sim = case.get("sim", {})
    if sim.get("repo"):
        subprocess.run([sys.executable, str(HERE / "build_repo.py"), str(EVALS / "fixtures" / sim["repo"]), str(proj)],
                       check=True)
    else:
        subprocess.run(["git", "init", "-q", str(proj)], check=True)
    store = work / "store"
    if sim.get("store"):
        shutil.copytree(EVALS / "fixtures" / sim["store"], store)
    if arm == "skill":
        dest = proj / ".claude" / "skills" / "learn-ledger"
        shutil.copytree(SKILL, dest, ignore=shutil.ignore_patterns("evals", "__pycache__"))
        if sim.get("install_hooks"):
            out = subprocess.run([sys.executable, str(dest / "scripts" / "ll.py"), "hook", "install", "--print"],
                                 capture_output=True, text=True, check=True).stdout
            body = "\n".join(x for x in out.splitlines() if not x.startswith("#"))
            (proj / ".claude" / "settings.json").write_text(body + "\n")
    return proj, store


def read_turn(proc):
    """Read stream-json lines until this turn's result. Returns (events, assistant_text)."""
    evs, texts = [], []
    for line in proc.stdout:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        evs.append(d)
        if d.get("type") == "assistant":
            for b in d["message"].get("content", []):
                if b.get("type") == "text":
                    texts.append(b["text"])
        if d.get("type") == "result":
            break
    return evs, "\n".join(texts)


def simulate(profile, history, sim_model, max_turns):
    prompt = SIM_PROMPT.format(profile=json.dumps(profile, indent=2), max_turns=max_turns, end=END)
    convo = "\n\n".join(f"TUTOR:\n{t}" if who == "tutor" else f"YOU:\n{t}" for who, t in history)
    r = subprocess.run(["claude", "-p", "--model", sim_model, "--system-prompt", prompt, "--tools", "",
                        "--setting-sources", "project", "--no-session-persistence", "--output-format", "json"],
                       input=convo + "\n\nReply as the learner now.", capture_output=True, text=True, timeout=300)
    return json.loads(r.stdout)["result"].strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--arm", choices=["skill", "baseline"], required=True)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--sim-model", default="haiku")
    ap.add_argument("--max-turns", type=int, default=24)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    case = case_by_name(a.case)
    sim = case.get("sim", {})
    work = Path(tempfile.mkdtemp(prefix=f"ll-eval-{a.case}-"))
    proj, store = setup(case, a.arm, work)
    profile = json.loads((EVALS / "fixtures" / "learners" / sim["learner"]).read_text()) if sim.get("learner") else {}
    sid = str(uuid.uuid4())
    env = dict(os.environ, LEARN_LEDGER_HOME=str(store), CLAUDE_CODE_SESSION_ID=sid, CLAUDE_CODE_DISABLE_AUTO_MEMORY="1")
    if sim.get("now"):
        env["LL_NOW"] = sim["now"]
    if a.arm == "skill" and not sim.get("store"):
        subprocess.run([sys.executable, str(SKILL / "scripts" / "ll.py"), "init"], env=env, check=True,
                       capture_output=True)
    env.pop("CLAUDE_CODE_SESSION_ID")

    cmd = ["claude", "-p", "--model", a.model, "--session-id", sid, "--input-format", "stream-json",
           "--output-format", "stream-json", "--verbose", "--setting-sources", "project,local",
           "--allowedTools", *ALLOWED]
    proc = subprocess.Popen(cmd, cwd=proj, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    first = ([(EVALS / sim["preamble_file"]).read_text()] if sim.get("preamble_file") else []) + [case["prompt"]]
    sent, history, stream = [], [], []

    def send(text):
        proc.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n")
        proc.stdin.flush()
        sent.append(text)
        history.append(("you", text))
        evs, reply = read_turn(proc)
        stream.extend(evs)
        history.append(("tutor", reply))
        return reply

    for m in first:
        send(m)
    for m in sim.get("scripted_followups", []):
        send(m)
    turns = 0
    while profile and turns < a.max_turns:
        reply = simulate(profile, history, a.sim_model, a.max_turns)
        if reply.strip() == END or not reply:
            break
        send(reply)
        turns += 1
    proc.stdin.close()
    proc.wait(timeout=600)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "transcript.json").write_text(json.dumps(
        {"case": a.case, "arm": a.arm, "model": a.model, "session": sid, "sent": sent,
         "history": history, "workdir": str(work)}, indent=2))
    (out / "stream.jsonl").write_text("".join(json.dumps(e) + "\n" for e in stream))
    if store.exists():
        shutil.copytree(store, out / "store", dirs_exist_ok=True)
    print(f"{a.case} {a.arm}: {len(sent)} learner messages, output in {out}")


if __name__ == "__main__":
    main()
