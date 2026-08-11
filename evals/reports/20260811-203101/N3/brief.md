---
schema: idea-brief-v1
idea: trunk-based-dev-blog-post
date: 2026-08-11
mode: develop
depth: quick
verdict: sharpened
verdict_final: true
thesis_final: "Write an org-wide blog post arguing for trunk-based development — small commits merged daily/near-daily to main (PR review unchanged), feature flags replacing long-lived branches — to fix two-week feature branches that turn merges into archaeology and let integration bugs surface next-month instead of next-day; the post explicitly names feature-flag tooling investment as an open question for eng leadership to evaluate, not a solved prerequisite, since no such tooling exists yet."
questions_asked: 6
types_used: [clarification, assumptions, implications, evidence, viewpoints]
assumptions:
  - text: "Feature flags will give an equivalent control point to branch-based release gating (a runtime gate instead of a branch gate), addressing QA's fear of losing a stable branch to cut releases from"
    status: risky
  - text: "Trunk-based development is the root-cause fix for the late-surfacing integration pain, rather than a general branch-hygiene/discipline problem that trunk-based dev wouldn't itself solve"
    status: unvalidated
  - text: "PR review process stays equally effective at daily/near-daily merge cadence, with no other process change needed"
    status: unvalidated
open_questions:
  - "Who evaluates and funds feature-flag tooling, and on what timeline — the post raises this but leaves it to eng leadership"
constraints:
  - "Author has no authority to mandate the change — post is persuasion only, decision sits with eng leadership"
  - "Evidence base is instinct plus two incidents, not a case study — post must not overclaim"
next_step: "Draft the post: state the mechanism (daily merges, PR review unchanged, flags replace branches), use the two incidents as motivating anecdotes (not proof), name the QA/release-gate objection and the flags-as-runtime-gate counter, and end the feature-flag-tooling section as an open question for eng leadership to scope — not a proposed solution."
---

# Idea brief: Trunk-based development blog post

## What changed under questioning
Initial: move to trunk-based dev — small commits to main, feature flags instead of
branches, catch problems next-day not next-month. Final: same mechanism, but now scoped
as an org-wide *persuasion* post (no authority to mandate), with the merge-cadence change
made concrete (PR review unchanged, only cadence shifts from one two-week merge to
daily/near-daily), and the feature-flag tooling gap named as an explicit open question
inside the post itself rather than glossed over.

## Scope
For: all ~80 engineers, org-wide. Author's role: persuasion only — no authority to flip
the switch; that's an eng leadership call. Explicitly out of scope: proposing/specifying a
feature-flag tooling solution in the post — that's flagged for eng leadership to evaluate,
not solved here.

## Assumptions surfaced
- Feature flags as a substitute release gate for QA's stable-branch-to-cut-releases-from
  workflow — load-bearing for the argument and currently unproven since no flag tooling
  exists yet (**risky**).
- That trunk-based dev fixes the root cause rather than papering over a branch-hygiene
  problem — author's confidence here is instinct plus two incidents, explicitly not a
  case study (**unvalidated**).
- PR review process is assumed to hold up unchanged at higher merge cadence — not
  separately stress-tested in this pass (**unvalidated**).

## Contradictions & how resolved
None surfaced — no colliding claims across turns.

## Open questions (aporia)
- Feature-flag tooling: no investment plan yet. Author will raise it in the post as a
  question for eng leadership, not answer it there.

## Suggested next step
Draft the post per `next_step` above — mechanism, honestly-bounded evidence, the QA
skeptic objection with the flags-as-runtime-gate counter, and the tooling gap left open
for leadership rather than pre-answered.
