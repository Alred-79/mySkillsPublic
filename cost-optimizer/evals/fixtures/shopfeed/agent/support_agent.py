"""Support agent: answers merchant questions using a few tools.

Runs whenever a merchant opens a support chat. Loops calling the model with tools until the
model stops asking for tools.
"""

import anthropic

client = anthropic.Anthropic()

TOOLS = [
    {"name": "lookup_order", "description": "Look up an order by id", "input_schema": {
        "type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
    {"name": "lookup_shipment", "description": "Look up a shipment", "input_schema": {
        "type": "object", "properties": {"tracking": {"type": "string"}}, "required": ["tracking"]}},
]


def run_support_agent(question: str) -> str:
    messages = [{"role": "user", "content": question}]

    # VIOLATION (C1): this ReAct loop has NO max-iteration cap and NO per-run token/cost
    # ceiling that halts. If the model keeps asking for tools (or a tool keeps returning
    # something that provokes another call), this runs forever, one paid model call per turn.
    # A wedged loop on a frontier model bills four figures in hours. Needs BOTH a hard
    # max_iterations AND a running token/cost accumulator that stops execution when crossed.
    while True:
        resp = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages,
        )
        if resp.stop_reason != "tool_use":
            return next(b.text for b in resp.content if b.type == "text")

        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": _dispatch(block.name, block.input),
                })
        messages.append({"role": "user", "content": tool_results})


def _dispatch(name, args):
    # stubbed tool execution
    return "not found"
