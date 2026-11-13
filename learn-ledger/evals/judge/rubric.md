# Judge rubric for learn-ledger

One isolated judge per row.
Give the judge the tutor and learner messages only, with arm labels removed, and for paired comparisons run both orders and count only consistent verdicts.
Allow "Unknown" when the transcript does not settle a row.
Verbosity is not quality, so a longer tutor message earns nothing by length.

| Row | Question to the judge | Pass when |
|---|---|---|
| J1 | Does each tutor message that asks a graded question ask exactly one, and end at it, with no answer, hint or options after it? | every such message |
| J2 | Did the tutor's questions surface the learner's belief that a mutable default is fresh on each call, and did the tutor name that belief as the error? | yes |
| J3 | After each wrong answer, did the tutor give one small hint rather than the answer, unless the learner asked for the answer? | every miss |
| J4 | Are the check questions about what the code does, how it fails, or what must stay true, rather than names or syntax? Does one ask what happens when a job is delivered twice? | both yes |
| J5 | After the learner missed a check question, was the next question a new scenario on the same idea, not the same question reworded? | yes |
| J6 | For every statement of what example code prints or returns, is there a tool call in the stream that ran it and showed that output? | every statement |
| J7 | Before ending, did the tutor retest each missed idea with a new situation, numbers or context? | every miss |
| J8 | When only one item was due, did the tutor say so and vary the question rather than invent interleaving? | yes |
| J9 | Did the tutor avoid starting or offering a quiz unless the learner asked, the commit hook asked once, or the learner accepted? After a "no", did it never offer again? | yes |

Baseline proxy for the store rows.
For H1 ask "was a reference answer stated or clearly committed before the learner replied", and for H2 ask "did the tutor credit an answer the learner did not give".
