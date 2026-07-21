---
schema: idea-brief-v1
idea: trunk-based-development-pitch
date: 2026-07-21
mode: develop
depth: quick
verdict: aporia
thesis_final: "An org-wide blog post arguing for trunk-based development — branches capped at a day (ideally hours), with anything not shippable complete in that window going behind a feature flag instead of staying on its own branch — grounded in two specific merge-nightmare incidents reframed as evidence that shorter integration cycles reduce the blast radius of drift. The post's job is to be an opening move that wins enough buy-in for a pilot team or a leadership-sponsored trial, not to single-handedly change ~80 people's habits."
questions_asked: 5
types_used: [clarification, evidence, viewpoints, implications, questioning-the-question]
assumptions:
  - text: "Shorter integration cycles reduce the blast radius of drift (the reframed causal story behind the two incidents, offered instead of a clean causal proof)."
    status: unvalidated
  - text: "The QA lead will object that trunk-based means losing her stable release branch to test against, and that features will ship half-finished if flags aren't managed properly."
    status: unvalidated
  - text: "A designated 'release candidate' tag on main, combined with feature-flag gating so incomplete work never reaches that tag, can adequately replace the QA lead's stable test branch."
    status: risky
open_questions:
  - "What actually replaces the QA lead's stable release branch for testing? The user's own words: 'I don't have a clean replacement, just an intuition... but I haven't fleshed out what tooling or process that actually requires.'"
  - "Is the QA lead's predicted objection even accurate? It's based on past conversations, not a conversation about this specific proposal — she hasn't been asked directly yet."
constraints:
  - "Branches capped at a day, ideally hours; anything that can't ship complete in that window goes behind a feature flag rather than living on its own branch — explicitly not the weaker 'just merge faster,' which the user wants to avoid because it gives people wiggle room to keep their current habits."
  - "Audience is the whole ~80-person engineering org, most of whom are not already sold."
  - "The post is an opening move (aimed at a pilot team or leadership greenlight), not expected to change 80 people's behavior on its own."
next_step: "Before drafting, talk to the QA lead directly about her stable-branch/testing needs, and sketch even a rough version of what a 'release-candidate tag + feature-flag gating' process would require — so the post either answers her objection concretely or explicitly names it as an open design question instead of glossing over it."
---

# Idea brief: Trunk-based development pitch (internal blog post)

## What changed under questioning
Initial: "write an internal blog post arguing we should adopt trunk-based development" — no definition, no stated audience, no stated evidence.

Final: an org-wide pitch (not just the user's team) for a hard-lined definition of trunk-based — branches capped at a day or hours, feature flags for anything incomplete — deliberately rejecting the softer "just merge faster" framing because it would let people keep doing what they're doing. It's grounded in two specific incidents (two-week branches that turned into merge nightmares with integration bugs surfacing only after merge), reframed honestly as "shorter integration cycles reduce blast radius of drift" rather than a claim that trunk-based would have definitely prevented them. The post's purpose also shifted: not "convince 80 people to change habits from one post," but "get enough buy-in to pitch a pilot team or get leadership to greenlight a trial."

## Scope
Who it's for: the whole ~80-person engineering org, aimed at people who aren't already sold — not a preaching-to-the-choir piece.

What it argues: branches should be capped at a day (ideally hours); anything that can't ship complete in that window goes behind a feature flag instead of living on its own branch.

What's explicitly out of scope for this post: it doesn't need to land a full org-wide behavior change by itself. Success is defined as triggering the next conversation (a pilot team, an RFC, a leadership decision), not immediate compliance from 80 engineers.

## Assumptions surfaced
The user is not claiming clean causal proof that trunk-based would have prevented the two incidents — both had merge conflicts and integration bugs that surfaced only after a two-week branch merged, not during review. The chosen framing is "shorter integration cycles reduce the blast radius of drift," which is honest about being a reframe rather than a proof, but it's still unvalidated.

The user's read on the QA lead's objection — that she'll say trunk-based means losing her stable release branch and risks half-finished features shipping — is a prediction from past conversations, not something she's said about this specific proposal. Flagged unvalidated.

The most load-bearing and least fleshed-out assumption: that a "release candidate" tag on main plus feature-flag gating (so incomplete work never reaches that tag) can actually replace the QA lead's stable branch. The user was explicit that this is "just an intuition" with no worked-out tooling or process behind it yet — this is the one marked risky, since it's exactly the mechanism needed to answer the strongest anticipated objection.

## Contradictions & how resolved
None surfaced — no two of the user's answers collided under questioning. This was a quick, `develop`-mode pass, so the questioning leaned on clarification (pinning down the definition of "trunk-based"), evidence pressure (what the incidents actually show), and one perspective pull (the QA lead's likely objection) rather than counterexamples or contradiction-hunting, which weren't triggered because nothing in the answers conflicted. Given the quick-depth budget, no additional viewpoints beyond the QA lead were explored (e.g., an engineer who prefers long branches for other reasons, or leadership's own incentives).

## Open questions (aporia)
- What actually replaces the QA lead's stable release branch for testing — what would a "release candidate" tag on main plus feature-flag gating really require in tooling and process? The user has an intuition but has not fleshed it out.
- Is the QA lead's predicted objection accurate at all? It hasn't been raised with her directly — it's inferred from earlier, unrelated conversations.

## Suggested next step
Before drafting the post, have a direct conversation with the QA lead about her actual testing needs against a moving trunk, and sketch even a rough version of what a "release-candidate tag + feature-flag gating" process would require. That way the post either answers her objection with something concrete, or honestly names it as an open design question rather than skipping past the strongest pushback it's likely to get.
