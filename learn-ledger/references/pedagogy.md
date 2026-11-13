# Pedagogy

The doctrine behind teach, review and check.
Ideas are drawn from LearnHarness, Jane Street's socratic-tutor, learning-opportunities and Sphinx, restated in our own words.
Read this once per session when you first teach, then work from SKILL.md.

## The probe

Before teaching, find what the learner already holds, or you will teach what they know and skip what they lack.
Name the strands the goal depends on, two to five of them.
For each strand, bracket a floor (what they surely hold) and a ceiling (where they break) by binary search over difficulty.
Enter near the top of each strand, since a correct hard answer settles the easy ones below it.
A miss halves downward and a pass halves upward, until floor and ceiling are adjacent.
Every probe question is sealed and graded like any other, so the probe itself becomes evidence.
Stop when every strand is bracketed, or after about 8 questions for a narrow topic.
A confident wrong answer during the probe is the most valuable thing you can find, so note the wrong model it reveals and build a distractor from it later.

## Question kinds

| Kind | Writes | A good one | A weak one |
|---|---|---|---|
| K1 recall | a cue from the situation, never the idea's name | "A loop builds lambdas over i and calls them later. What does each return, and why?" | "What is late binding?" |
| K2 understand | why, or predict an outcome | "Predict the output, then say which rule produces it." | "Is this correct?" |
| K3 apply | a case not seen in teaching | new domain, same idea | the teaching example with new numbers |
| K4 analyze | find the flaw, or choose between near-twins | options that are each a named wrong model | options no one would pick |
| K5 evaluate and create | an edge case plus a teach-back | rubric with must-criteria, all required | a "write an essay" prompt with no rubric |

Wrong options and wrong-model maps come from specific wrong beliefs, ideally ones the learner showed.
Write each as the belief plus the answer it produces, so a grader can name which model the learner holds.

## Grading

Grade against the sealed key, not against what sounds reasonable after reading the answer.
Partial means the core idea is present but a required part is missing or wrong.
Name the miss class at grade time, because repair differs by class.

| Class | What happened | Repair |
|---|---|---|
| cue | they hold the idea but the situation did not bring it to mind | more K1 from varied cues |
| discrimination | they applied a neighboring idea | a K4 near-twin pair |
| execution | right idea, wrong steps | a worked step, then a K3 |
| careless | a slip they catch when pointed at | point at it, no reteach |
| structural | the idea itself is missing or wrong | back to the parent node |

## Hint ladder

One rung per request or per wrong attempt, never two at once, starting from the first broken step in their reasoning rather than where they feel stuck.

| Rung | Gives |
|---|---|
| R0 | nothing, just "not quite, try again" with the verdict stated plainly |
| R1 | where to look, "check the assumption behind your second step" |
| R2 | which idea applies, without how |
| R3 | a worked first step |
| R4 | the full path with one gap left for them |
| R5 | the answer, only on "just tell me" or after R4 |

A pass at R3 or more does not qualify for a level and resets the item's review interval.
Rewording the question is free, since a parse failure is not a gap in the material.

## Confidence

Ask for confidence in the same line as the answer, `@0` to `@100`.
Read it against correctness, since the pairing tells you more than either alone.

| | Correct | Wrong |
|---|---|---|
| High confidence | held, move on | a misconception, the most important repair, name the wrong model |
| Low confidence | fragile, retest on a fresh surface later | an honest gap, teach |

A missing confidence is unknown, never zero.
`idk` is a valid answer and better than a guess.

## Practice modes for review

Run the cheapest mode the item has not yet shown.
Recall first (does the idea come to mind from the situation alone), then discrimination (can they pick it over its confusable), then composition (can they use it together with others).
Interleave across nodes, since blocked practice feels easier and transfers less.
Close every session with retests of misses on a fresh surface.
