---
schema: idea-brief-v1
idea: billing-service-rust-rewrite
date: 2026-07-20
mode: stress
depth: standard
verdict: aporia
thesis_final: "Billing service should be rewritten in Rust for type-safety and predictable performance to prevent outages -- though the two prior outages traced primarily to connection-pool sizing rather than the language, leaving what the rewrite actually buys over a targeted fix unresolved."
questions_asked: 3
types_used: [evidence, assumptions, implications]
assumptions:
  - text: "Python's performance ceiling is the true cause of the billing outages"
    status: risky
  - text: "A Rust rewrite is necessary to get predictable performance and avoid another 3am page"
    status: risky
  - text: "The fee-calculation code genuinely chews CPU under peak load"
    status: validated
open_questions:
  - "What does a full Rust rewrite solve that fixing the connection-pool sizing (and possibly optimizing the fee-calc hot path in place) would not?"
constraints: []
next_step: "Before committing to a rewrite, test whether resizing the connection pool plus targeted fee-calc optimization eliminates the outage risk under simulated peak load; if it does, the case for a full Rust rewrite needs a justification other than outage prevention (e.g. type-safety or long-term maintainability)."
---

# Idea brief: Billing service Rust rewrite

## What changed under questioning
Initial thesis: Python is fine for CRUD but not fast enough for the billing service's synchronous fee calculations under load; two outages last year plus a desire for type-safety and predictable performance justify a full Rust rewrite.

Final state: under questioning, the user's own account of the outages shifted the causal story. The profiler showed fee-calc "chewing CPU under load," but "the real killer was a connection pool that wasn't sized for the concurrent spike, so requests backed up and cascaded into timeouts." Asked directly whether the outages would still have happened with only the pool fixed, the user said: "Honestly, no -- if we'd just fixed the pool sizing I think we'd have absorbed the spike fine. The CPU chewing was real but secondary, it made things slower, not down." That concedes the outage-prevention motivation for the rewrite doesn't hold as stated. The follow-up question -- what a Rust rewrite specifically buys beyond a pool-sizing fix -- was asked but not answered before the user ended the session.

## Scope
The billing service's synchronous fee-calculation path, under peak/concurrent-spike traffic. Not discussed: any other service, migration approach, or timeline. Out of scope for this brief.

## Assumptions surfaced
- "Python's performance ceiling causes the outages" -- load-bearing for the original justification, but the user's own account attributes both outages primarily to connection-pool sizing, not language speed. Marked risky rather than invalidated outright, since the follow-up question that would have settled it went unanswered.
- "A Rust rewrite is necessary to avoid another 3am page" -- depends directly on the assumption above; equally risky and equally unresolved.
- "The fee-calc code genuinely chews CPU under load" -- validated: the user cited profiler evidence directly, independent of the pool-sizing question.

## Contradictions & how resolved
Unresolved. The rewrite's stated motivation ("predictable performance instead of another 3am page") assumes the outages were a language/performance problem. The user's own narrative instead attributes both outages mainly to a connection pool "not sized for the concurrent spike," with CPU load as a secondary factor that made things "slower, not down." This was surfaced and the user was asked what the rewrite solves beyond a pool-sizing fix -- but the session ended on a stop signal before a substantive answer, so this is recorded as an open question, not a refutation (no verbatim colliding quotes were pushed to a "which yields" resolution).

Disclosed gaps in the stress pass: no explicit falsification question ("what would change your mind about this") was completed -- the counterfactual about pool sizing served a similar function but wasn't framed that way. No questioning-the-question probe (is "rewrite vs. targeted fix" even the right framing) was completed before the stop.

## Open questions (aporia)
- What does a full Rust rewrite solve that fixing the connection-pool sizing (and possibly optimizing the fee-calc hot path in place) would not?

## Suggested next step
Before committing to a rewrite, test whether resizing the connection pool plus targeted fee-calc optimization eliminates the outage risk under simulated peak load; if it does, the case for a full Rust rewrite needs a justification other than outage prevention (e.g. type-safety or long-term maintainability).
