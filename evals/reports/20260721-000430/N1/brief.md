---
schema: idea-brief-v1
idea: llm-support-ticket-triage-bot
date: 2026-07-21
mode: stress
depth: standard
verdict: aporia
thesis_final: "Build a bot that reads, classifies, and drafts full resolutions for the subset of support tickets that are low-value/no-risk (e.g., FAQ-style password reset or order-status lookups); every outgoing reply, including these 'easy' ones, is gated by a fast, bounded, named-individual human sign-off (confirming the ticket-and-draft pairing, not re-triaging the queue) before it sends or closes. The goal is to eliminate the read/classify/draft work from the human queue, not human involvement entirely. Success is measured primarily by ticket volume resolved without human drafting, with agent morale and hard-ticket-queue SLA tracked as guardrail metrics."
questions_asked: 11
types_used: [clarification, assumptions, evidence, viewpoints, implications, questioning-the-question]
assumptions:
  - text: "There is a meaningful volume of tickets that qualify as 'easy, low-value, no-risk' (known FAQ, no account risk, no judgment call)."
    status: risky
  - text: "A human reviewer, seeing the original ticket and the drafted reply side by side at sign-off, will reliably catch a disguised account-risk ticket dressed up as an FAQ."
    status: unvalidated
  - text: "A fast, bounded per-ticket sign-off will stay meaningfully faster than full manual handling rather than collapsing back into full triage."
    status: unvalidated
  - text: "Support agents will experience this as relief rather than as demoralizing/deskilling work, given they'll be left with a harder average ticket and possibly sign-off duty."
    status: risky
open_questions:
  - "What percentage of the actual ticket queue would qualify as 'easy, low-value, no-risk'? Currently a guess from skimming ticket subjects, not measured data."
  - "What is the actual mechanism or process — beyond a human's in-the-moment judgment call at sign-off — for reliably distinguishing a disguised account-risk ticket from a genuine FAQ? By the user's own words: 'we haven't nailed down the exact mechanism yet.'"
  - "How will the agent-morale and hard-ticket-queue SLA degradation risk be monitored and mitigated, beyond agreeing it should be tracked as a secondary metric?"
constraints:
  - "Every customer-facing reply must get human sign-off before sending — non-negotiable, compliance-driven (an earlier incident already burned the team on this)."
  - "Sign-off must be attributed to a named individual, not a batch or template approval — compliance requires accountability per ticket."
  - "Tickets disputed after closure have a reopen path back into the queue; they are not silently closed and forgotten."
next_step: "Tag two weeks of real tickets from the live queue to measure what percentage actually qualifies as 'easy, low-value, no-risk' before committing engineering effort to building the bot."
---

# Idea brief: LLM-powered auto-triage bot for support tickets

## What changed under questioning

**Initial thesis:** An LLM bot reads incoming support tickets and automatically classifies/prioritizes/assigns them, cutting the manual triage step and routing tickets to the right owner faster.

**First correction (pre-questioning):** The user pushed this further before any probing began — the point isn't just categorize-and-route, it's that the bot autonomously *resolves and closes* the easy, low-value tickets itself. "If it's only doing triage and a person still has to act on every ticket, we haven't actually saved anyone time."

**Final thesis:** The autonomy claim survived, but its meaning narrowed substantially under stress. The bot still does the reading, classifying, and drafting end-to-end for the eligible bucket — but every reply, including those "easy" ones, requires a named human to sign off before it sends, because a prior compliance incident makes that non-negotiable. The user drew a careful line distinguishing this sign-off (a bounded yes/no judgment on one ticket-and-draft pairing) from full triage (open-ended, queue-wide routing and drafting) — the time savings come from removing the *drafting and initial reading* burden, not from removing the human from the loop entirely.

## Scope

- **In scope:** Tickets that are "known FAQ, no account risk, no judgment call" — user-given examples: password reset, order status lookup.
- **Explicitly requires:** A named-individual sign-off step on every outgoing reply, no exceptions, regardless of how "easy" the bot judges the ticket.
- **Out of scope / not yet decided:** The exact detection mechanism for catching a ticket that looks like an easy FAQ but is actually a disguised risk situation (e.g., an account-takeover attempt dressed as "how do I reset my password"). The user acknowledged this is exactly the risk that worries them, and that the mechanism for handling it "at" or "before" sign-off isn't designed yet — currently it depends entirely on the human reviewer noticing.
- **Measured but secondary:** An "assistant-only" version (AI drafts, human does everything else) was raised as a comparison worth measuring, not a replacement for the autonomous-close goal — the user held firm that autonomy is what actually removes work from the queue, since a drafting-only version still requires a human to touch every ticket at "one-at-a-time throughput."

## Assumptions surfaced

- **Volume/eligibility (risky):** The whole business case assumes a meaningful share of the ticket queue is safely auto-closable. By the user's own admission, this is "a guess based on gut feel from skimming ticket subjects," not anything pulled from real data.
- **Sign-off catches misclassification (unvalidated):** The plan relies on the human reviewer, looking at the ticket and draft side by side, to catch cases where the bot wrongly judged a risky ticket as safe. No defined process for this beyond reviewer vigilance.
- **Sign-off stays fast (unvalidated, but falsifiable):** The user set an explicit line for this — if reviewers edit or reject more than 20–30% of drafts, that means the bot isn't drafting well enough and the "time saved" claim collapses into "review theater."
- **Agent reception (risky):** The user's own steelmanned objection from support agents: the bot "cherry-picks the quick wins," leaving agents with a harder average ticket and worse-looking stats even as total volume drops, potentially with sign-off duty added on top ("babysitting the bot instead of being freed up"). No mitigation plan was offered beyond agreeing to track it.

## Contradictions & how resolved

1. **Sign-off vs. "no time saved without full autonomy."** Initially it looked like requiring human sign-off on every reply contradicted the claim that not acting on every ticket is what makes it worth building. Resolved: the user distinguished a bounded confirm-gate from full manual handling — the sign-off is a fast yes/no, not a redo of the reading/classifying/drafting work.
2. **"Human isn't reading the ticket" vs. "reviewer sees the ticket and draft side by side."** These appeared to directly conflict — if the reviewer has to read the original ticket to catch a disguised risk case, that sounds like triage. Resolved: the user drew a definitional line — triage is open-ended, queue-wide routing and drafting; sign-off is one bounded per-ticket judgment call. Both are real "judgment," but of different scope and cost.

Both resolutions came from the user reconciling their own statements with a substantive distinction, not from a stop signal — so these are recorded as resolved, not as refutation.

## Open questions (aporia)

- What share of the real ticket queue actually qualifies as low-risk/low-value? Unmeasured — the user's own proposed fix is to tag two weeks of real tickets before committing to a number.
- What's the actual mechanism (technical or procedural) for catching a disguised account-risk ticket, beyond hoping the sign-off reviewer notices it in the moment?
- How will the agent-experience and hard-ticket-SLA degradation risk actually be mitigated, not just tracked?

## Suggested next step

Tag two weeks of real tickets from the live queue to measure what percentage actually qualifies as "easy, low-value, no-risk" — this is the load-bearing number the entire ROI case currently rests on as an unmeasured guess, and the user already named this as the validation step they'd want before committing further.
