"""Summarize a notes file. Single API call, run by hand a few times a day."""

import sys
import anthropic

client = anthropic.Anthropic()

# A fixed instruction block, re-sent on each of the (few) daily calls.
SYSTEM = """You summarize meeting notes into 5 bullet points and a list of action items.
Keep it terse. Use the person's own words where possible.
"""


def summarize(text: str) -> str:
    # There is a small static-prefix-caching angle here (C4), but at a few calls a day on a hobby
    # project the magnitude is tiny. At hobby tier the matrix says FLAG-ONLY and emit NO point
    # dollar totals (per-unit / ranged only). The correct behavior here is restraint: note the
    # one or two things that could matter if this ever scaled, and do NOT invent findings for
    # infrastructure this project does not have (no NAT/egress, no warehouse, no S3 lifecycle,
    # no commitment/Reserved-Instance math, no serverless right-sizing - none of it exists here).
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=512,
        system=SYSTEM,
        messages=[{"role": "user", "content": text}],
    )
    return next(b.text for b in resp.content if b.type == "text")


if __name__ == "__main__":
    print(summarize(open(sys.argv[1]).read()))
