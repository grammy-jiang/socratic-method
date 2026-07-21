---
schema: idea-brief-v1
idea: pro-tier-saas
date: 2026-07-20
mode: stress
depth: standard
verdict: sharpened
thesis_final: "Ship a documented, rate-limited Pro API as a narrow, bounded experiment — not the original three-feature bundle — with a two-month grace period and advance notice before restricting the undocumented endpoints power users currently scrape for the same data. Add scheduled exports and higher project caps only if the API alone clears a conversion bar that still needs to be set for this narrower scope."
questions_asked: 11
types_used: [clarification, assumptions, evidence, viewpoints, implications, questioning-the-question]
assumptions:
  - text: "Support-ticket signals (duct-taping workarounds like manual weekly exports and multi-account juggling, plus unprompted 'I'd pay for that' comments) indicate real willingness to pay, not just feature demand."
    status: risky
  - text: "The three candidate features (scheduled exports, higher project caps, documented API) needed to launch together as one bundle because they serve the same power-user cohort."
    status: unvalidated
  - text: "Free users won't feel anything was taken away as long as no currently documented/supported feature is restricted — even though the undocumented endpoints being locked down are used by the same power-user cohort being courted for Pro."
    status: risky
  - text: "Scrapers using undocumented endpoints without accounts can be adequately reached during the grace period via endpoint deprecation notices, in-app banners, and a changelog post."
    status: unvalidated
constraints:
  - "No currently free, documented/supported feature gets clawed back or restricted."
  - "Undocumented/unsupported endpoints get a minimum two-month grace period, with notices starting immediately at launch, before being restricted."
  - "The experiment is time-boxed and has a kill switch — it does not run indefinitely regardless of outcome."
open_questions:
  - "What click-through and conversion thresholds define success/failure for the API-only test — the original bundle bar (5% upgrade-button click-through in month one, <1% paid conversion by day 60) does not automatically transfer to a narrower, single-feature offering aimed at a smaller slice of the cohort."
  - "How will scrapers without accounts actually be reached during the grace period? Endpoint deprecation messages, in-app banners, and changelog posts are the stated fallback, but reach to anonymous, non-account users is untested."
  - "The two-month grace-period cutoff and the day-60 kill-switch decision land at roughly the same time. If the API experiment fails right as undocumented access is cut off, free/scraping users lose access with no successful product behind it — this timing interaction hasn't been examined."
next_step: "Set a conversion/click-through threshold specific to the API-only test (not a copy-paste of the bundle's 5%/1%), then ship the documented, rate-limited API alone as the first Pro feature, with grace-period notices starting immediately at launch."
---

# Idea brief: Pro tier for free side-project SaaS

## What changed under questioning

**Initial thesis:** Add a paid "Pro" tier to the free SaaS, bundling scheduled exports, higher project caps, and a documented API, aimed at devs/small teams who've hit free-tier limits — because support tickets and repeated "is there a way to do X" requests suggest a subset of users would pay for more.

**Final thesis:** Ship the documented, rate-limited API alone first, as the narrowest possible test of the riskiest piece — the one that requires restricting currently-scraped undocumented endpoints. Give existing users of those endpoints a two-month grace period with advance notice. Only add scheduled exports and higher project caps afterward, and only if the API-only offering clears a conversion bar still to be defined.

Two things drove the change:
1. A contradiction surfaced and was resolved: the user initially said "nothing currently free gets clawed back," but the sanctioned Pro API's whole incentive depends on locking down the undocumented endpoints the same power users currently scrape for free. The user acknowledged this **is** a clawback, revised the claim to "nothing documented and supported gets clawed back," and added a mitigation (grace period + advance notice) that hadn't existed before.
2. A "questioning the question" probe reframed "should I charge for this?" as "should I restrict this access at all?" — which led the user to conclude the three-feature bundle was never actually tested as a bundle; only the API needs the access-restriction tradeoff, so it should be tested alone first.

## Scope

- **For:** devs and small teams already on the free tier who are visibly working around its limits (manual weekly exports, multiple accounts to dodge project caps, scraping undocumented endpoints or asking about an API).
- **What's in the first paid release:** a documented, rate-limited API key. Scheduled exports and higher project caps are deferred, not cut — they ship later only if the API clears its (still-undetermined) bar.
- **Explicitly out for now:** any change to currently free, documented/supported features. Undocumented endpoints are the one exception — they get restricted, but only after a two-month notice-and-grace-period window.

## Assumptions surfaced

- **Willingness to pay (risky):** the evidence is a few unprompted "I'd pay for that" comments in support tickets plus the observation that scheduled-export/API-style workflows are the kind teams don't like rebuilding elsewhere once working. The user was explicit: "nothing tells me that for certain yet... 'I'd pay for that' in a support ticket isn't a credit card." This is the load-bearing, still-unvalidated core of the whole idea.
- **Bundling was necessary (unvalidated, now retired in favor of unbundling):** the three features were grouped as "the power-user tier" because they showed up together in tickets, not because bundling itself was tested. The user concluded: "I bundled all three mostly because they showed up together in my head... not because I'd tested whether that bundling was necessary."
- **Goodwill risk is contained (risky):** the user's biggest stated worry is "ticking off free users," yet the mechanism requires restricting access some of those exact free power users currently rely on. The user's own correction: "I have to be straight with myself: that IS a clawback, even if it doesn't feel like one."
- **Grace-period outreach is adequate (unvalidated):** the plan for reaching anonymous scrapers (no account, no email) is deprecation notices on the endpoint response, in-app banners, and a changelog post — untested against whether that actually reaches the people affected.

## Contradictions & how resolved

1. **"Nothing free gets clawed back" vs. "undocumented endpoints get locked down to create the paid incentive."** Surfaced directly; the user resolved it by narrowing the claim to "nothing documented and supported gets clawed back" and adding a grace-period mitigation. Not left unresolved — counts as a sharpening, not a refutation.
2. **"Grace period is two months" vs. "my gut says two-to-four weeks."** Surfaced directly; the user clarified these weren't competing numbers but two different things conflated in one breath — notices start immediately, but the full window is two months. Resolved, no lingering conflict.

## Open questions (aporia)

- What conversion/click-through bar should gate the API-only test, since the original bundle's 5%/1% bar was never derived for a single, narrower feature aimed at a smaller slice of the cohort.
- How to reach scrapers who have no account and thus no email — the stated fallback (endpoint messages, banners, changelog) is unverified.
- The day-60 kill-switch decision and the two-month grace-period cutoff coincide almost exactly. Nobody has examined what happens if the experiment fails right as access is cut off — free/scraping users would lose access with nothing successful to show for it.

## Suggested next step

Set a conversion/click-through threshold specific to the API-only test — don't reuse the bundle's 5%/1% by default — then ship the documented, rate-limited API alone as the first Pro feature, with grace-period notices to existing endpoint users starting immediately at launch.
