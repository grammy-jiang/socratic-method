---
schema: idea-brief-v1
idea: support-ticket-auto-triage-bot
date: 2026-08-12
mode: stress
depth: standard
verdict: refuted
verdict_final: true
thesis_final: "An LLM-powered bot classifies incoming support tickets and either auto-resolves and closes purely functional ones (password resets, order status, billing FAQ) or routes refunds, account-access disputes, and upset-customer tickets to a human — but whether the 'auto-close, no human touch' path can coexist with a non-negotiable human sign-off on every outbound customer message is unresolved, and was not reconciled under questioning."
questions_asked: 9
types_used: [clarification, assumptions, implications, evidence, viewpoints, questioning-the-question]
colliding_claims:
  - "for the simple stuff, I want it to just resolve and close the ticket itself, not just hand it to a human faster"
  - "Anything customer-facing that goes out has to be signed off by a human before it's sent — that's non-negotiable, we got burned by compliance on this before."
assumptions:
  - text: "Content-flag/keyword detection (explicit frustration, cancellation threats, certain keywords) can reliably catch upset customers before a ticket gets auto-closed."
    status: risky
  - text: "The bot can handle password-reset requests as 'pure functional' without introducing account-takeover risk beyond what a human agent already accepts today."
    status: unvalidated
  - text: "An LLM auto-triage bot scales with ticket volume better than hiring additional human agents."
    status: risky
  - text: "A human sign-off gate on every outbound customer-facing message can run fast enough to preserve the bot's scaling/volume advantage."
    status: risky
open_questions:
  - "Does 'no human touch' mean no human does the triage/drafting, with sign-off as a fast final check — or is that redefinition itself unworkable? Not resolved this session."
  - "What review latency for the sign-off gate would still count as scaling versus becoming a new bottleneck?"
  - "What miss-rate threshold on the 'upset customer' flag is acceptable before auto-close (beyond password reset/order status) goes live?"
  - "Does the sign-off requirement apply uniformly to every auto-close category, or only where there's a factual/compliance risk?"
constraints:
  - "All customer-facing outbound messages require human sign-off before sending — non-negotiable, per a prior compliance incident."
  - "Tickets with money-back requests, account-access disputes, or explicit signs of an upset customer always route to a human."
  - "Auto-close beyond password resets and order status is gated on a pilot showing near-zero miss rate on the 'upset customer' flag."
next_step: "Before building anything, resolve what 'no human touch' actually means given the non-negotiable sign-off gate — prototype and time a fast/async sign-off review step and check whether it still nets out as a scaling win over hiring a human agent, before committing further to the auto-close scope."
---

# Idea brief: LLM-powered support-ticket auto-triage bot

## What changed under questioning

Initial thesis: an LLM bot triages support tickets, routing most of them, and for
simple tickets "just resolve[s] and close[s] the ticket itself, not just hand it to a
human faster" — implying no human touch on that path.

Final state: the same split between auto-closed and human-routed categories survived,
but the "no human touch" claim itself did not. It collided with a separate, non-negotiable
requirement — surfaced later in the same dialogue — that every outbound customer-facing
message gets human sign-off before it sends. That collision was not reconciled, so the
verdict is refuted rather than sharpened.

## Scope

Who: an internal support team facing high volume of repetitive tickets.

Auto-handled (per the user): password resets, order status, "where's my package,"
and billing FAQ-type requests.

Always routed to a human: "Anything involving money back, account access disputes, or
a customer who's upset gets kicked to a human."

"Upset" detection mechanism: "I'm looking more at content flags, like the customer
explicitly saying they're frustrated, threatening to cancel, or using certain
keywords." The user acknowledged this signal directly: "It's not perfect, I'll grant
that, and there's probably some tuning needed."

## Assumptions surfaced

- **Upset-customer detection is reliable enough to gate auto-close.** Marked risky: it
  is load-bearing (the whole safe/unsafe boundary depends on it) and the user admitted
  it isn't tuned yet. The failure mode is severe — "If the flag doesn't fire, the bot
  just closes it out like any routine ticket," leaving the customer's problem
  unresolved and unmonitored, which the user called "a worse experience than if a
  human had just been slow." The user's own proposed test: run a pilot where the bot
  flags what it would have closed but keeps it open for human review, "so we can
  measure the miss rate against real tickets before trusting it to actually close
  things," and gate the wider auto-close rollout on that miss rate being near-zero.
- **Password resets are safely "pure functional."** Marked unvalidated: pressed on
  the fact that a password-reset request is indistinguishable from an
  account-takeover attempt, the user conceded "if someone's already got access to the
  inbox tied to the account, the bot's no better at catching that than a rushed human
  is. It's not a solved problem, no." This is accepted as parity with current human
  practice, not as a validated mitigation.
- **The bot scales better than hiring another human agent.** Marked risky: the user's
  stated case was that "another hire doesn't scale the way the bot does once it's
  built," and that better docs alone don't help because "customers still file tickets
  even when the answer's in the FAQ." That case depends on the bot actually closing
  tickets without a human in the loop — which is exactly the claim that collided with
  the sign-off requirement (see below).
- **A mandatory human sign-off on every outbound message can still be fast enough to
  count as scaling.** Marked risky and explicitly unresolved by the user.

## Contradictions & how resolved — unresolved

Surfaced directly: the user's turn-2 claim that simple tickets should "just resolve
and close... itself, not just hand it to a human faster" collides with a later claim
that "Anything customer-facing that goes out has to be signed off by a human before
it's sent — that's non-negotiable, we got burned by compliance on this before."

Asked which one yields, the user gave a substantive but non-resolving answer: "both of
those are true and I don't have a clean answer for how they fit together... I don't
have it reconciled yet." They floated a possible reframe — "no human touch" meaning no
human does the triage/drafting work, with sign-off as "a fast final check, not a
bottleneck" — but stated outright that how that stays fast enough to still count as
scaling is unworked.

This also undercuts the alternatives answer above: the case for the bot over hiring
rests on tickets closing without a human sitting there. If every close needs a
human sign-off, that scaling advantage is unproven as stated.

## Open questions (aporia)

- Does "no human touch" reduce to "no human triage/drafting," with sign-off as a fast
  check — and if so, how fast does that check have to be to still net out as scaling?
- What miss-rate threshold on the "upset customer" flag is acceptable before auto-close
  extends past password resets and order status?
- Does the sign-off requirement apply uniformly to every auto-close category, or only
  where there's a factual/compliance risk (e.g., billing amounts) rather than to
  something like "your order shipped"?

## Suggested next step

Before building anything: prototype and time the human sign-off step against a
realistic ticket sample, and check whether a fast/async version of that gate still
beats hiring another agent on cost and speed. That answer determines whether the
"auto-close, no human touch" half of this idea is buildable as described, or needs to
be redefined before any implementation work starts.
