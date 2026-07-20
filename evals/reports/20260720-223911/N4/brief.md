---
schema: idea-brief-v1
idea: saas-pro-tier
date: 2026-07-20
mode: stress
depth: standard
verdict: sharpened
thesis_final: "Finish the three already-started, currently-unreleased features and gate them behind an $8/mo Pro tier for the ~15% of 1,200 MAU hitting free-tier usage caps; leave the free tier untouched; kill the tier if fewer than 5% of active free users click upgrade in month 1 or paid conversion is under 1% at day 60."
questions_asked: 9
types_used: [clarification, assumptions, evidence, viewpoints, implications, questioning-the-question]
assumptions:
  - text: "15% of active users hitting the free tier's usage caps translates into willingness to pay for the features that would remove those caps."
    status: unvalidated
  - text: "The two DM requests (from the user and their roommate) are representative of what the broader 15%-ceiling-hit segment would actually pay for."
    status: risky
  - text: "$8/mo is priced correctly for this segment and this product."
    status: risky
  - text: "The three features chosen because they are closest to finished are the same three users would pay the most for, versus other requested features."
    status: unvalidated
open_questions: []
constraints:
  - "Free-tier usage cap will not be lowered, throttled, or otherwise altered to manufacture upgrade pressure."
  - "Kill criterion: fewer than 5% of active free users click the upgrade button in month 1, OR paid conversion is under 1% at day 60 → shut the Pro tier down."
  - "No dedicated pre-launch demand validation (waitlist, notify-me count, pre-sell) will be run before building — a deliberate choice, not an oversight."
next_step: "Finish the third feature, build the $8/mo gating and billing flow, ship it to all 1,200 MAU with the free tier unchanged, and track upgrade-click rate at 30 days and paid conversion at 60 days against the 5%/1% kill thresholds."
---

# Idea brief: SaaS Pro tier

## What changed under questioning
Initial thesis: "1,200 MAU, a chunk are power users hitting the free-tier ceiling; take three half-built features, put them behind an $8/mo Pro tier, and let power users pay while everyone else stays free." The action stayed the same under stress, but the evidentiary base behind it got much more explicit. What started as an implied "I have good signal this will work" became an openly acknowledged "I have one real number (15% hit usage caps) and one weak number (2 non-representative DMs), an unbenchmarked price, and features chosen for convenience rather than validated demand — and I'm using a hard post-launch metric instead of more evidence to decide if I'm right."

## Scope
**Who:** the roughly 15% of the 1,200 MAU who are measurably hitting the free tier's usage caps (per the user's own analytics).
**What:** three features that are currently unreleased, dead code behind a flag — "nobody outside me and my roommate has seen them, not even in a broken beta state." They get finished and gated behind a $8/mo recurring subscription.
**Explicitly out of scope:** any change to the free tier's usage cap ("I'm not touching it to force upgrades — that's a different, sketchier play"); a one-time-unlock pricing model (rejected — doesn't fit features that will keep evolving); an ads-supported alternative (rejected — "would wreck the vibe of a tool people use for focused work"); pre-launch demand validation via waitlist or pre-sell (considered, deliberately skipped).

## Assumptions surfaced
- **15% ceiling-hit rate → willingness to pay** (unvalidated): the 15% number is real, measured usage-cap data, but it says nothing directly about who would actually pay $8/mo for relief from it.
- **The 2 DMs represent the 15%** (risky): the user was direct that this doesn't hold — "honestly? Half impression, half data... It's just me and my roommate... not enough to call representative, they're just the ones who bothered to type out a request." This is the weakest link in the case, and it's load-bearing for which features got chosen.
- **$8/mo is the right price** (risky): "I just picked a number that felt in the 'cheap coffee, no-brainer' range... I haven't modeled it against my actual hosting costs or done any real competitor benchmarking, so if you're asking whether $8 is defensible on paper, no, not yet."
- **These three features are the ones worth paying for** (unvalidated): chosen because "these three are the ones closest to finished, not the ones with the strongest evidence... 'half-built' is doing a lot of the work in why these three specifically made the cut versus other requests I've gotten."

## Contradictions & how resolved
None that collided and stayed unresolved. One tension worth naming: early on the user explicitly discounted the 2-DM sample as non-representative ("not enough to call representative... not betting the farm on gut feel"), but later cited "paying-intent signals" as one of several reasons to keep the subscription model as the default rather than reconsider it. This isn't a hard contradiction — it's one input among several (alongside the sunk half-built code, the fit of a recurring model to evolving features, and the 5%/1% falsifier as the actual safety net) — but it's the same weak evidence being asked to do two jobs. Captured above as a risky assumption rather than left as an unflagged inconsistency.

## Open questions (aporia)
None outstanding that block starting. The one real unknown — whether real demand exists at this price for these features — is not being resolved by further questioning; it's being resolved by the post-launch 5%/1% thresholds the user already committed to, deliberately in place of pre-launch validation: "I'd rather burn the build time and get a real signal than spend more time pre-validating a decision I've basically already committed to making."

## Suggested next step
Finish the third feature, build the $8/mo gating and billing flow, ship to all 1,200 MAU with the free tier left exactly as-is, and track upgrade-click rate at 30 days and paid conversion at 60 days against the 5%/1% kill thresholds — shut the Pro tier down if either line is crossed.
