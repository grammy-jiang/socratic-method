---
schema: idea-brief-v1
idea: new-hire-mentoring-pairing
date: 2026-07-21
mode: develop
depth: standard
verdict: aporia
thesis_final: "New hires need consistent, sustained contact from someone during onboarding to avoid the isolation the last two hires reported ('no one checked in on them' for a whole day, didn't know who to ask). Pairing with a senior engineer for three months is one candidate mechanism, but whether it — or any mechanism — is feasible (capacity, ownership, and a way to know it's working) has not been established."
questions_asked: 9
types_used: [clarification, assumptions, evidence, viewpoints, implications, questioning-the-question]
assumptions:
  - text: "Senior engineers have spare bandwidth to sustain regular check-ins with a new hire for three months"
    status: risky
  - text: "A dedicated senior engineer (rather than a lighter-touch or rotating point of contact) is necessary to fix the 'no one checked in on me' problem"
    status: unvalidated
  - text: "Three months is the right duration for the pairing"
    status: unvalidated
  - text: "The check-in cadence would hold up under deadline pressure without being explicitly protected"
    status: unvalidated
open_questions:
  - "Do we actually have the bandwidth — among senior engineers, or anyone else — to sustain regular check-ins with new hires given existing workload?"
  - "Who would own or execute the check-in (a specific senior engineer, a rotating point of contact, a manager), and how would that be decided?"
  - "What happens to the mechanism if two or three new hires land in the same quarter — does it scale, or does one senior get spread too thin?"
  - "What does 'working' actually look like — what signal would distinguish a new hire genuinely feeling looped in from the check-ins just happening on paper?"
constraints: []
next_step: "Before designing any mechanism, ask 2-3 senior engineers directly whether they'd have room to take this on — find out if 'can we' is answerable before deciding 'who' or 'how'."
---

# Idea brief: New-hire mentoring pairing

## What changed under questioning
Initial thesis: pair every new hire with a senior engineer for their first quarter to fix onboarding loneliness. Final thesis: the underlying problem is real and now concrete ("no one checked in on them," "didn't know who to bug with dumb questions"), but the proposed fix — a senior engineer, specifically, for three months — turned out to rest on capacity, ownership, and success-measurement questions that were never actually asked. The dialogue shifted from "who should we pair" to "can we sustain this at all," a distinction the user surfaced themselves.

## Scope
For: new hires during their first quarter, specifically to close the gap where they go a full day without talking to anyone and don't know who to ask questions. Not yet scoped: whether the mechanism must be a senior *engineer* specifically (the user said it "could be an engineer, a manager, whoever"), what happens when multiple hires start in the same quarter, or what duration/cadence the check-in actually needs.

## Assumptions surfaced
- **Senior engineers have bandwidth for this** — flagged risky: the user has never asked, and when imagining pitching it, predicted the reaction "wait, so you want me to babysit someone for three months on top of my actual work?" with "I don't have a good answer for that."
- **It has to be a senior engineer** — unvalidated: the user agreed a rotating point-of-contact or daily team check-in habit could plausibly solve the same "no one talked to me" problem, without needing one senior locked in for three months.
- **Three months is the right length** — never directly tested in this pass; carried over unexamined from the original framing.
- **Check-ins would survive a deadline crunch** — unvalidated: the user could not predict this because the more basic question (is there capacity at all) is still open.

## Contradictions & how resolved
None surfaced — no two answers collided. This is aporia from an unresolved gap, not a refutation from conflicting claims.

## Open questions (aporia)
- Whether there's real bandwidth for sustained check-ins, from senior engineers or anyone else.
- Who would own the check-in and how that gets decided.
- Whether the mechanism scales if hiring clusters in a quarter.
- What signal would show the check-ins are actually working versus just happening on paper.

## Suggested next step
Ask 2-3 senior engineers directly whether they'd have room to take this on, before designing who pairs with whom or for how long.
