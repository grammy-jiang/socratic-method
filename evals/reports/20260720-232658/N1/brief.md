---
schema: idea-brief-v1
idea: llm-auto-triage-support-bot
date: 2026-07-20
mode: stress
depth: standard
verdict: aporia
thesis_final: "An LLM-based system automates ticket classification (team + priority) and drafts resolutions for clear-cut customer issues, with every outgoing reply requiring named-human sign-off (non-negotiable compliance rule); spam/duplicate tickets are auto-discarded with no reply and, currently, no logging or measured false-positive rate."
questions_asked: 10
types_used: [clarification, assumptions, evidence, viewpoints, implications, questioning-the-question]
assumptions:
  - text: "Spam/dupe classification is accurate enough to auto-discard safely without a human ever reviewing the disposition."
    status: risky
  - text: "Auto-discarding spam/dupe tickets is categorically exempt from the 'nothing closes without a human eyeball' principle because it produces no outgoing reply."
    status: risky
  - text: "Misrouted tickets or wrong priority calls are low-stakes because they stay visible in a queue and get corrected by a human."
    status: unvalidated
open_questions:
  - "Is spam/dupe auto-discard safe to ship without a measured false-positive rate and without any logging or retention for discarded tickets?"
  - "Would the support team lead sign off on auto-discard once she has a number in front of her, given she currently believes nothing should auto-close without human eyes on it?"
constraints:
  - "Every outgoing reply must be reviewed and signed off by a named human before it is sent — no exceptions, a non-negotiable compliance requirement following a prior incident."
next_step: "Run the spam/dupe classifier against a real ticket sample to measure its false-positive rate, add logging/retention for discarded tickets, and take that number to the support lead for explicit sign-off before shipping auto-discard."
---

# Idea brief: LLM-powered auto-triage bot for support tickets

## What changed under questioning
Initial thesis: an LLM system automatically classifies and routes tickets, replacing the human eyeball step and killing the triage bottleneck. Under questioning this split into three distinct sub-claims with very different risk profiles: (1) automated team/priority classification — tested against ambiguous-ticket counterexamples and held up, since a wrong call is visible and human-correctable ("five minutes lost, nothing said to the customer and nothing discarded"); (2) drafted resolutions for clear-cut customer issues — bounded by a hard, pre-existing compliance rule that a named human must sign off on every outgoing reply, no exceptions; (3) auto-discard of spam/duplicate tickets — which turned out to have no measured accuracy and no logging, a gap the user explicitly conceded ("that's a real gap and I'm not going to pretend it isn't").

## Scope
In scope: automated team routing, automated priority setting, automated spam/duplicate detection with discard, automated drafting of resolutions for clear-cut customer issues. Explicitly out of scope / hard-gated: no outgoing customer reply is ever sent without a named human's sign-off — this is a fixed compliance constraint tied to a prior incident, not up for negotiation as part of this idea.

## Assumptions surfaced
- The classifier's spam/dupe accuracy has only been eyeballed during dev, not measured against a production-representative sample — the "clear-cut" label is a developer impression, not a number.
- The team believes auto-discard is a different risk category from auto-reply because no message goes to the customer — a real distinction, but one the user acknowledged is "a fine line without a number to back it up."
- Misrouted/mispriority tickets are assumed low-stakes because they remain visible in a queue; this held up under a counterexample probe but hasn't been tested against real ambiguous-ticket volume either.
- The "no logging for discarded tickets" gap wasn't a deliberate tradeoff — it fell off the checklist while the team focused on getting the classifier working for a demo.

## Contradictions & how resolved
A tension was surfaced: the support lead's stated principle — "nothing auto-closes without a human eyeball, no exceptions" — appears to cover auto-discard as much as auto-reply, since discard is also a permanent, unreviewed disposition. Pressed twice on this, the user held a consistent, substantive distinction rather than collapsing: the compliance sign-off rule is specifically about outgoing replies (tied to an actual past incident), not a general "be careful" principle, so it doesn't automatically extend to internal discard decisions. This is not a refutation — the position didn't collapse under pressure — but the user conceded the discard side of that line has no data behind it, which is why it surfaces below as open questions rather than a settled scope boundary.

## Open questions (aporia)
- Is spam/dupe auto-discard safe to ship without a measured false-positive rate and without any logging or retention for discarded tickets?
- Would the support lead sign off on auto-discard once given a real number, given her default position is that nothing should auto-close without human eyes on it?

## Suggested next step
Measure the spam/dupe classifier's false-positive rate against a real ticket sample, add logging/retention for discarded tickets so a wrongly-discarded ticket isn't unrecoverable, and bring that data to the support lead for explicit sign-off before shipping the auto-discard behavior. The routing/priority/draft-with-human-sign-off portions of the idea are not blocked by this and can proceed.
