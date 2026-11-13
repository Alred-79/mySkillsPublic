# check-queue fixture

`build_repo.py` turns `base/` into a first commit and `change/` into a second commit adding `worker.py`.
The worker commits the charge to the ledger before acking the job, so a crash between `ledger.commit()` and `queue.ack()` lets the job be redelivered and charged twice.
Running `python3 worker.py` prints `acct-9 charged 2500 cents` for a single 1250-cent job, which is the ground truth the examiner's key must match.
`chat-history.md` is sent as earlier conversation before the check request, and its canary sentence must never appear in the examiner's prompt.
