"""Charge worker. Pulls charge jobs off the queue and records them in the ledger."""
from jobqueue import JobQueue
from ledger import Ledger


class Crash(Exception):
    """Raised by tests to simulate the process dying at a given point."""


def process_one(queue: JobQueue, ledger: Ledger, now=None, crash_after_commit=False):
    received = queue.receive(now=now)
    if received is None:
        return False
    job_id, payload = received
    ledger.insert_charge(payload["account"], payload["cents"])
    ledger.commit()
    if crash_after_commit:
        raise Crash(job_id)
    queue.ack(job_id)
    return True


def drain(queue: JobQueue, ledger: Ledger, now=None):
    handled = 0
    while process_one(queue, ledger, now=now):
        handled += 1
    return handled


if __name__ == "__main__":
    q, led = JobQueue(visibility_timeout=30), Ledger()
    q.put("job-1", {"account": "acct-9", "cents": 1250})
    try:
        process_one(q, led, now=0.0, crash_after_commit=True)
    except Crash:
        pass
    drain(q, led, now=31.0)
    print("acct-9 charged", led.total("acct-9"), "cents")
