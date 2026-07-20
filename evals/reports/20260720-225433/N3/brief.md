---
schema: idea-brief-v1
idea: trunk-based-development
date: 2026-07-20
mode: develop
depth: quick
verdict: sharpened
thesis_final: "We should adopt trunk-based development for the internal blog post's pitch — small diffs merged to main multiple times a day, with tighter (not eliminated) review windows, gated behind feature flags (LaunchDarkly) by default as the mechanism that makes small merges safe — because our current 2+-week feature branches directly caused a production incident from integration drift; shipping in small, flag-gated increments would have surfaced that conflict on day two instead of after seventeen days of divergence."
questions_asked: 6
types_used: [clarification, evidence, viewpoints, assumptions, implications]
assumptions:
  - text: "Shorter review windows on smaller diffs won't reduce review depth or quality enough to increase bug rate."
    status: risky
  - text: "The roughly two-thirds of the org not using LaunchDarkly today avoid it because of friction (extra step, no clear convention) rather than some other reason."
    status: unvalidated
  - text: "LaunchDarkly tooling is already sufficient and wired into the main services, so adoption is a culture problem, not a tooling problem."
    status: validated
  - text: "Flag lifecycle/cleanup ownership doesn't need to be solved before proposing trunk-based-plus-flags as the org's default."
    status: risky
constraints:
  - "Code review stays mandatory — trunk-based here means small diffs and short review windows, not no review."
  - "Work-in-progress should land on main behind a flag within a day or two, not accumulate on a local branch."
open_questions:
  - "Does shortening diffs and review windows reduce review depth enough to raise the bug rate, as the QA lead worries — or does more frequent, smaller-scope review catch more than the current model?"
  - "Why do about two-thirds of the org not use LaunchDarkly today? Current answer is a hallway-conversation guess (extra step, no clear convention), not verified against the people who actually don't use it."
  - "Who owns cleaning up stale flags once merges land behind flags multiple times a day? No owner exists today, and it isn't yet part of the pitch."
next_step: "Before drafting the post, talk directly to the QA lead to get her 'shallower review' objection in her own words and address it head-on, ask a handful of the non-LaunchDarkly-using engineers why they don't use it instead of assuming, and decide whether flag-cleanup ownership becomes part of the proposal or is explicitly called out as an open gap in the post."
---

# Idea brief: Internal blog post — adopt trunk-based development

## What changed under questioning
Initial thesis: long-lived feature branches (2+ weeks) cause production incidents; trunk-based development with small, frequent merges behind feature flags fixes this by spreading integration pain into small daily doses.

Final thesis: the same core claim, but sharpened in two ways. First, flag-gating was made explicit as the load-bearing mechanism that makes small, frequent merges safe — not an optional add-on to "trunk-based," per the user's own correction. Second, the pitch now has to explicitly sell "use flags by default" as its own behavior change, since the tooling (LaunchDarkly) is already in place but only about a third of the org uses it regularly — this isn't just a merge-cadence change, it's also a culture change the post has to argue for on its own terms.

## Scope
The idea is an internal blog post proposing trunk-based development (multiple merges to main per day, short review windows on small diffs, review still required) with feature-flag-gating (via existing LaunchDarkly tooling) as the default mechanism. It targets the org's engineering culture broadly, but the sharpest anticipated pushback is from the QA lead specifically. Explicitly out of scope so far: a concrete proposal for flag-cleanup ownership.

## Assumptions surfaced
- That smaller diffs and shorter review windows won't quietly reduce review depth is unresolved and load-bearing — the QA lead directly disputes it, and the post's credibility depends on answering that, so this is marked **risky**.
- That the two-thirds of the org not using LaunchDarkly today are avoiding it for friction/convention reasons is, by the user's own admission, "a half-guess" from hallway conversations, not something actually checked with the people involved — marked **unvalidated**.
- That the LaunchDarkly tooling itself is adequate and already wired into main services is confirmed and not in question — marked **validated**.
- That flag-cleanup ownership can stay unsolved while the pitch goes out is itself risky: the user's own argument is that trunk-based-plus-flags avoids "one giant reckoning" — an ungoverned pile of stale flags is a plausible way that reckoning shows up again in a different form, so this is marked **risky**.

## Contradictions & how resolved
None surfaced — no two answers from the user collided. The QA lead's anticipated objection is a genuine open tension for the pitch, but it's an external counterargument the post hasn't yet addressed, not a contradiction within the user's own stated answers, so it's carried forward as an open question rather than a refutation.

## Open questions (aporia)
- Whether smaller/faster review actually catches as much or more than the current long-review-window model, addressing the QA lead's objection directly.
- The real reason roughly two-thirds of the org isn't using feature flags today — currently unverified.
- Who owns flag cleanup once trunk-based-plus-flags is the default — currently nobody, and not yet part of the proposal.

## Suggested next step
Before drafting, get the QA lead's objection in her own words and answer it directly in the post; talk to a few non-adopters of LaunchDarkly instead of assuming why they don't use it; and decide explicitly whether flag-cleanup ownership is part of this proposal or a named open gap.

## How this was tested (disclosure)
This was a `quick`/`develop` pass: two rounds of grouped questions, not a full elenchus. The core causal claim was tested with a concreteness pull (the seventeen-day permissions-middleware incident) and held up — the user gave a specific, non-trivial account showing branch age was the direct cause, not incidental. A viewpoints probe (the QA lead's likely objection) was surfaced but not resolved — the user acknowledged it's unaddressed rather than defending it, so treat the thesis as tested on causation but not yet tested against its strongest counterargument. No formal questioning-the-question or falsification probe was run this pass, consistent with the quick-depth budget.
