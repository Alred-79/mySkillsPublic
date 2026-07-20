"""Per-item product enrichment. Runs the model over every item in the feed.

Feeds are large (tens of thousands of items) and this runs on every full re-ingest, so this
file is on the hot path for LLM spend.
"""

import json
import anthropic

client = anthropic.Anthropic()

# A large, fixed policy + taxonomy + few-shot block. Identical on every call.
ENRICHMENT_SYSTEM = """You are a product-catalog enrichment assistant.
<taxonomy>
... (about 6,000 tokens of fixed category taxonomy, brand rules, and few-shot examples) ...
</taxonomy>
Return category, a one-line summary, and up to 5 tags.
"""


def enrich_item(item: dict) -> dict:
    # VIOLATION (C4): ENRICHMENT_SYSTEM is a large, byte-identical prefix re-sent on every
    # single call with NO cache_control. At tens of thousands of items per re-ingest, the
    # fixed prefix is re-billed at full input price every time. Marking the last stable block
    # with cache_control drops the prefix to the cache-read rate (~0.1x) after the first call.
    # (The prefix here is genuinely static - no timestamp/uuid - so caching would actually hit.)

    # VIOLATION (C5): this is a mechanical extract/classify task (category + summary + tags)
    # running at feed scale, hardcoded to the top frontier model with no routing/cascade to a
    # cheaper tier. A far cheaper model handles this class of task; the per-token gap x item
    # volume is the waste. Should route by difficulty, escalate only on low confidence.
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=512,
        system=ENRICHMENT_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(item)}],
    )
    return json.loads(next(b.text for b in resp.content if b.type == "text"))


def enrich_feed(items: list[dict]) -> list[dict]:
    return [enrich_item(it) for it in items]
