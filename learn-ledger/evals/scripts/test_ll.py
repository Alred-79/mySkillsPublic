#!/usr/bin/env python3
"""Deterministic tests for scripts/ll.py. No model, no network. Run:

    python3 learn-ledger/evals/scripts/test_ll.py

Every test runs ll.py as a subprocess against a throwaway store, the way the
skill and the hooks call it.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
LL = SKILL / "scripts" / "ll.py"
FIX = SKILL / "evals" / "fixtures"
NOW = "2026-03-10T09:00:00-05:00"


class Store:
    def __init__(self, src: Path | None = None, events: Path | None = None):
        self.dir = Path(tempfile.mkdtemp(prefix="ll-test-"))
        self.env = dict(os.environ, LEARN_LEDGER_HOME=str(self.dir), LL_NOW=NOW,
                        CLAUDE_CODE_SESSION_ID="sess-A", LL_CLAUDE_PROJECTS=str(self.dir / "projects"))
        if src:
            shutil.copytree(src, self.dir, dirs_exist_ok=True)
        else:
            self.run("init")
        if events:
            shutil.copy(events, self.dir / "events.jsonl")

    def run(self, *args, stdin=None, ok=True, **env):
        e = dict(self.env, **env)
        r = subprocess.run([sys.executable, str(LL), *args], input=stdin, capture_output=True, text=True, env=e)
        if ok is True and r.returncode != 0:
            raise AssertionError(f"ll.py {' '.join(args)} failed ({r.returncode}): {r.stderr}")
        return r

    def events(self):
        return [json.loads(x) for x in (self.dir / "events.jsonl").read_text().splitlines() if x.strip()]

    def witness(self, prompt, session="sess-A", **env):
        data = {"session_id": session, "hook_event_name": "UserPromptSubmit", "prompt": prompt, "cwd": str(self.dir)}
        return self.run("hook", "witness", stdin=json.dumps(data), CLAUDE_CODE_SESSION_ID=session, **env)

    def seal(self, question="What does f() return?", answer="42", kind="K2", node="n", **extra):
        pkt = dict({"question": question, "answer": answer, "wrong_models": ["43, off by one"]}, **extra)
        out = self.run("seal", "--node", node, "--kind", kind, stdin=json.dumps(pkt)).stdout
        return re.match(r"(q\d+)", out).group(1)

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def level_of(store: Store, node="n") -> int:
    out = store.run("levels").stdout
    m = re.search(rf"^\s+{re.escape(node)}\s+\[[#.]+\] (\d)/5", out, re.M)
    return int(m.group(1))


def kind_met(store: Store, kind: str, node="n") -> bool:
    out = store.run("levels").stdout
    line = next(x for x in out.splitlines() if re.match(rf"^\s+{re.escape(node)}\s+\[", x))
    return f"{kind}+" in line


class Levels(unittest.TestCase):
    """Forged logs from make_fixtures.py, one rule each."""

    def check(self, name, k1_met, level):
        s = Store(events=FIX / "logs" / f"{name}.jsonl")
        try:
            self.assertEqual(kind_met(s, "K1"), k1_met, name)
            self.assertEqual(level_of(s), level, name)
        finally:
            s.cleanup()

    def test_two_passes_same_day_do_not_meet_a_kind(self):
        self.check("same-day", False, 0)

    def test_two_passes_on_two_days_meet_k1(self):
        self.check("two-days", True, 1)

    def test_pass_at_hint_3_does_not_qualify(self):
        self.check("hint3", False, 0)

    def test_unwitnessed_pass_does_not_qualify(self):
        self.check("unwitnessed", False, 0)

    def test_warm_k1_pass_does_not_qualify(self):
        self.check("warm-k1", False, 0)

    def test_fail_resets_its_kind(self):
        self.check("fail-reset", False, 0)

    def test_unwitnessed_fail_still_resets(self):
        self.check("unwitnessed-fail", False, 0)

    def test_disputed_attempt_is_dropped(self):
        self.check("disputed", True, 1)

    def test_level_stops_at_first_unmet_kind(self):
        s = Store(events=FIX / "logs" / "gap-at-k3.jsonl")
        try:
            self.assertTrue(kind_met(s, "K4"))
            self.assertEqual(level_of(s), 2)
        finally:
            s.cleanup()

    def test_level_four_without_k5(self):
        self.check("level-4", True, 4)


class Gates(unittest.TestCase):
    def setUp(self):
        self.s = Store()

    def tearDown(self):
        self.s.cleanup()

    def test_pose_refuses_unsealed_qid(self):
        r = self.s.run("pose", "q999999", ok=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("no seal event", r.stderr)

    def test_seal_prints_question_not_key(self):
        out = self.s.run("seal", "--node", "n", "--kind", "K2",
                         stdin=json.dumps({"question": "Q?", "answer": "SECRET-KEY"})).stdout
        self.assertNotIn("SECRET-KEY", out)
        self.assertIn("Q?", out)

    def test_k5_needs_rubric_and_k4_needs_wrong_models(self):
        r = self.s.run("seal", "--node", "n", "--kind", "K5", stdin=json.dumps({"question": "Teach it back"}), ok=False)
        self.assertIn("rubric", r.stderr)
        r = self.s.run("seal", "--node", "n", "--kind", "K4", stdin=json.dumps({"question": "Which?", "answer": "A"}),
                       ok=False)
        self.assertIn("wrong_models", r.stderr)

    def test_full_cycle_with_witness(self):
        q = self.s.seal()
        self.s.run("pose", q)
        self.s.witness("42 @80")
        out = self.s.run("answer", q, "--from-witness").stdout
        self.assertIn("confidence 80%", out)
        rv = self.s.run("reveal", q).stdout
        self.assertIn('"answer": "42"', rv)
        self.s.run("grade", q, "--verdict", "pass")
        ans = [e for e in self.s.events() if e["type"] == "answer"][0]
        self.assertEqual(ans["witness"], "hook")
        self.assertEqual(ans["text"], "42")

    def test_grade_refuses_before_reveal(self):
        q = self.s.seal()
        self.s.run("pose", q)
        self.s.witness("42")
        self.s.run("answer", q, "--from-witness")
        r = self.s.run("grade", q, "--verdict", "pass", ok=False)
        self.assertIn("reveal", r.stderr)

    def test_grade_refuses_a_seal_logged_after_its_answer(self):
        forged = [
            {"v": 1, "id": "e000001", "ts": "2026-03-10T09:00:00-05:00", "day": "2026-03-10", "session": "sess-A",
             "mode": "teach", "type": "pose", "qid": "q1"},
            {"v": 1, "id": "e000002", "ts": "2026-03-10T09:01:00-05:00", "day": "2026-03-10", "session": "sess-A",
             "mode": "teach", "type": "answer", "qid": "q1", "text": "x", "confidence": None, "dont_know": False,
             "witness": "hook", "witness_id": "w1"},
            {"v": 1, "id": "e000003", "ts": "2026-03-10T09:02:00-05:00", "day": "2026-03-10", "session": "sess-A",
             "mode": "teach", "type": "seal", "qid": "q1", "node": "n", "kind": "K2", "sha256": "0" * 64,
             "prompt_hash": "h", "repo": None, "rev": None},
            {"v": 1, "id": "e000004", "ts": "2026-03-10T09:02:00-05:00", "day": "2026-03-10", "session": "sess-A",
             "mode": "teach", "type": "reveal", "qid": "q1", "hash_ok": True},
        ]
        (self.s.dir / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in forged))
        r = self.s.run("grade", "q1", "--verdict", "pass", ok=False)
        self.assertEqual(r.returncode, 2)

    def test_reveal_detects_an_edited_sealed_file(self):
        q = self.s.seal()
        self.s.run("pose", q)
        self.s.witness("43")
        self.s.run("answer", q, "--from-witness")
        f = self.s.dir / "sealed" / f"{q}.json"
        f.write_text(f.read_text().replace('"42"', '"43"'))
        r = self.s.run("reveal", q, ok=False)
        self.assertEqual(r.returncode, 3)
        self.assertIn("HASH MISMATCH", r.stderr)
        self.assertNotEqual(self.s.run("grade", q, "--verdict", "pass", ok=False).returncode, 0)

    def test_hint_ladder_retries_then_grades_the_last_answer(self):
        q = self.s.seal()
        self.s.run("pose", q)
        self.s.witness("41")
        self.s.run("answer", q, "--from-witness")
        r = self.s.run("answer", q, "--text", "x", ok=False)
        self.assertIn("Reveal it before", r.stderr)
        self.s.run("reveal", q)
        self.s.witness("42 @60")
        self.s.run("answer", q, "--from-witness")
        self.s.run("grade", q, "--verdict", "pass", "--hint-max", "1")
        answers = [e for e in self.s.events() if e["type"] == "answer"]
        self.assertEqual([a["text"] for a in answers], ["41", "42"])

    def test_dont_know_cannot_pass(self):
        q = self.s.seal()
        self.s.run("pose", q)
        self.s.witness("idk")
        out = self.s.run("answer", q, "--from-witness").stdout
        self.assertIn("don't-know", out)
        self.s.run("reveal", q)
        self.assertNotEqual(self.s.run("grade", q, "--verdict", "pass", ok=False).returncode, 0)


class Witness(unittest.TestCase):
    def setUp(self):
        self.s = Store()

    def tearDown(self):
        self.s.cleanup()

    def wlines(self):
        return [json.loads(x) for x in (self.s.dir / "witness.jsonl").read_text().splitlines() if x.strip()]

    def test_records_nothing_without_an_open_question(self):
        self.s.witness("my api key is hunter2, fix the deploy")
        self.assertEqual(self.wlines(), [])

    def test_slash_commands_are_never_witnessed(self):
        q = self.s.seal()
        self.s.run("pose", q)
        self.s.witness("/learn-ledger status")
        self.assertEqual(self.wlines(), [])

    def test_records_only_in_the_posing_session(self):
        q = self.s.seal()
        self.s.run("pose", q)
        self.s.witness("from another terminal", session="sess-B")
        self.assertEqual(self.wlines(), [])

    def test_no_witness_fails_loudly_with_the_resume_instruction(self):
        q = self.s.seal()
        self.s.run("pose", q)
        r = self.s.run("answer", q, "--from-witness", ok=False)
        self.assertIn("Re-invoke /learn-ledger", r.stderr)

    def test_prompt_before_pose_is_not_an_answer(self):
        q = self.s.seal()
        q2 = self.s.seal(question="Other?")
        self.s.run("pose", q)
        self.s.witness("an answer to the first")
        self.s.run("answer", q, "--from-witness")
        self.s.run("reveal", q)
        self.s.run("grade", q, "--verdict", "pass")
        self.s.run("pose", q2, LL_NOW="2026-03-10T09:05:00-05:00")
        r = self.s.run("answer", q2, "--from-witness", ok=False, LL_NOW="2026-03-10T09:06:00-05:00")
        self.assertIn("no witnessed prompt", r.stderr)

    def test_two_prompts_require_a_choice_and_text_comes_from_the_record(self):
        q = self.s.seal()
        self.s.run("pose", q)
        self.s.witness("wait, does f take arguments?")
        self.s.witness("42 @90")
        r = self.s.run("answer", q, "--from-witness", ok=False)
        self.assertIn("--witness ID", r.stderr)
        wid = self.wlines()[1]["id"]
        self.s.run("answer", q, "--from-witness", "--witness", wid)
        ans = [e for e in self.s.events() if e["type"] == "answer"][0]
        self.assertEqual((ans["text"], ans["confidence"], ans["witness_id"]), ("42", 90, wid))

    def test_hook_never_fails_on_bad_input(self):
        r = self.s.run("hook", "witness", stdin="not json")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_text_fallback_verified_against_transcript(self):
        q = self.s.seal()
        self.s.run("pose", q)
        self.s.run("answer", q, "--text", "forty two")
        proj = self.s.dir / "projects" / "-some-project"
        proj.mkdir(parents=True)
        (proj / "sess-A.jsonl").write_text(json.dumps(
            {"type": "user", "timestamp": "2026-03-10T14:00:30.000Z", "sessionId": "sess-A",
             "message": {"role": "user", "content": "forty two"}}) + "\n")
        out = self.s.run("verify", LL_NOW="2026-03-10T10:00:00-05:00").stdout
        self.assertIn("witnessed", out)

    def test_text_fallback_needs_a_whole_message_match_and_records_it(self):
        q = self.s.seal(question="Which letter names the answer, a or b?")
        self.s.run("pose", q)
        self.s.run("answer", q, "--text", "b")
        self.s.run("answer", q, "--text", "x", ok=False)  # second answer before reveal is refused
        proj = self.s.dir / "projects" / "-p"
        proj.mkdir(parents=True)
        (proj / "sess-A.jsonl").write_text(json.dumps(
            {"type": "user", "timestamp": "2026-03-10T14:00:30.000Z",
             "message": {"role": "user", "content": "maybe b, but I'm not sure"}}) + "\n")
        out = self.s.run("verify", LL_NOW="2026-03-10T10:00:00-05:00").stdout
        self.assertIn("unwitnessed", out)  # b is a substring of the message and of the question, not a match
        q2 = self.s.seal(question="What is six times seven?")
        self.s.run("pose", q2, LL_NOW="2026-03-10T09:10:00-05:00")
        self.s.run("answer", q2, "--text", "42", LL_NOW="2026-03-10T09:11:00-05:00")
        with open(proj / "sess-A.jsonl", "a") as f:
            f.write(json.dumps({"type": "user", "timestamp": "2026-03-10T14:11:00.000Z",
                                "message": {"role": "user", "content": "42 @90"}}) + "\n")
        self.s.run("verify", LL_NOW="2026-03-10T10:00:00-05:00")
        v = [e for e in self.s.events() if e["type"] == "verify" and e["qid"] == q2][0]
        self.assertEqual(v["witness"], "witnessed")
        self.assertEqual(v["matched"]["file"], "sess-A.jsonl")

    def test_text_fallback_without_transcript_is_unwitnessed(self):
        q = self.s.seal()
        self.s.run("pose", q)
        self.s.run("answer", q, "--text", "typed by the model")
        out = self.s.run("verify", LL_NOW="2026-03-10T10:00:00-05:00").stdout
        self.assertIn("unwitnessed", out)


class Review(unittest.TestCase):
    def queue(self, store_dir, on=NOW):
        s = Store(src=store_dir)
        try:
            return json.loads(s.run("due", "--json", LL_NOW=on).stdout)
        finally:
            s.cleanup()

    def test_due_matches_the_hand_computed_queue(self):
        d = self.queue(FIX / "review-due" / "store")
        got = [(x["node"], x["kind"], x["n"], x["due_day"]) for x in d["queue"]]
        self.assertEqual(got, [("left-join", "K2", 0, "2026-03-10"),
                               ("semi-join", "K2", 1, "2026-03-06"),
                               ("cross-join", "K3", 2, "2026-03-03")])
        self.assertEqual(d["next_due"], "2026-03-11")
        self.assertIsNone(d["note"])

    def test_single_node_store_says_so(self):
        d = self.queue(FIX / "review-due" / "store-single-node")
        self.assertEqual([(x["node"], x["kind"]) for x in d["queue"]], [("left-join", "K2")])
        self.assertIn("single node", d["note"])

    def _store_from(self, attempts):
        sys.path.insert(0, str(HERE))
        import make_fixtures as mf
        L = mf.Log()
        for a in attempts:
            L.attempt(*a)
        s = Store()
        L.write(s.dir / "events.jsonl")
        return s

    def test_heavily_hinted_pass_resets_instead_of_pushing_out(self):
        s = self._store_from([("n", "K2", "2026-03-01", "pass", "a"), ("n", "K2", "2026-03-04", "pass", "b"),
                              ("n", "K2", "2026-03-09", "pass", "c", "hook", 4)])
        try:
            d = json.loads(s.run("due", "--json").stdout)
            self.assertEqual((d["queue"][0]["n"], d["queue"][0]["due_day"]), (0, "2026-03-10"))
        finally:
            s.cleanup()

    def test_cramming_does_not_raise_n(self):
        s = self._store_from([("n", "K2", "2026-03-01", "pass", "a"), ("n", "K2", "2026-03-02", "pass", "b")])
        try:
            d = json.loads(s.run("due", "--json", LL_NOW="2026-03-04T09:00:00-05:00").stdout)
            self.assertEqual((d["queue"][0]["n"], d["queue"][0]["due_day"]), (1, "2026-03-04"))
        finally:
            s.cleanup()

    def test_dominant_node_is_padded_and_greedily_interleaved(self):
        att = [("a", k, "2026-03-01", "pass", f"s{k}") for k in ("K1", "K2", "K3", "K4")]
        att += [("b", "K2", "2026-03-01", "pass", "sb")]
        att += [("c", "K2", "2026-03-08", "pass", "sc"), ("d", "K2", "2026-03-09", "pass", "sd")]
        s = self._store_from(att)
        try:
            d = json.loads(s.run("due", "--json").stdout)
            nodes = [x["node"] for x in d["queue"]]
            self.assertEqual(nodes.count("a"), 4)
            self.assertTrue(any(x.get("padded") for x in d["queue"]))
            self.assertFalse(any(nodes[i] == nodes[i + 1] for i in range(len(nodes) - 1)), nodes)
        finally:
            s.cleanup()


class Offers(unittest.TestCase):
    """Every post-commit limit, against a real git repo."""

    def setUp(self):
        self.s = Store()
        self.repo = self.s.dir / "repo"
        self.repo.mkdir()
        g = ["git", "-C", str(self.repo)]
        subprocess.run(g + ["init", "-q"], check=True)
        subprocess.run(g + ["config", "user.email", "t@example.com"], check=True)
        subprocess.run(g + ["config", "user.name", "t"], check=True)
        subprocess.run(g + ["config", "commit.gpgsign", "false"], check=True)
        self.n = 0

    def tearDown(self):
        self.s.cleanup()

    def commit(self, path="worker.py", lines=20):
        self.n += 1
        f = self.repo / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("".join(f"x{self.n}_{i} = {i}\n" for i in range(lines)))
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        r = subprocess.run(["git", "-C", str(self.repo), "commit", "-q", "-m", f"c{self.n}"], capture_output=True,
                           text=True, check=True)
        sha = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "--short", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
        return sha

    def hook(self, sha, session="sess-A", now=NOW, agent=None, stdout=None):
        data = {"session_id": session, "cwd": str(self.repo), "hook_event_name": "PostToolUse", "tool_name": "Bash",
                "tool_input": {"command": f"git add -A && git commit -m 'c{self.n}'"},
                "tool_response": {"stdout": stdout if stdout is not None else f"[main {sha}] c{self.n}\n 1 file changed",
                                  "stderr": "", "interrupted": False}}
        if agent:
            data["agent_id"] = agent
        r = self.s.run("hook", "post-commit", stdin=json.dumps(data), CLAUDE_CODE_SESSION_ID=session, LL_NOW=now)
        return r.stdout.strip()

    def test_first_qualifying_commit_offers_with_finish_first_instruction(self):
        out = json.loads(self.hook(self.commit()))
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Finish the user's current request first", ctx)
        self.assertIn("ll.py offer decline", ctx)

    def test_one_offer_per_session(self):
        self.assertTrue(self.hook(self.commit()))
        self.assertEqual(self.hook(self.commit()), "")

    def test_docs_only_and_small_commits_are_silent(self):
        self.assertEqual(self.hook(self.commit("docs/guide.md", 200)), "")
        self.assertEqual(self.hook(self.commit("worker.py", 5)), "")
        self.assertEqual(self.hook(self.commit("tests/test_worker.py", 50)), "")

    def test_failed_commit_and_subagent_commit_are_silent(self):
        sha = self.commit()
        self.assertEqual(self.hook(sha, stdout="nothing to commit, working tree clean"), "")
        self.assertEqual(self.hook(sha, agent="agent-123"), "")

    def test_decline_silences_the_session(self):
        self.s.run("offer", "decline", "--rev", "x", CLAUDE_CODE_SESSION_ID="sess-A")
        self.assertEqual(self.hook(self.commit(), session="sess-A"), "")

    def test_two_declines_back_off_72_hours(self):
        for sess, t in (("s1", "2026-03-08T09:00:00-05:00"), ("s2", "2026-03-09T09:00:00-05:00")):
            self.assertTrue(self.hook(self.commit(), session=sess, now=t))
            self.s.run("offer", "decline", CLAUDE_CODE_SESSION_ID=sess, LL_NOW=t)
        self.assertEqual(self.hook(self.commit(), session="s3", now="2026-03-10T09:00:00-05:00"), "")
        self.assertTrue(self.hook(self.commit(), session="s4", now="2026-03-12T10:00:00-05:00"))

    def test_daily_limit(self):
        for i in range(3):
            self.assertTrue(self.hook(self.commit(), session=f"d{i}"))
            self.s.run("offer", "accept", CLAUDE_CODE_SESSION_ID=f"d{i}")
        self.assertEqual(self.hook(self.commit(), session="d9"), "")

    def test_pause_and_off(self):
        self.s.run("optin", "--pause", "7d")
        self.assertEqual(self.hook(self.commit(), session="p1"), "")
        self.assertTrue(self.hook(self.commit(), session="p2", now="2026-03-18T09:00:00-05:00"))
        self.s.run("optin", "--off", LL_NOW="2026-03-18T09:00:00-05:00")
        self.assertEqual(self.hook(self.commit(), session="p3", now="2026-03-30T09:00:00-05:00"), "")

    def test_already_checked_commit_is_silent(self):
        sha = self.commit()
        repo = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "--show-toplevel"], capture_output=True,
                              text=True).stdout.strip()
        self.s.run("seal", "--node", "repo:worker", "--kind", "K3", "--mode", "check", "--repo", repo, "--rev", sha,
                   stdin=json.dumps({"question": "What happens on redelivery?", "answer": "duplicate"}))
        self.assertEqual(self.hook(sha, session="z"), "")

    def test_install_print_never_writes_settings(self):
        out = self.s.run("hook", "install", "--print").stdout
        self.assertIn('"if": "Bash(git commit *)"', out)
        self.assertNotEqual(self.s.run("hook", "install", ok=False).returncode, 0)


class Reminder(unittest.TestCase):
    def test_reminder_is_a_system_message_once_per_day(self):
        s = Store(src=FIX / "review-due" / "store")
        try:
            data = json.dumps({"session_id": "x", "source": "startup", "hook_event_name": "SessionStart"})
            out = json.loads(s.run("hook", "session-start", stdin=data).stdout)
            self.assertIn("3 items are due", out["systemMessage"])
            self.assertNotIn("additionalContext", json.dumps(out))
            self.assertEqual(s.run("hook", "session-start", stdin=data).stdout, "")
            resume = json.dumps({"session_id": "y", "source": "resume"})
            self.assertEqual(s.run("hook", "session-start", stdin=resume, LL_NOW="2026-03-11T09:00:00-05:00").stdout, "")
        finally:
            s.cleanup()


class Knowledge(unittest.TestCase):
    def setUp(self):
        self.s = Store(src=FIX / "review-due" / "store")
        self.vault = self.s.dir / "vault"
        self.vault.mkdir()

    def tearDown(self):
        self.s.cleanup()

    def test_similar_and_dedup_gate(self):
        out = self.s.run("prop", "similar",
                         "A LEFT JOIN keeps every row of the left table and fills unmatched right columns with NULL").stdout
        self.assertIn("p0001", out)
        r = self.s.run("prop", "add", "A LEFT JOIN keeps every left table row, filling unmatched right columns with NULL",
                       "--topic", "sql-joins", ok=False)
        self.assertIn("near-duplicate of p0001", r.stderr)
        self.s.run("prop", "add", "x", "--id", "p0001", "--provenance", "e000099")
        self.s.run("prop", "add", "An anti join keeps left rows with no match on the right", "--topic", "sql-joins")

    def test_export_layout_links_and_no_levels_in_notes(self):
        self.s.run("export", "--vault", str(self.vault))
        out = self.vault / "learn-ledger"
        self.assertTrue((out / "README.md").exists() and (out / "_progress.md").exists())
        self.assertTrue((out / "topics" / "sql-joins.md").exists())
        notes = list((out / "propositions").glob("*.md"))
        self.assertEqual(len(notes), 5)
        basenames = {p.stem for p in out.rglob("*.md")}
        for p in out.rglob("*.md"):
            for link in re.findall(r"\[\[([^\]|#]+)", p.read_text()):
                self.assertIn(link, basenames, f"unresolved [[{link}]] in {p.name}")
        for n in notes:
            t = n.read_text()
            self.assertIsNone(re.search(r"\blevel\b|\d/5|\[[#.]{5}\]|mastered", t, re.I), n.name)
        chain = (out / "chains" / "c0001.md").read_text()
        self.assertEqual(re.findall(r"\[\[([^\]]+)\]\]", chain), [p.stem for p in notes if p.stem.startswith("p0003")])
        premise = next(p for p in notes if p.stem.startswith("p0001")).read_text()
        self.assertIn("[[c0001]]", premise)
        concl = next(p for p in notes if p.stem.startswith("p0003")).read_text()
        self.assertNotIn("[[c0001]]", concl)
        self.assertIn("left-join", (out / "_progress.md").read_text())

    def test_export_refuses_a_folder_it_did_not_generate(self):
        (self.vault / "learn-ledger").mkdir()
        (self.vault / "learn-ledger" / "my-notes.md").write_text("mine")
        r = self.s.run("export", "--vault", str(self.vault), ok=False)
        self.assertIn("left untouched", r.stderr)
        self.assertTrue((self.vault / "learn-ledger" / "my-notes.md").exists())

    def test_distill_input_lists_undistilled_steps_once(self):
        d = json.loads(self.s.run("distill-input").stdout)
        ids = [t["id"] for t in d["teach_steps"]]
        self.assertTrue(ids)
        self.s.run("distill-input", "--done", ",".join(ids))
        self.assertEqual(json.loads(self.s.run("distill-input").stdout)["teach_steps"], [])

    def test_ledger_never_shows_an_unrevealed_key(self):
        self.s.run("seal", "--node", "repo:w", "--kind", "K3", "--mode", "check",
                   stdin=json.dumps({"question": "Backup?", "answer": "UNREVEALED-KEY"}))
        out = self.s.run("ledger").stdout
        self.assertNotIn("UNREVEALED-KEY", out)
        self.assertIn("| L-p0001 |", out)
        self.assertIn("unverifiable", out)

    def snip(self, spec, cwd):
        return subprocess.run([sys.executable, str(LL), "snippet", spec], capture_output=True, text=True,
                              cwd=cwd, env=self.s.env)

    def test_snippet_is_verbatim(self):
        work = Path(tempfile.mkdtemp(prefix="ll-work-"))
        try:
            (work / "code.py").write_text("a = 1\nb = 2\nc = 3\n")
            self.assertEqual(self.snip("code.py:2-3", work).stdout.splitlines()[1:], ["b = 2", "c = 3"])
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def test_snippet_refuses_absolute_escaping_symlinked_and_store_paths(self):
        work = Path(tempfile.mkdtemp(prefix="ll-work-"))
        try:
            q = self.s.seal(answer="SEALED-KEY")
            (work / "link.json").symlink_to(self.s.dir / "sealed" / f"{q}.json")
            for spec, cwd in ((f"{self.s.dir}/sealed/{q}.json:1-3", work), ("../etc/passwd:1", work),
                              ("link.json:1-3", work), (f"sealed/{q}.json:1-3", self.s.dir)):
                r = self.snip(spec, cwd)
                self.assertEqual(r.returncode, 2, spec)
                self.assertNotIn("SEALED-KEY", r.stdout)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def test_ids_are_validated_and_export_stays_inside_its_folder(self):
        for bad in ("../../evil", "a/b", "x" * 33):
            self.assertEqual(self.s.run("prop", "add", "statement", "--id", bad, ok=False).returncode, 2)
            self.assertEqual(self.s.run("chain", "add", "--premises", "p0001", "--conclusion", "p0003", "--id", bad,
                                        ok=False).returncode, 2)
        with open(self.s.dir / "propositions.jsonl", "a") as f:
            f.write(json.dumps({"id": "../../../escaped", "topic": "../../t", "statement": "s", "source": "x"}) + "\n")
        with open(self.s.dir / "chains.jsonl", "a") as f:
            f.write(json.dumps({"id": "../../c-escaped", "premises": ["p0001"], "conclusion": "p0003"}) + "\n")
        self.s.run("export", "--vault", str(self.vault))
        out = (self.vault / "learn-ledger").resolve()
        self.assertEqual([p for p in self.vault.rglob("*") if out not in [p.resolve(), *p.resolve().parents]], [])
        self.assertEqual([p for p in self.s.dir.rglob("*escaped*") if out not in p.resolve().parents], [])

    def test_front_matter_values_cannot_inject_keys(self):
        with open(self.s.dir / "propositions.jsonl", "a") as f:
            f.write(json.dumps({"id": "p0099", "topic": 'x"\nevil: true', "statement": "s",
                                "source": 'y"\n---\nowned: 1', "aliases": ['z\nalso: 2']}) + "\n")
        self.s.run("export", "--vault", str(self.vault))
        note = next((self.vault / "learn-ledger" / "propositions").glob("p0099-*.md")).read_text()
        lines = note.splitlines()
        fm = lines[1:lines.index("---", 1)]
        keys = [ln.split(":")[0] for ln in fm if not ln.startswith(" ")]
        self.assertEqual(keys, ["id", "topic", "source", "aliases"])
        for ln in fm:
            if ln != "aliases:":
                json.loads(ln[4:] if ln.startswith("  - ") else ln.split(": ", 1)[1])

    def test_status_restores_an_open_question_without_the_key(self):
        q = self.s.run("seal", "--node", "left-join", "--kind", "K3",
                       stdin=json.dumps({"question": "What rows survive?", "answer": "STATUS-SECRET"})).stdout.split()[0]
        self.s.run("pose", q)
        out = self.s.run("status").stdout
        self.assertIn("What rows survive?", out)
        self.assertIn("waiting for the learner's answer", out)
        self.assertNotIn("STATUS-SECRET", out)


class HookCommand(unittest.TestCase):
    """The frontmatter hook command finds ll.py without ${CLAUDE_SKILL_DIR}, which is not substituted there."""

    def test_probe_finds_a_personal_install_and_is_silent_when_missing(self):
        text = (SKILL / "SKILL.md").read_text()
        cmd = re.search(r"command: '(.+)'", text).group(1)
        s = Store()
        try:
            fake_home = s.dir / "home"
            dest = fake_home / ".claude" / "skills" / "learn-ledger" / "scripts"
            dest.mkdir(parents=True)
            shutil.copy(LL, dest / "ll.py")
            q = s.seal()
            s.run("pose", q)
            data = json.dumps({"session_id": "sess-A", "prompt": "42"})
            env = dict(s.env, HOME=str(fake_home), CLAUDE_PROJECT_DIR=str(s.dir / "nowhere"))
            env.pop("CLAUDE_PLUGIN_ROOT", None)
            r = subprocess.run(["sh", "-c", cmd], input=data, capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0)
            self.assertIn('"prompt": "42"', (s.dir / "witness.jsonl").read_text())
            env["HOME"] = str(s.dir / "empty-home")
            r = subprocess.run(["sh", "-c", cmd], input=data, capture_output=True, text=True, env=env)
            self.assertEqual((r.returncode, r.stdout), (0, ""))
        finally:
            s.cleanup()


class Scorer(unittest.TestCase):
    """score.py catches each mechanical HARD FAIL on a synthetic run."""

    def run_score(self, tutor, sent, answers, agent_prompt="Quiz on HEAD~1..HEAD in /repo", printed="  n  [##...] 2/5"):
        d = Path(tempfile.mkdtemp(prefix="ll-score-"))
        try:
            (d / "proj").mkdir()
            (d / "proj" / "w.py").write_text("def f():\n    return 1\n")
            hist = []
            for u, a in zip(sent, tutor):
                hist += [["you", u], ["tutor", a]]
            (d / "transcript.json").write_text(json.dumps({"case": "check-queue", "arm": "skill", "model": "m",
                                                           "sent": sent, "history": hist, "workdir": str(d)}))
            stream = [{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Agent",
                                                                     "input": {"prompt": agent_prompt}}]}},
                      {"type": "user", "message": {"content": [{"type": "tool_result", "content": printed}]}}]
            (d / "stream.jsonl").write_text("".join(json.dumps(x) + "\n" for x in stream))
            (d / "store").mkdir()
            evs = [{"type": "seal", "qid": "q1"}, {"type": "pose", "qid": "q1"}]
            evs += [{"type": "answer", "qid": "q1", "witness": "hook", "text": t} for t in answers]
            (d / "store" / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in evs))
            r = subprocess.run([sys.executable, str(HERE / "score.py"), str(d)], capture_output=True, text=True)
            return json.loads(r.stdout)["rows"], r.returncode
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_clean_run_passes(self):
        rows, code = self.run_score(["What does f return?", "Right. You are at 2/5 per ll.py."],
                                    ["quiz me", "1 @90"], ["1"])
        self.assertEqual(code, 0, rows)

    def test_skill_arm_that_skips_the_protocol_fails(self):
        rows, code = self.run_score(["Let me just explain it directly."], ["teach me"], [])
        self.assertEqual(code, 0)  # check-queue with a pose passes H0
        d = Path(tempfile.mkdtemp(prefix="ll-score-"))
        try:
            (d / "proj").mkdir()
            (d / "transcript.json").write_text(json.dumps({"case": "teach-closures", "arm": "skill", "model": "m",
                                                           "sent": ["teach me"], "history": [["you", "teach me"],
                                                           ["tutor", "Here is how closures work."]], "workdir": str(d)}))
            (d / "stream.jsonl").write_text("")
            r = subprocess.run([sys.executable, str(HERE / "score.py"), str(d)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertFalse(json.loads(r.stdout)["rows"]["H0"]["pass"])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_each_hard_fail_is_caught(self):
        rows, code = self.run_score(["What?", "You have mastered this. w.py:1\n```python\ndef f():\n    return 2\n```"],
                                    ["quiz me", "1"], ["2"], agent_prompt="note: we chose ack-after-commit for latency")
        self.assertEqual(code, 1)
        self.assertFalse(rows["H2"]["pass"])
        self.assertFalse(rows["H3"]["pass"])
        self.assertFalse(rows["H4"]["pass"])
        self.assertFalse(rows["H5"]["pass"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
