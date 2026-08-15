---
schema: idea-brief-v1
idea: llm-support-triage-bot
date: 2026-08-12
mode: stress
depth: standard
verdict: sharpened
verdict_final: true
thesis_final: "An LLM triage bot reads every inbound ticket, routes it to the owning team, and — for password-reset and order-status tickets specifically — auto-closes and auto-sends the reply with zero human touch, gated only by the same classifier's own risk read (any ticket it flags as carrying account or dispute risk always gets human sign-off before sending, no exceptions); new auto-close categories are added only by a human reviewing accuracy stats, never by the bot self-promoting; and the premise that these tickets need LLM-level judgment rather than simpler rules is accepted on unmeasured gut feel for now, to be tested by production classifier-accuracy stats rather than validated against ticket data first."
questions_asked: 11
types_used: [clarification, assumptions, evidence, viewpoints, implications, questioning-the-question]
assumptions:
  - text: "The classifier can reliably tell a genuine informational ticket (password reset, order status) apart from a disguised risk-carrying one (account takeover, dispute) using combined order and account signals, not just ticket text — and this same risk read is the only gate before an informational reply auto-sends, with no independent check behind it."
    status: risky
  - text: "Roughly half of triage tickets carry a 'wrinkle' that a rules-based or self-service system would miss, justifying an LLM's added risk and complexity over a simpler deterministic system."
    status: unvalidated
  - text: "The failed push to a plain FAQ/self-service portal about a year and a half ago is strong evidence that a non-LLM approach can't handle these tickets now."
    status: unvalidated
  - text: "Waiting to hear about problems through customer complaints or an actual compliance incident is an adequate detection mechanism for classifier risk-read errors on the informational categories."
    status: risky
  - text: "New auto-close categories will keep being added only through manual human review of accuracy stats, never by the bot self-promoting itself."
    status: validated
open_questions:
  - "What is the actual measured frequency of tickets with a 'wrinkle' that a simple rules-based system would misroute — the working number used was 'half,' by gut feel, not ticket data."
  - "What concrete detection or monitoring mechanism will surface a classifier risk-read miss on an informational ticket, beyond waiting for a customer complaint or a compliance incident?"
  - "Will category promotion and risk-gating stay human-only indefinitely, or is bot self-promotion of new auto-close categories being considered later?"
constraints:
  - "Any reply the classifier scores as risk-carrying (account or dispute risk) must get human sign-off before it sends — no exceptions, driven by a prior compliance incident."
  - "New categories are added to the auto-close set only by a human manually reviewing accuracy stats — never by the bot promoting itself."
next_step: "Before launch, build the accuracy/risk-read monitoring the go/no-go decision already depends on, since production stats — not pre-validated ticket data — are the agreed mechanism for testing whether the classifier's risk read and the 'these tickets need LLM judgment' bet actually hold."
---

# Idea brief: LLM-powered support-ticket auto-triage bot

## What changed under questioning

Initial thesis: the bot reads every ticket, routes it, and for "the truly simple stuff" (password resets, order status) "just closes them out itself so our humans aren't wasting time" — framed as fully hands-off for the low-hanging-fruit categories, with the set of auto-close categories expanding as trust builds.

Final thesis: "closing" a ticket and sending a customer-facing reply are distinct actions — routing and closing are always zero-touch, but any reply the classifier scores as risk-carrying (account or dispute risk) requires mandatory human sign-off, no exceptions. The two starter categories auto-send informational replies with zero human touch specifically because the same classifier that categorizes the ticket also decides the reply isn't risk-carrying — there is no separate gate behind it. New categories only join the auto-close set through manual human review of accuracy stats, never bot self-promotion. The premise that an LLM is actually needed (versus simpler rules or self-service) rests on an unmeasured belief that "half" of tickets carry a wrinkle, which the team plans to test through production classifier-accuracy stats rather than by checking ticket data first.

## Scope

Who: the internal support team and the tickets in their queue. What: the initial auto-close scope is password-reset and order-status tickets specifically; other categories join only via manual promotion after a human reviews accuracy stats — never bot self-promotion ("at least not yet," per the user). Any reply flagged risk-carrying (account or dispute) always routes to a human for sign-off before sending, regardless of category. Not covered in this pass: specific ticket channels or systems, candidate categories beyond the first two, multi-language handling, or a timeline/resourcing constraint — none of these came up in the dialogue.

## Assumptions surfaced

The riskiest assumption is architectural: the same classifier that categorizes a ticket also makes the risk call gating whether a reply can auto-send, with no independent second check for the "safe" categories. The user acknowledged directly that if the classifier misreads a disguised dispute or account-takeover case as a plain order-status question, the result is exactly "a reply carrying account or dispute risk going out unreviewed" — the outcome the sign-off policy exists to prevent — and characterized this as "a classifier accuracy problem, not a policy problem."

The core justification for using an LLM at all, rather than a simpler rules-based or self-service system, rests on the claim that "half these tickets have some wrinkle." The user confirmed this is "honestly a gut feel from working the queue," not something pulled from ticket data.

The one concrete evidence point offered for needing an LLM — a self-service push about a year and a half ago whose edge cases "bounced right back into the queue" — was tested against a plain static FAQ/portal, "no keyword rules, no classifier behind it at all," a materially weaker bar than the deterministic rules-bot alternative actually being weighed against the LLM approach.

Detection of classifier risk-read errors on the informational categories is reactive, not proactive: "If tracking-number replies started causing problems we'd hear about it fast," with no defined monitoring beyond that, and an explicit unwillingness to add a trigger before an actual incident happens.

Governance of which categories get auto-close stays manual for now — "We're not letting the bot promote itself, at least not yet" — a human eyeballs accuracy stats and flips a category by hand.

## Contradictions & how resolved

An apparent conflict surfaced between "our humans aren't wasting time on password resets and 'where's my order' all day" and "every customer-facing reply that actually goes out has to be signed off by a human, full stop, no exceptions." Resolved: "closing" a ticket and "a reply going out" are distinct actions in the user's model — routing and closing are always zero-touch; only replies the classifier scores as risk-carrying need sign-off. Plain informational replies (e.g., a tracking number) auto-send with no human in the loop.

A second apparent conflict surfaced between that "no exceptions" sign-off rule and the fact that informational replies auto-send with no human involved. Resolved: the user clarified "no exceptions" was always scoped to the risk-carrying category, not to every reply — "A plain order-status ping was never what that policy was written for."

A deeper collision was surfaced but only partially resolved: the user's claim that a classifier miss on an informational ticket has trivial consequences ("worst case a customer gets a wrong ETA") sits against their own earlier point that the classifier's job is specifically to catch disguised risk-carrying tickets. When pressed, the user conceded a classifier miss on the risk read does produce the same unreviewed-risky-reply outcome the sign-off gate exists to prevent, but reframed it as an accuracy bug to fix rather than a design flaw. This is a live, accepted risk, not a resolved one — it is carried into the assumptions list and into the explicit gate in `thesis_final`.

## Open questions (aporia)

- What is the actual measured frequency of tickets with a "wrinkle" that a simple rules-based system would misroute — the working number used was "half," by gut feel, not ticket data.
- What concrete detection or monitoring mechanism will surface a classifier risk-read miss on an informational ticket, beyond waiting for a customer complaint or a compliance incident?
- Will category promotion and risk-gating stay human-only indefinitely, or is bot self-promotion of new auto-close categories being considered later?

## Suggested next step

Before launch, build the accuracy/risk-read monitoring the go/no-go decision already depends on, since production stats — not pre-validated ticket data — are the agreed mechanism for testing whether the classifier's risk read and the "these tickets need LLM judgment" bet actually hold.
