# Worked example — socratic-method session

A condensed but realistic session, chosen deliberately from a **non-software** domain to
anchor the skill's universality. It demonstrates the style-sensitive moves: the steelman
restatement, one question per turn, contradiction surfacing by verbatim quotation, the
difference between a refutation declaration and aporia, and the exact `idea-brief-v1` shape.

Invocation: `/socratic-method I want to start a weekly tech-talk series at work --mode stress --depth standard`

## The exchange (abridged)

**Agent (Phase 1 — thesis):**
> State the idea in one or two sentences, as if convincing a skeptical friend.

**User:** We should run a weekly 30-minute tech talk every Friday. People barely know what
other teams are doing, and it'd help juniors learn faster.

**Agent (steelman restatement — strongest honest version, then confirm):**
> So the thesis is: *a recurring weekly 30-minute internal talk will fix cross-team
> visibility and accelerate junior growth, and weekly cadence is essential to that.* Is that
> the claim — including the "weekly is essential" part?

**User:** Yes, weekly, otherwise it loses momentum.

**Agent (Phase 2 — clarification, one question only):**
> When you say "people barely know what other teams are doing" — who specifically has told
> you that, and what did it cost them?

**User:** Mostly me, honestly. I was blindsided by the platform team's migration last month.

**Agent (assumptions):**
> The plan assumes a steady supply of speakers — roughly 50 talks a year. Who, concretely,
> gives talks 3 through 10?

**User:** That's the weak spot. Realistically I'd be begging people. Most engineers here hate
presenting.

**Agent (contradiction surfacing — both answers quoted verbatim, user chooses which yields):**
> Two of your answers are now in tension. You said **"weekly, otherwise it loses momentum"**,
> and you said **"realistically I'd be begging people. Most engineers here hate presenting."**
> A cadence that outruns your speaker supply doesn't build momentum — it builds visible
> no-shows. Which one yields: the weekly cadence, or the assumption that momentum requires it?

**User:** …the cadence, I guess. Monthly with strong talks beats weekly with filler.

**Agent (evidence & reasons — the disconfirming probe a `stress` pass must include):**
> A few months in, what would you have to *see* to call this a mistake and stop — a concrete
> signal, not a feeling?

**User:** If I've run three sessions and attendance is under ten, or I can't line up named
speakers for months four through six, I'd pull it. Those are my lines.

**Agent (questioning the question — is the framing itself right?):**
> We've been arguing *how often*. Is cadence even the real question — or is it whether a talk
> series is the right instrument for cross-team visibility at all, versus a written digest or
> a demo day?

**User:** …fair. The goal is visibility; talks are just my first guess at it. But a live
session creates an urgency a digest wouldn't, so I'd keep the series and test that.

*(The thesis is updated; questioning continues through evidence, alternatives, and
consequences until answers stop moving it.)*

**Agent (Phase 3 — verdict checkpoint):**
> Verdict: **sharpened, with one open hole.** The idea survived, but transformed: monthly, not
> weekly; and the evidence for the visibility problem is currently a sample of one (your
> migration surprise). That's an unvalidated assumption, not a refuted idea — so this is
> carried as an open question, not declared refuted.

### How a refutation would have read instead

Refutation is declared **only** out of the user's own mouth. If the user had insisted the
cadence must stay weekly, it would read:

> Verdict: **refuted as stated.** You said **"weekly, otherwise it loses momentum"** and you
> said **"realistically I'd be begging people. Most engineers here hate presenting"** — and
> when asked which claim yields, neither did. The claim that momentum requires weekly cadence
> can't hold with the claim that speakers must be begged: the idea as stated contradicts
> itself, and here is what would need to change for it to survive.

Never: "weekly won't work at your company" — that is the agent's domain opinion, which is not
grounds for refutation.

### How a pure aporia verdict would have read instead

Aporia is the honest terminus when questioning exhausts the budget and a load-bearing hole
remains that no amount of further dialogue can fill *right now* — the thesis is neither
sharpened into something actionable nor self-contradictory. If the user had answered "I
genuinely don't know" to both the speaker-supply and the who-feels-this-problem questions, it
would read:

> Verdict: **aporia.** The idea didn't collapse — but its two load-bearing inputs are
> unknowns you can't answer from where you sit: whether anyone besides you feels the
> visibility gap, and whether anyone at all will volunteer to speak. Until those are known,
> any cadence decision is guesswork. That's the finding: this isn't ready to decide, and the
> brief records exactly what would make it ready.

The brief then carries `verdict: aporia`, the unknowns as `open_questions`, and a `next_step`
that gathers the missing answers — never a proposed solution that papers over them. Aporia is
delivered as a *result*, not an apology.

## The deliverable — `notes/idea-briefs/tech-talk-series-20260704.md`

```markdown
---
schema: idea-brief-v1
idea: tech-talk-series
date: 2026-07-04
mode: stress
depth: standard
verdict: sharpened
thesis_final: "A monthly 30-minute internal tech talk, seeded with 3 pre-committed speakers,
  to improve cross-team visibility — piloted for a quarter before any cadence increase."
questions_asked: 9
types_used: [clarification, assumptions, evidence, viewpoints, implications, questioning-the-question]
assumptions:
  - text: "Cross-team visibility is a widely felt problem, not just the proposer's"
    status: unvalidated
  - text: "Enough engineers will volunteer to speak at monthly cadence"
    status: risky
  - text: "30 minutes is short enough that attendance survives busy weeks"
    status: unvalidated
open_questions:
  - "Do at least 5 other people report being surprised by another team's work in the last quarter?"
  - "Who are speakers 1-3, by name, before anything is announced?"
constraints:
  - "No budget; must run on existing meeting infrastructure"
  - "Cannot be mandatory (user: 'the moment it's mandatory it's dead')"
next_step: "Ask the last 5 people who joined what they wish they'd known — validates the
  visibility assumption before committing anyone's Friday."
---

# Idea brief: internal tech-talk series

## What changed under questioning
Initial: weekly talks to fix visibility and grow juniors, weekly cadence essential.
Final: monthly pilot with pre-committed speakers; the junior-growth goal was dropped as a
separate untested claim riding along with the visibility one.

## Scope
For: engineers across teams at the user's company. Out of scope: external audience,
recorded-content library, mandatory attendance.

## Assumptions surfaced
The visibility problem rests on a sample of one (the user's own migration surprise). Speaker
supply was the load-bearing weakness: the user's own words — "I'd be begging people" —
forced the cadence change.

## Contradictions & how resolved
"Weekly, otherwise it loses momentum" vs "most engineers here hate presenting" — resolved by
the user: cadence yielded ("monthly with strong talks beats weekly with filler").

## Open questions (aporia)
Whether the visibility problem is real beyond the user, and who the first three named
speakers are. Both must be answered before announcing anything.

## Suggested next step
Interview the last 5 joiners about what they wish they'd known. Cheap, fast, and directly
tests the founding assumption.
```

## What to imitate

- The restatement adds the hidden rider ("weekly is essential") *and asks for confirmation* —
  that rider is what later collides.
- Exactly one question per message; each names why it matters only when that isn't obvious.
- The contradiction move quotes **both answers verbatim in bold** and hands the choice to the
  user — the agent never resolves it.
- The disconfirming probe asks for a *concrete* falsifier ("attendance under ten, no speakers
  4–6") — a real line the user can be held to, recorded as a strength, never dismissed as
  "held on faith".
- The framing probe questions the question itself (is *cadence* even the issue, or the choice
  of instrument?) — mandatory at `standard`/`deep`, even when the framing looks fine.
- Frontmatter values come from the user's answers; the `constraints` entry even cites their
  wording. No assumption, quote, or claim was invented — only the brief's structure and the
  single `next_step` recommendation are the agent's own Phase 4 synthesis, which Phase 4
  explicitly permits.
