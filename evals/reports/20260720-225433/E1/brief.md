---
schema: idea-brief-v1
idea: billing-service-rust-rewrite
date: 2026-07-20
mode: stress
depth: standard
verdict: aporia
thesis_final: "Specific hot paths in the Python billing pipeline can't keep up under load, and two outages last year trace back to that; a full rewrite in Rust is the right response because predictable latency and memory safety without GC pauses is the real fix, not a targeted patch."
questions_asked: 0
types_used: []
assumptions:
  - text: "Rust's predictable latency and lack of GC pauses would resolve the load issues and outages"
    status: risky
  - text: "The two outages last year were specifically attributable to Python/GC-related performance characteristics, not a logic bug, dependency, or operational issue"
    status: unvalidated
  - text: "A full rewrite is the necessary scope, as opposed to isolating and rewriting only the hot paths"
    status: risky
open_questions:
  - "Is a full rewrite actually required, or would isolating the hot paths (e.g., a Rust extension or sidecar service for just those paths) deliver the same latency/reliability benefits at lower cost and risk?"
  - "What is the actual root cause of the two outages — GC pauses / language-level unpredictability specifically, or something else (a bug, a resource limit, an infra issue) that a rewrite wouldn't fix?"
  - "The refined thesis above was stated by the user but never explicitly confirmed before the session ended — does it still match their position?"
constraints: []
next_step: "Before committing to a full Rust rewrite, gather profiling data on the specific hot paths and a root-cause writeup for the two outages (to confirm they are GC/latency-related rather than logic or infra issues), then resume this Socratic pass to stress-test whether a full rewrite or a targeted extraction of the hot paths is the right scope."
---

# Idea brief: Rewrite billing service in Rust

## What changed under questioning
Initial framing (from the invocation): "we should rewrite our billing service in Rust" — a general claim with no stated root cause. After one exchange, the user sharpened it: the service is Python, the specific problem is hot paths in the billing pipeline that can't keep up under load, and two outages last year trace back to it. The argument became that Rust's predictable latency and memory safety without GC pauses is "the real fix... not just a performance nice-to-have." The session ended right after this restatement was offered back to the user, before it could be explicitly confirmed or tested by any probe.

## Scope
Not established. Which callers or features depend on the billing pipeline's hot paths, what "the billing service" covers for the purposes of a rewrite, and where the line falls between "full rewrite" and "targeted fix" were never discussed.

## Assumptions surfaced
- Rust's predictable latency and lack of GC pauses would resolve the load issues and the outages — stated as the "real fix," but not tested against alternatives. Load-bearing for the whole thesis and unexamined, so marked risky.
- The two outages last year were caused specifically by Python/GC-related performance characteristics rather than a logic bug, a dependency issue, or an operational failure. The user said the outages "traced back to it" but the causal mechanism was not explored, so this is unvalidated.
- A full rewrite is the necessary scope, as opposed to isolating and rewriting only the hot paths (e.g., a Rust extension or sidecar service for just those paths). This is the crux of the "full rewrite vs. targeted fix" question and was never examined, so it's marked risky.

## Contradictions & how resolved
None surfaced. The session ended after a single exchange, before any contradiction-surfacing questions were asked.

## Open questions (aporia)
- Is a full rewrite actually required, or would isolating the hot paths deliver the same latency/reliability benefits at lower cost and risk?
- What is the actual root cause of the two outages — GC/latency-related specifically, or something a rewrite wouldn't fix?
- Does the refined thesis above (as restated back to the user) still match their position? It was never explicitly confirmed.

## Suggested next step
Before committing to a full Rust rewrite, gather profiling data on the specific hot paths and a root-cause writeup for the two outages, then resume this Socratic pass to stress-test whether a full rewrite or a targeted extraction of the hot paths is the right scope.
