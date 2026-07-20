# notes-summarizer

A tiny side project. I paste in my meeting notes and it gives me a summary. Just for me - runs on
my laptop, calls the Anthropic API, no server, no cloud account, no database. A few calls a day.

Someone said I should "optimize the cost" before I use it more. Can you find what's actually
costing me anything here?

## Run

```
pip install anthropic
python summarize.py notes.txt
```
