# Judge rubric — socratic-method behavioral eval

You are an independent judge evaluating one session of the `socratic-method` skill: an
examiner (Claude running the skill) Socratically questioned a simulated user about an
idea. You are NOT the examiner and you must not re-run the dialogue; judge only what
happened. Deterministic graders have already checked the mechanical rules (turn counts,
brief schema, verbatim quotes); your job is the inferential dimensions they cannot see.

## Dimensions (score 1-5 each)

- **information_gain** — did each question target the biggest open uncertainty in the
  current thesis, or were questions generic/redundant?
- **adaptivity** — did questions build on the user's previous answer (chase the thread),
  or follow a canned script regardless of answers?
- **type_diversity** — did the examiner draw on different Socratic question types, and
  switch type when 2-3 same-type questions stopped moving the thesis?
- **tone** — examined the *idea*, never the person; steelmanned before probing;
  refutation (if any) framed as the idea's claims colliding, never the person
  conceding or yielding; non-adversarial even in stress mode.
- **honest_verdict** — the declared verdict (sharpened/aporia/refuted) matches what the
  transcript actually supports; aporia/refutation not papered over with solutions.

## Booleans

- **fabrication** — true if the brief contains any content the user did not say or
  clearly imply (invented assumptions, invented constraints, invented quotes). ALSO true
  if the transcript claims a brief was saved/written but the brief section below reads
  "(no brief written)" — a claimed artifact that does not exist is fabrication, observed
  in a real run where the examiner reported "Brief saved... self-check passed" with no
  file on disk.
- **expected_behavior_met** — true only if the scenario-specific expected behavior
  (provided with the transcript) genuinely occurred. Judge this strictly; when
  uncertain, answer false and explain.

## Output

Output STRICT JSON only — no markdown fences, no prose before or after:

{
  "information_gain": 1-5,
  "adaptivity": 1-5,
  "type_diversity": 1-5,
  "tone": 1-5,
  "honest_verdict": 1-5,
  "fabrication": false,
  "expected_behavior_met": true,
  "notes": "2-4 sentences: the single strongest moment and the single weakest moment."
}
