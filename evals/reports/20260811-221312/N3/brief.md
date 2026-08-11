---
schema: idea-brief-v1
idea: trunk-based-development-adoption
date: 2026-08-11
mode: develop
depth: quick
verdict: sharpened
verdict_final: true
thesis_final: "Most of our ~80-engineer org (excluding the firmware team, whose hardware certification cycle makes this a poor fit for now) should adopt trunk-based development — short-lived branches merged within a day, behind feature flags where needed, still CI-gated — starting with the platform team and one product team as first movers. Expansion past them is contingent on a ~6-week pilot showing concrete proof points (lower merge-conflict frequency, faster time-to-merge, zero incidents attributable to branch age) AND on actually standing up faster/parallelized CI plus flag-cleanup discipline, which today is a real gap (a 25-minute full test run), not an assumption to wave away."
questions_asked: 6
types_used: [clarification, evidence, viewpoints, assumptions]
assumptions:
  - text: "Short daily merges of small diffs would have caught incident 1's root cause (a subtle interaction between two of the branch's own commits missed in review because the diff was large)"
    status: validated
  - text: "Long branch lifetime was also the root cause of incident 2, via the deadline pressure that led to a rushed, all-at-once merge"
    status: unvalidated
  - text: "Faster/parallelized CI and flag-cleanup discipline can be stood up before the pilot needs to expand past the first two teams"
    status: risky
  - text: "The platform team and one product team's six-week pilot results will generalize as convincing proof points for the rest of the org"
    status: unvalidated
open_questions:
  - "What is the timeline and owner for standing up faster/parallelized CI and flag-cleanup discipline — the prerequisite for expanding trunk-based development past the two first-mover teams?"
constraints:
  - "org-wide scope: ~80 engineers, but firmware team explicitly excluded (hardware certification cycle) — a structural exemption, not a team that simply hasn't converted yet"
  - "definition: short-lived branches merged within a day, behind feature flags where needed, still gated by CI on merge — not literal direct-to-main commits"
  - "phased rollout: platform team + one product team as first movers, for a ~6-week pilot, before any expansion"
  - "current CI full test run is ~25 minutes — too slow for the model as-is; faster/parallelized CI is a real prerequisite, not yet solid"
next_step: "Before drafting or publishing the blog post, get a scoped commitment (owner + timeline) from whoever owns CI infrastructure for the faster/parallelized test run and flag-cleanup discipline; only then set the six-week pilot start date with the platform and product team leads."
---

# Idea brief: Trunk-based development adoption

## What changed under questioning
Initial framing was "write an internal blog post arguing we should adopt trunk-based
development." First correction: the idea under test is the org-wide adoption itself,
not the post — the post is only the buy-in mechanism. The definition was then
sharpened to short-lived branches merged within a day, behind feature flags where
needed, still CI-gated — not literal direct-to-main commits. The scope narrowed twice
more: from every team switching at once ("not all 80 at once") to a phased rollout
(platform team + one product team as first movers), and from a "most of the org"
pitch to explicitly not "eventually everyone," with the firmware team named as a
structural, not temporary, exemption because of its hardware certification cycle. Most
significantly, the honest CI-speed gap (a 25-minute full test run) surfaced as a real
prerequisite rather than something assumed already solved.

## Scope
~80-engineer org minus the firmware team (excluded because its certification cycle is
tied to specific hardware revisions and doesn't fit this model until that process
changes independently — an explicit, durable exemption, not a team that simply hasn't
converted yet). Rollout is phased: the platform team and one product team already
doing short-lived branches informally are the first movers for a ~6-week pilot; wider
expansion follows only after that pilot, not alongside it.

## Assumptions surfaced
- Short daily merges of small diffs would have caught incident 1's root cause — a
  subtle interaction between two of the branch's own commits missed in review because
  the diff was large. **Validated** by the user's own account: this is a direct,
  specific causal story, not a general assertion.
- Long branch lifetime was also the root cause of incident 2, but more indirectly: the
  deadline pressure that caused the rushed, all-at-once merge existed because the
  branch had been open so long. **Unvalidated** — the user called this "fuzzier"
  themselves; it's a plausible causal chain, not a directly confirmed one.
- Faster/parallelized CI and flag-cleanup discipline can be stood up before the pilot
  needs to expand past the first two teams. **Risky** — load-bearing (the whole model
  depends on CI gates staying meaningful at speed) and currently doubtful (today's full
  run is ~25 minutes, and the user named this as "the honest gap," not solved). This is
  why it's carried as an explicit condition in the thesis itself, not just listed here.
- The two first-mover teams' six-week pilot results will generalize as convincing
  proof points for the rest of the org. **Unvalidated** — not yet tested, but the user
  has already defined what would count (merge-conflict frequency, time-to-merge, zero
  branch-age-attributable incidents over six weeks) rather than leaving it to a "felt
  sense," which is itself a good sign for how testable the claim is.

## Contradictions & how resolved
None surfaced. The answers built on each other consistently — the firmware exemption,
the concrete proof-point metrics, and the CI-speed admission all sharpened the thesis
rather than colliding with an earlier answer.

## Open questions (aporia)
- Who owns standing up faster/parallelized CI and flag-cleanup discipline, and on what
  timeline? This is the one piece that was named as a real gap but never assigned an
  owner or a date in this pass.

## Suggested next step
Before drafting or publishing the blog post, get a scoped commitment (owner + timeline)
from whoever owns CI infrastructure for the faster test run and flag-cleanup
discipline; only then set the six-week pilot start date with the platform and product
team leads.

## Disclosure
This was a `develop`-mode, `quick`-depth pass (two rounds, six questions): clarification,
concreteness/evidence, a perspective probe (the firmware exemption), and an assumptions
probe (CI-gate readiness) were used. Not run this pass: a stress-style counterexample or
disconfirming push, or independent pressure-testing of the incident-2 causal chain beyond
the user's own account — both would be reasonable next steps if this thesis is about to
carry real budget or a leadership ask, rather than just inform a first draft of the post.
