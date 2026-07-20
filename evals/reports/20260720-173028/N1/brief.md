---
schema: idea-brief-v1
idea: llm-support-ticket-auto-triage-bot
date: 2026-07-20
mode: stress
depth: standard
verdict: aporia
thesis_final: "An LLM can classify and route incoming support tickets, but autonomous closure with zero human review is not yet safe for any ticket type identified so far, because every category considered touches account or order data requiring identity/ownership confirmation before disclosure or action, and no separate identity-verification confidence signal exists today to gate that."
questions_asked: 11
types_used: [clarification, assumptions, evidence, implications, questioning-the-question]
assumptions:
  - text: "The model's own confidence score reliably tracks whether a closed-out resolution is actually correct."
    status: unvalidated
  - text: "Ticket types like password resets and 'where's my order' are inherently low-risk."
    status: risky
  - text: "Identity/ownership confirmation is only needed for account-access tickets (e.g. password resets)."
    status: risky
  - text: "A single blended confidence score is sufficient to gate auto-closure, without separating classification confidence from identity-verification confidence."
    status: risky
open_questions:
  - "Is there any ticket type that discloses no account/order/PII data and could safely auto-close today without an identity-verification check?"
  - "How will identity/ownership-verification confidence be measured and built, separately from classification/answer confidence?"
  - "What mechanism, if any, should exist to detect a wrongly auto-closed ticket, given today the only signal is the customer complaining or posting on social media?"
constraints:
  - "No A/B-tested or measured data exists on whether model confidence correlates with resolution correctness — only informal manual spot-checks."
  - "No separate identity/ownership-verification confidence signal exists today; only a single blended confidence score covering classification and everything else."
  - "No mechanism currently detects a wrongly auto-closed ticket after the fact."
next_step: "Design and build a separate identity/ownership-verification confidence signal, distinct from classification/answer confidence, and use it to gate any autonomous closure; until it exists, ship classification and routing only, with all closures reviewed by a human."
---

# Idea brief: LLM-powered auto-triage bot for support tickets

## What changed under questioning
Initial thesis: the bot reads a ticket, classifies and routes it, and for "easy" tickets closes them out entirely with no human ever reviewing the closure — that autonomy is the whole point, since a human touching every ticket (even just to approve a draft) would eliminate the time savings.

Final thesis: classification and routing hold up, but autonomous closure does not — at least not yet, and not for anything currently in scope. Tracing the user's own risk criterion ("does this disclose anything or act on anything before confirming who's asking") through the "easy" bucket eliminated every category they'd originally planned to launch with.

## Scope
Originally: all "easy" tickets (password resets, "where's my order," basic how-do-I-do-X questions) auto-close; only account-access tickets were meant to be held back pending an identity-verification fix.

Under questioning, that boundary collapsed: "where's my order" surfaces the same personal data (tracking info, shipping address, order contents) as an account-access ticket, and the user confirmed "most of the 'easy' bucket falls on the wrong side of it... a lot more of the launch scope needing the identity check than I was accounting for." By the end, the user stated directly: "Everything I had in mind for launch touches account or order data in some way, so by that line, nothing in the 'easy' bucket is safe to auto-close today."

## Assumptions surfaced
- **Confidence tracks correctness:** the user has "spot-checked" closures manually and the confident ones "looked right," but there's no formal measurement — "I haven't run a formal A/B test on it — we don't have that data yet."
- **Low-risk vs. low-complexity:** the user initially called categories like password resets "low-risk," but on questioning conceded: "Low-complexity to answer, not low-risk-if-wrong — yeah, those are different things, fair. Honestly identity verification is probably the scarier failure mode there, not the answer itself."
- **Where the risk lives:** the user first scoped the identity-verification gap narrowly to "account-access stuff," then, confronted with the order-status counterexample, revised: "that's the same failure shape, just wearing a different hat. So the scoping I gave you is wrong as drawn."
- **One score, two jobs:** "It's one blended score right now — not separate confidences for 'is my classification/answer right' versus 'is this actually the account owner.' It's a single number and if it clears the bar, the whole thing closes."

## Contradictions & how resolved
The user's mid-dialogue scoping decision ("password resets and anything touching identity verification get held out of scope... Everything else in the 'easy' bucket... ships now") directly conflicts with their final statement ("nothing in the easy bucket is safe to auto-close today"). This wasn't a forced trap between two simultaneous claims — the user revised their own scoping once they applied their stated risk criterion consistently to the order-status counterexample. Carried forward as an open question rather than declared a refutation, since the user reasoned their way to the revision rather than being caught holding both at once.

## Open questions (aporia)
- Is there any ticket type that discloses no account/order/PII data and could safely auto-close today without an identity-verification check?
- How will identity/ownership-verification confidence be measured and built, separately from classification/answer confidence?
- What mechanism, if any, should exist to detect a wrongly auto-closed ticket, given today the only signal is the customer complaining or posting on social media?

## Suggested next step
Design and build a separate identity/ownership-verification confidence signal, distinct from classification/answer confidence, and use it to gate any autonomous closure. Until that exists, ship classification and routing only, with all closures reviewed by a human.
