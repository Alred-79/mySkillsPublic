"""A tiny at-least-once job queue, in memory.

A received job is invisible until it is acked. If it is not acked within
visibility_timeout seconds, it becomes visible again and is redelivered.
"""
import time


class JobQueue:
    def __init__(self, visibility_timeout=30.0):
        self.visibility_timeout = visibility_timeout
        self._jobs = {}
        self._inflight = {}

    def put(self, job_id, payload):
        self._jobs[job_id] = payload

    def receive(self, now=None):
        now = time.monotonic() if now is None else now
        for job_id, deadline in list(self._inflight.items()):
            if deadline <= now:
                del self._inflight[job_id]
        for job_id, payload in self._jobs.items():
            if job_id not in self._inflight:
                self._inflight[job_id] = now + self.visibility_timeout
                return job_id, payload
        return None

    def ack(self, job_id):
        self._jobs.pop(job_id, None)
        self._inflight.pop(job_id, None)
