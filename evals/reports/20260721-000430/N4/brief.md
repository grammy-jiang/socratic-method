---
schema: idea-brief-v1
idea: pro-tier-feature-gate
date: 2026-07-21
mode: stress
depth: standard
verdict: sharpened
thesis_final: "Finish building bulk export and saved custom views (already 60-70% done on the backend) and ship them gated behind a new paid Pro tier, using a 60-day empirical signal (>=5% upgrade-click rate and >=1% paid conversion of 1,200 MAU) as the go/no-go test rather than pre-launch willingness-to-pay validation."
questions_asked: 9
types_used: [clarification, assumptions, evidence, viewpoints, implications, questioning-the-question]
assumptions:
  - text: "Users who requested bulk export / saved views in feedback and support threads are the same users who would pay for them"
    status: unvalidated
  - text: "1,200 MAU is a large enough base that a 60-day conversion signal (5% click / 1% pay) is meaningful rather than noise from a handful of accounts"
    status: risky
  - text: "Not gating any currently-free functionality (only the two new half-built features) will read as fair to the free users who originally requested those features"
    status: risky
  - text: "Finishing the already-half-built features is the fastest path to a real revenue signal, not merely the path of least resistance because the engineering is sunk"
    status: risky
open_questions: []
constraints:
  - "No feature clawback: existing free-tier access is unchanged; only the two new, not-yet-shipped features are gated"
  - "No accommodation (grandfathering, early access, discount) for users who originally requested the gated features — deliberately out of scope for this decision"
  - "Kill switch: if upgrade-click rate stays under 5% of MAU in month 1, or paid conversion stays under 1% (12 users) by day 60, the Pro tier is pulled and the features ship free or are shelved"
next_step: "Finish and ship bulk export and saved custom views gated behind the Pro tier; instrument upgrade-click rate and 60-day paid conversion, and act on the stated kill thresholds (>=5% click / >=1% convert) rather than gut feeling."
---

# Idea brief: Pro-tier gate on two half-built features

## What changed under questioning

Initial framing (from the invocation): add a paid "Pro" tier to a free side-project SaaS —
read as a build-Pro-features-from-scratch decision.

First correction: the two candidate Pro features (bulk export, saved custom views) are
already 60-70% built on the backend. The real decision is whether to finish and gate
work that's mostly done, not whether to build Pro features at all.

Under stress questioning, the thesis held but picked up real texture: the user
initially framed the feature choice as "a real signal" from support threads, distinct
from "closest to done." Pressed on a sunk-cost counterfactual — would this still be the
first move on a greenfield version of the decision — the user candidly admitted sunk
cost is "doing real work" in lowering the bar for what gets gated, while maintaining the
feature requests are independent evidence too. The final thesis keeps "finish + gate"
but is now paired with an explicit, numeric falsification plan (5%/1% thresholds) that
did not exist at the start of the conversation — before this session the fallback was
just "watch the numbers," with no defined failure line.

## Scope

- **In scope:** finishing and shipping bulk export and saved custom views, gated behind
  a new paid Pro tier, for the existing free base (1,200 MAU).
- **Explicitly out of scope for now:** any accommodation (grandfathering, early access,
  discount) for the specific users who requested these features in support threads;
  pre-launch willingness-to-pay validation (survey, landing-page test); alternative
  monetization paths (donation link, general free-tier polish) — considered and set
  aside in favor of finishing the sunk work.
- **Unchanged:** nothing currently free is being reclaimed; the paywall applies only to
  the two features that don't exist for free users yet.

## Assumptions surfaced

- The feature choice rests on support-thread requests as a demand signal, but the user
  has not directly confirmed that the people who asked would actually pay — "no one's
  said 'I'd pay $8/mo for this' explicitly." Unvalidated by design; the 60-day
  conversion number is meant to substitute for pre-launch validation.
- The 1,200-MAU base clears the user's own noise floor (12 conversions at 1% is "not
  2-3 people"), but the user also granted that a small enough base means "a handful of
  edge-case churns could swing the percentage more than I'd like." Load-bearing for the
  entire go/no-go mechanism, and self-acknowledged as fragile — marked risky.
  - "That's a real signal, not just 'closest to done'... though I'll admit I haven't rigorously checked if the people asking are the same people who'd actually pay."
- Fairness framing ("I'm not clawing back anything anyone currently has") is true on its
  face but the user immediately conceded it "won't land for everyone" — someone who
  asked for a feature and watches it ship paid-only may feel it was dangled in front of
  them. No mitigation plan exists beyond watching support threads after launch.
- Sunk cost is explicitly acknowledged as part of the reasoning: on a greenfield version
  of this same decision, the user said they'd "more likely just poll a few power users
  directly or run a quick landing-page test" instead of committing straight to finishing
  and gating two specific features.

## Contradictions & how resolved

No irreconcilable contradiction surfaced. The closest tension — "real demand signal"
(early) versus "sunk cost is doing real work" (later) — was raised directly as a
sunk-cost counterfactual and the user resolved it themselves: both are true at once
(genuine signal plus a lowered bar from existing work), not a collision requiring one
claim to yield. Held under stress, disclosed rather than smoothed over.

## Open questions (aporia)

None block the decision as currently scoped. The residual uncertainty — whether
requesters and payers overlap, and whether 1,200 MAU is enough to trust the 60-day
number — is being tested empirically post-launch via the stated kill thresholds rather
than resolved before building.

## Suggested next step

Finish and ship bulk export and saved custom views gated behind the Pro tier. Instrument
upgrade-click rate and 60-day paid conversion from day one, and commit to acting on the
stated thresholds (>=5% click-through in month 1, >=1% / 12-user paid conversion by day
60) — pull the paywall and ship the features free (or shelve them) if either line isn't
cleared, rather than letting sunk cost argue for staying the course past the point the
data said no.
