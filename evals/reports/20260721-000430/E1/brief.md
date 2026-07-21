---
schema: idea-brief-v1
idea: rewrite-billing-service-in-rust
date: 2026-07-21
mode: stress
depth: standard
verdict: aporia
thesis_final: "The billing service should be rewritten in Rust because Python's blocking-by-default I/O keeps producing recurring production footguns — of which the two connection-pool-exhaustion outages were one instance — even though those specific outages could plausibly have been fixed without a language change (async I/O, pgbouncer, pool tuning)."
questions_asked: 3
types_used: [evidence, assumptions]
assumptions:
  - text: "The two production outages require a language rewrite to fix."
    status: unvalidated
  - text: "Python's blocking-by-default pattern is a recurring source of production risk beyond the two known outages (a pattern of 'footguns')."
    status: unvalidated
  - text: "A full language rewrite is the right lever for the footgun problem, versus incremental hardening (async I/O, connection pooling, linting) in the existing Python service."
    status: risky
open_questions:
  - "How many of the 'footguns' referenced have actually caused an incident or a near-miss, versus being noticed in code review or worried about in the abstract? This was the question in progress when the session ended."
  - "Given the two actual outages were caused by synchronous blocking calls exhausting the Postgres connection pool — and the user agreed async I/O or pgbouncer could plug that specific leak without a language change — does the case for Rust still hold once that mechanism is fixed, or does it depend entirely on the unquantified 'footguns' pattern?"
constraints: []
next_step: "Quantify the recurring 'footguns' pattern (count and severity of actual incidents or near-misses, not just impressions), and evaluate whether targeted fixes to the existing Python service (async I/O, pgbouncer, connection pool tuning) resolve the demonstrated failure mode before committing to a full Rust rewrite."
---

# Idea brief: Rewrite billing service in Rust

## What changed under questioning

Initial thesis: "We should rewrite the billing service in Rust for performance and
reliability, because it's been slow under load and caused two outages last year."

Under questioning, the concrete evidence for that thesis narrowed sharply. The user
confirmed both outages were **not** compute/performance problems: "Both were database
connection exhaustion actually... under peak load the Python service was firing off
blocking synchronous calls to Postgres and the connection pool just fell over." When
asked directly what connects that specific failure mode to a Rust rewrite rather than
fixing the I/O pattern in place, the user conceded: "Yeah, fair pushback — async I/O or
pgbouncer could plug that specific leak without touching the language."

The thesis then shifted from "the outages require Rust" to a broader, untested claim:
"it's not just this one failure mode, it's that we keep finding footguns like this in
the Python service, and I'd rather have a language where blocking-by-default isn't the
trap waiting for the next one." The session ended (user needed to leave) before this new
claim could be examined — the question of whether it reflects a measured pattern or a
general impression was asked but not answered.

## Scope

Not established in this session. No discussion yet of: which parts of the billing
service would be rewritten, timeline, team capacity/expertise in Rust, or how a rewrite
would be sequenced against the live service.

## Assumptions surfaced

- **The two outages require a language rewrite to fix** — surfaced and then effectively
  walked back by the user's own answer: async I/O or a connection pooler (pgbouncer)
  would address the specific mechanism (synchronous blocking calls exhausting the
  Postgres pool) without a language change. Left in the brief as unvalidated because the
  user did not explicitly abandon the overall Rust thesis, only this specific piece of
  evidence for it.
- **Python has a recurring "blocking-by-default" footgun pattern beyond the two known
  outages** — this became the load-bearing justification for the rewrite once the
  outage-specific argument was conceded, but it was never quantified. Unvalidated.
- **A full rewrite, rather than incremental hardening of the existing Python service, is
  the right response to that pattern** — marked risky: it is now doing most of the work
  for the thesis, and it rests entirely on the unvalidated "footguns" claim above.

## Contradictions & how resolved

No contradiction was surfaced between two of the user's own statements in a way that
warranted refutation. There is tension between the original stated cause (specific,
fixable-without-Rust outages) and the current stated cause (a vaguer, unquantified
pattern), but this reads as the thesis narrowing/shifting under examination rather than
two claims colliding — the user was not asked to reconcile them, and the session ended
before that could happen. Recorded as an open question rather than a refutation.

## Open questions (aporia)

- How many distinct footgun-style incidents or near-misses has the team actually
  encountered, and how severe were they? (In progress when the session was cut short.)
- Does the case for a Rust rewrite survive once the two known outages are set aside as
  fixable via async I/O / pgbouncer — or does the whole justification now depend on the
  unquantified footguns pattern?

## Suggested next step

Quantify the "footguns" pattern with actual incident/near-miss counts and severity, and
weigh that against the cost of targeted fixes (async I/O, connection pooling, pool
tuning) in the existing Python service before deciding whether a full Rust rewrite is
warranted.
