---
schema: idea-brief-v1
idea: shared-expenses-app
date: 2026-07-20
mode: develop
depth: standard
verdict: sharpened
thesis_final: "A ten-second-to-use expense logger for four roommates that removes the friction
  of logging shared costs (rent, utilities, groceries, one-offs) in the moment, then nets
  everything down to a minimum-transfer settlement at month-end."
assumptions:
  - text: "Making logging fast/low-friction (~10 seconds from phone) is what actually gets
      people to log promptly, versus the current two-week-later habit"
    status: unvalidated
  - text: "A flat even four-way split (ignoring the room-size/rent difference) is acceptable
      to all four roommates long-term"
    status: validated
open_questions: []
constraints:
  - "Standing categories are rent, utilities, groceries, split evenly four ways by agreement"
  - "One-off costs (e.g. paper towels, shared Amazon orders) are tagged separately but still
    net into the same month-end settlement"
next_step: "session in progress — no next step yet"
---

# Idea brief: shared-expenses app

## What changed under questioning
Initial: an app that logs shared costs as they happen and tells the household who owes who
at month-end. Corrected immediately: it's not a running tally people check anytime — it's a
fixed monthly reconciliation, netted to a minimum number of settlement payments.
Mid-session shift: the user first framed the problem as "the math is messy," but when pressed
on what actually breaks about the current spreadsheet, admitted "it's the nagging... someone
always has to chase everyone to actually fill it in" — the real problem is logging compliance,
not settlement math. The thesis is being pulled toward "fast logging removes the friction"
as the mechanism that fixes that.

## Scope
For: the user's four-person household. Standing shared categories: rent, utilities, groceries
(split evenly by agreement, despite the user's larger room costing more — they eat the
difference). One-off shared costs (paper towels, shared Amazon orders) are tagged separately
but roll into the same month-end settlement. Settlement itself nets balances down to the
minimum number of transfers (e.g., in a 4-person example, 2 payments instead of up to 12).

## Assumptions surfaced
The design assumes friction-free logging (~10 seconds, phone-based) will change actual
behavior — this hasn't been tested against the household's real pattern of waiting ~2 weeks
to log. The even four-way split for rent, despite unequal room sizes, is something the user
confirmed the household already actively agreed to and lives with, not a live sore point.

## Contradictions & how resolved
None surfacing as contradictions requiring a "which yields" resolution yet.

## Open questions (aporia)
None yet — session in progress.

## Suggested next step
Session in progress — no next step yet.
