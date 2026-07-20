---
schema: idea-brief-v1
idea: billing-service-rust-rewrite
date: 2026-07-20
mode: stress
depth: standard
verdict: aporia
thesis_final: "The Python billing service caused two outages traced to architecture problems (unbounded request-body buffering, missing DB row locking) rather than to anything Rust's memory-safety model addresses; whether a rewrite in Rust specifically is justified, versus fixing those problems within Python, is unresolved."
questions_asked: 3
types_used: [evidence, assumptions, viewpoints]
assumptions:
  - text: "Rust's memory safety and lack of GC pauses would have prevented the two outages."
    status: risky
  - text: "A full rewrite is the only way to force the concurrency/locking model to be redesigned properly; a Python-only fix wouldn't get the same discipline."
    status: unvalidated
open_questions:
  - "What does Rust specifically buy that a Python fix (streaming request bodies, SELECT FOR UPDATE row locking, a task queue with better guarantees than Celery) wouldn't?"
constraints: []
next_step: "Before committing to a rewrite, spec out the Python-only fix (streaming bodies, SELECT FOR UPDATE locking, a better-behaved task queue) and compare its cost and risk against a Rust rewrite, to isolate what Rust specifically adds."
---

# Idea brief: billing-service-rust-rewrite

## What changed under questioning
Initial thesis: the Python billing service should be rewritten in Rust because it caused two outages, and Rust's memory safety and GC-pause-free latency would fix the underlying problem.

Final thesis: both outages trace to architecture bugs — unbounded in-memory request buffering, and a missing database row lock across two Celery workers — neither of which is a memory-safety problem in the sense Rust addresses. The user explicitly conceded "the language itself doesn't fix a missing lock" and reframed the rewrite as a forcing function for a concurrency redesign (sqlx with `SELECT FOR UPDATE`, an actix-based task queue instead of Celery), but did not establish why that redesign requires a new language rather than being done in Python.

## Scope
Billing service, currently implemented in Python, running on Celery workers for background/async work (e.g. invoice/balance updates) and handling payment webhooks synchronously. Not otherwise scoped in this session (no discussion of team size, timeline, or budget).

## Assumptions surfaced
- "Rust's memory safety and lack of GC pauses would have prevented the outages" — the user's opening justification. Outage 1 (OOM from buffering full request bodies) is a streaming/design issue, not a language-safety issue. Outage 2 (double-charge from a locking race across two separate worker processes) is a database transaction-isolation issue; Rust's memory-safety guarantees apply to shared memory within a single process, not to races across separate processes over a shared database row. The user conceded the language itself doesn't fix a missing lock. Marked **risky**.
- "A full rewrite is the forcing function needed to get the concurrency model redesigned properly" — introduced as the user's fallback justification after the above concession. Never tested against the alternative of doing the same redesign (row locking, streaming, better queue semantics) inside the existing Python stack. Marked **unvalidated**.

## Contradictions & how resolved
No outright contradiction between two stated claims — the user's own root-cause account (buffering, locking) didn't support their opening causal claim (memory safety, GC pauses), and the user acknowledged this directly rather than defending it. This moved the session to aporia rather than refutation: the justification shifted, but the resulting claim (rewrite-as-forcing-function) was not itself resolved or contradicted before the session ended.

## Open questions (aporia)
- What does Rust specifically buy that a Python-only fix — streaming request bodies, adding `SELECT FOR UPDATE` locking, replacing Celery with a task queue that gives better guarantees — wouldn't? This was asked directly and the session ended before it was answered.

## Suggested next step
Spec out the Python-only fix (streaming bodies, proper row locking, a better task queue) alongside a Rust-rewrite estimate, and compare cost/risk/timeline of each before deciding — so the choice of Rust is evaluated against what it actually adds, not against the outages alone.
