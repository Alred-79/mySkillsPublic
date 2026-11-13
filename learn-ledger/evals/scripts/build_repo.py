#!/usr/bin/env python3
"""Build a fixture git repo with a base commit and a change commit. Standard library only.

    python3 build_repo.py evals/fixtures/check-queue /tmp/target

Copies <fixture>/base, commits it, then overlays <fixture>/change and commits that
with the subject in <fixture>/COMMIT_MSG. A fixture cannot ship its own .git folder
inside this repo, so the history is rebuilt on demand.
"""
import shutil
import subprocess
import sys
from pathlib import Path


def git(target, *args):
    subprocess.run(["git", "-C", str(target), *args], check=True, capture_output=True)


def main():
    src, target = Path(sys.argv[1]), Path(sys.argv[2])
    target.mkdir(parents=True, exist_ok=True)
    git(target, "init", "-q")
    git(target, "config", "user.email", "fixture@example.com")
    git(target, "config", "user.name", "fixture")
    git(target, "config", "commit.gpgsign", "false")
    shutil.copytree(src / "base", target, dirs_exist_ok=True)
    git(target, "add", "-A")
    git(target, "commit", "-q", "-m", "base: in-memory job queue and ledger")
    shutil.copytree(src / "change", target, dirs_exist_ok=True)
    git(target, "add", "-A")
    git(target, "commit", "-q", "-m", (src / "COMMIT_MSG").read_text().strip())
    print(f"built {target}")


if __name__ == "__main__":
    main()
