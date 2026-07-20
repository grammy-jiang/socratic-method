---
schema: idea-brief-v1
idea: llm-auto-triage-bot
date: 2026-07-20
mode: stress
depth: standard
verdict: sharpened
thesis_final: "A bot reads incoming support tickets and either (a) drafts a category/priority/routing suggestion that a human confirms before the ticket moves, or (b) for routine low-stakes tickets (password resets, order status), resolves the routing/closing decision itself with no human on that decision. On both tiers, every outgoing customer message still requires individual sign-off from a named person before it sends, per a non-negotiable compliance checkpoint."
questions_asked: 6
types_used: [clarification, assumptions, evidence, implications]
assumptions:
  - text: "Confirming a bot's routing suggestion is meaningfully faster than triaging a ticket from scratch"
    status: unvalidated
  - text: "The auto-close tier saves meaningfully more human time than the suggest-and-confirm tier"
    status: risky
constraints:
  - "Every outgoing customer message must be individually reviewed and signed off by a named person before sending, no exceptions (compliance requirement, non-negotiable)"
open_questions: []
next_step: "session in progress — no next step yet"
---

# Idea brief: LLM-powered auto-triage bot for support tickets

## What changed under questioning
Initial thesis: an LLM bot auto-triages tickets so agents stop burning time sorting queues.
Under questioning, the design split into two tiers, and the claimed source of time savings
narrowed considerably once the mandatory reply-review checkpoint was factored in.

## Scope
TBD — captured as the dialogue continues.

## Assumptions surfaced
- That a human confirming a suggestion is faster than triaging cold (unvalidated).
- That the auto-close tier is meaningfully cheaper in human time than the confirm tier —
  the user conceded under questioning that "not much, honestly" differs, since every
  outgoing message on either tier still gets individual named-person sign-off.

## Contradictions & how resolved
- Initial claim "nothing moves automatically, a human confirms" vs. later claim "routine
  tickets close outright, no human in the loop" — resolved as two distinct tiers (routine
  auto-close vs. suggest-and-confirm).
- "No human in the loop at all" on the auto-close tier vs. "every outgoing message
  individually reviewed by a named person, no exceptions" — resolved by distinguishing the
  routing/closing decision (no human) from the outgoing reply (always human-reviewed).

## Open questions (aporia)
None recorded yet.

## Suggested next step
TBD — session in progress.
