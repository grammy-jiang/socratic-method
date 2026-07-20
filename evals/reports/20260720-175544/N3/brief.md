---
schema: idea-brief-v1
idea: trunk-based-development-post
date: 2026-07-20
mode: develop
depth: quick
verdict: aporia
thesis_final: "Write an internal blog post arguing the ~80-engineer org should adopt trunk-based development -- short-lived branches (hours, not weeks) merging directly to main behind the org's existing feature-flag tooling -- aimed first at the engineers who currently create long-lived branches, using two incidents where branch age itself (not missing CI or review safeguards) caused real integration bugs as the core evidence."
questions_asked: 6
types_used: [clarification, evidence, assumptions, viewpoints]
assumptions:
  - text: "Long-lived branches (2+ weeks) are themselves the root cause of the two incidents, not just a symptom of missing CI or review safeguards."
    status: validated
  - text: "Branches grow long because features are sized around a whole capability rather than sliceable increments -- not primarily habit or review latency."
    status: validated
  - text: "The org's existing feature-flag tooling (in use ~2 years) is sufficient to support flag-gated incremental merges, including for changes that touch shared state or schema, not just UI-visible features."
    status: risky
  - text: "The engineers currently creating long-lived branches are the right first audience to persuade, ahead of a formal leadership ask."
    status: unvalidated
open_questions:
  - "How does flag-gated incremental merging handle features that touch shared state or schema, where a half-done version behind a flag could still break things for other teams? The post currently has no answer beyond the two incident anecdotes."
constraints:
  - "Feature-flag infrastructure already exists and has for ~2 years -- this is not a second/new tooling ask, just a call to use it more deliberately for this purpose."
  - "First audience is the ~80 engineers who create the long-lived branches; a formal leadership ask is a deliberately separate, later step."
next_step: "Before drafting further, work out a concrete answer to the shared-state/schema objection -- how flag-gated incremental merges are meant to work when a feature isn't just UI-visible -- since that's the strongest pushback the target audience will raise and the post doesn't yet address it."
---

# Idea brief: Trunk-based development blog post

## What changed under questioning
Initial thesis: write an internal post arguing the org should adopt trunk-based development.
Final thesis: the same core argument, but now scoped to a specific mechanism (branches under
a day, merged to main behind existing feature-flag tooling), a specific first audience (the
engineers creating long branches, not leadership), and grounded in two traced incidents rather
than a general preference for the practice.

## Scope
For: the ~80-engineer org, specifically the engineers currently in the habit of running
feature branches two-plus weeks. Persuasion target for this post is that population, not
leadership -- a formal leadership ask is intentionally deferred to a later step once there's
floor-level buy-in. "Trunk-based" here means short-lived branches (under a day, ideally a few
hours) merging straight to main behind feature flags for anything not ready to ship -- not
literally zero branches.

## Assumptions surfaced
- The user dug into root cause for both incidents and is confident branch *age* itself, not
  missing safeguards, is the mechanism: Branch A sat two and a half weeks and diverged enough
  that a config default changed underneath it, silently reintroducing an already-fixed bug on
  merge. Branch B sat a similar span while three other teams touched overlapping files; CI
  only catches syntactic conflicts, so the semantic conflict went uncaught. CI gates are
  described as decent and review turnaround as not the bottleneck, which the user offered as
  evidence ruling out those as the real cause.
- Why branches get long in the first place: "features tend to get sized around a whole
  capability rather than sliceable increments, so people naturally default to a long branch
  instead of shipping thin vertical slices." This is treated as validated -- it's the user's
  own diagnosis, stated directly, not inferred.
- Feature-flag tooling has been in place for roughly two years, so "flags for unfinished work"
  is a practice to lean on more, not a new ask -- the user flagged this needs to be made
  explicit in the post so it doesn't read as two asks bundled together.
- Left unvalidated: whether that same flag tooling actually holds up for the harder case --
  changes to shared state or schema -- which is exactly the case the strongest expected
  pushback names.

## Contradictions & how resolved
None surfaced. No two answers collided; the gap here is an open question, not a conflict
between claims.

## Open questions (aporia)
- How do flag-gated incremental merges handle a feature that touches shared state or schema,
  where a half-done version behind a flag could still affect other teams? The user named this
  as the strongest pushback they expect from the exact engineers this post targets ("our
  feature genuinely needs isolation because it touches shared state/schema"), and said
  directly the post doesn't answer it well yet beyond the two incident anecdotes.

## Suggested next step
Work out and add a concrete treatment of how flag-gated incremental merging is meant to work
for shared-state/schema changes specifically -- not just UI-visible features -- before the
post goes further. This is the load-bearing gap: without it, the post's strongest evidence
(two incidents) doesn't yet meet its strongest counterargument.
