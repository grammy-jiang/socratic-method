---
schema: idea-brief-v1
idea: trunk-based-development-blog-post
date: 2026-08-11
mode: develop
depth: quick
verdict: aporia
verdict_final: true
thesis_final: "Move the team to short-lived branches (merged within 1-2 days, not direct-to-main-with-flags), backed by one solid incident (a day-long merge conflict) rather than two — the broken-build incident argues for a stronger CI gate more than for trunk-based itself. Whether a CI gate running QA's regression suite on every merge, plus a smoke/integration layer, actually gives QA coverage equivalent to their current release-branch regression pass is asserted but not yet verified."
questions_asked: 5
types_used: [clarification, evidence, viewpoints, questioning-the-question, assumptions]
assumptions:
  - text: "Feature branches sitting ~2 weeks and blowing up on merge caused real pain"
    status: validated
  - text: "Feature flags plus a stronger CI gate on main can replace QA's release-branch regression pass as the pre-prod gate"
    status: risky
open_questions:
  - "Does a CI gate that runs QA's full regression suite on every merge to main, plus a smoke/integration layer, actually give coverage equivalent to QA's current regression pass against a cut release branch? Author states this is unverified ('homework I still owe')."
constraints:
  - "Post must address QA's anticipated pushback about losing release branches"
  - "Ask is short-lived branches merged within 1-2 days, not direct-to-main commits"
next_step: "Before writing the section that tells QA what replaces their regression gate, map the proposed CI gate (full regression suite on every merge + smoke/integration layer) against what QA's current regression pass actually catches, and confirm with QA (or test data) that nothing is lost."
---

# Idea brief: Trunk-based development blog post

## What changed under questioning
Initial: wants to write a persuasive internal blog post arguing for trunk-based development, citing two incidents as support and anticipating QA pushback over losing release branches.
Final: the ask narrowed to short-lived branches merged within 1-2 days (not direct-to-main-with-flags). Under questioning, the author revised their own evidence: the "broken build shipped to prod" incident turned out to be a CI/testing gap, not a branch-age problem — the same collision would have happened even with day-long branches, so that incident now argues for a stronger CI gate rather than for trunk-based itself. The merge-conflict incident (a day lost untangling it) still squarely supports the branch-age argument. The proposed answer to QA's core objection — feature flags plus a stronger CI gate replacing their regression-pass gate — remains unverified by the author's own admission.

## Scope
Internal blog post; primary skeptical audience is QA, whose current stability anchor is cutting a release branch, running a regression pass against it, and treating that as the pre-prod gate. The ask is short-lived branches (1-2 days), not a full direct-to-main-with-feature-flags model.

## Assumptions surfaced
- Feature branches sitting ~2 weeks and blowing up on merge caused real pain — validated by the merge-conflict incident, which held up under questioning as a genuine branch-age problem.
- Feature flags plus a stronger CI gate on main can replace QA's regression-pass gate — risky: this is the load-bearing claim for the post's target audience (QA), and the author states outright it is not yet verified against what QA's regression pass actually catches.

## Contradictions & how resolved
The initial framing implied both incidents supported trunk-based development. Under questioning, the author resolved this themselves: the broken-build incident is better evidence for a stronger CI gate than for trunk-based specifically ("the collision itself would still have happened with day-long branches ... what actually let it ship was that CI didn't catch it"). This was a self-correction, not an unresolved collision — the post's evidence section should be reframed accordingly rather than lead with that incident as the trunk-based case.

## Open questions (aporia)
- Does a CI gate that runs QA's full regression suite on every merge to main, plus a smoke/integration layer, actually give coverage equivalent to QA's current regression pass against a cut release branch? This is the specific claim QA will push back on, and the author has not yet verified it.

## Suggested next step
Before writing the section that tells QA what replaces their regression gate, map the proposed CI gate (full regression suite on every merge + smoke/integration layer) against what QA's current regression pass actually catches, and confirm with QA (or test data) that nothing is lost. Write the incident-1 section as a CI-gate argument, not a trunk-based argument.
