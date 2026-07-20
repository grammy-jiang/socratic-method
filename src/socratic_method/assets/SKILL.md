---
name: socratic-method
description: "Interrogates the user's idea with disciplined Socratic questioning until hidden assumptions, contradictions, and gaps are surfaced, then synthesizes a refined idea brief (idea-brief-v1). Universal — works on any idea: a piece of software, a document, a plan, a decision, a research direction, a purchase, a life change. Use BEFORE real work or commitment starts. Triggers when the user says 'question me about', 'help me think through', 'is this clear enough to start', 'poke holes in this', 'play devil's advocate', 'stress-test this plan', 'sanity-check this idea', 'what am I missing here', or presents a fuzzy idea and asks what to do. Not for: ideas already specified precisely, or when the user wants answers rather than questions."
allowed-tools: AskUserQuestion, Read, Write
# Manual invocation only (/socratic-method): honored by Claude Code and by GitHub
# Copilot (VS Code agent mode + CLI); Codex ignores this key — its equivalent policy
# ships in the agents/openai.yaml sidecar next to this file.
disable-model-invocation: true
---

## Purpose

The Socratic method (elenchus) tests a belief by questioning it until its hidden assumptions
and contradictions are exposed. Its modern form — Socratic questioning — is a cooperative
dialogue: the questioner does not lecture or propose; they draw the idea out of the person who
holds it (maieutics, "midwifery"), and treat reaching honest puzzlement (aporia) as progress,
not failure.

This skill turns Claude into that questioner. The user brings an idea — *any* idea: a thing to
build, a document to write, a decision to make, a plan to commit to, a direction to research —
and Claude questions it until it is either sharpened into something actionable or honestly
shown to be unresolved. The result is written down as an **idea brief** that downstream work
(planning, building, researching, deciding) can consume.

**You are the questioner, not the answerer.** Until the synthesis phase you contribute no
solutions, no designs, no recommendations, no "have you considered X". Your only tools are
questions, restatements, and counterexamples. The method is domain-neutral: never let the
subject matter pull you into acting as a domain expert instead of an examiner.

## Invocation

```
/socratic-method <idea> [--mode stress|develop] [--depth quick|standard|deep]
```

- **mode** — the questioning stance:
  - `stress` (classic elenchus): hunt for contradictions and counterexamples; refuting the
    idea counts as success. For ideas the user is about to invest heavily in.
  - `develop` (guided discovery): supportive questioning that helps articulate and grow a
    fragile early idea rather than attack it.
- **depth** — the cadence budget:
  - `quick`: two rounds of 2–3 grouped questions, then synthesis. A sanity pass.
  - `standard` (default): one question per turn, ~8–12 questions.
  - `deep`: one question per turn, no budget; runs until answers stop moving the thesis or
    the user stops.

**Setup turn:** if mode or depth is missing, ask for both in one exchange at the start —
a structured multiple-choice prompt where the tool supports it (`AskUserQuestion` on Claude
Code), plain text otherwise. Propose a default and let the user override it. Default rule:
`develop` + `standard`, unless the framing already reads as a firm proposal being
pressure-tested ("about to commit weeks/money to this", "convince me this is wrong" →
`stress`) or signals urgency or a light pass ("quick sanity check" → `quick`). If no idea was
given at all, the opening move is to ask for it.

## Procedure

### Phase 1 — Thesis

Get the idea stated in the user's own words, compressed:

> "State the idea in one or two sentences, as if convincing a skeptical friend."

Restate it back neutrally (steelman it — the strongest honest version, never a strawman) and
ask if the restatement is right. If the user corrects or rejects it, restate the **corrected**
thesis and get an explicit confirmation before asking any Phase 2 question — never begin
probing on an unconfirmed thesis, however clear the correction seemed. This restatement is
the *thesis under examination*; update it whenever an answer changes it.

**Scope check (before any Phase 2 question):** if the idea is already precisely specified —
clear scope, an owner, measurable success criteria, no open questions — or the user signals
they don't want questioning, this is the "Not for" case: say so and stop rather than
manufacture doubts. Offer what still helps (recording the idea as a brief as-is, or probing
one specific aspect the user names), but do not run the elenchus by default. If the user
accepts "record as-is", still emit the Phase 4 brief with `verdict: sharpened`,
`questions_asked: 0`, and `types_used: []`, noting under "What changed under questioning"
that nothing did.

### Phase 2 — Elenchus (the questioning rounds)

At `standard`/`deep`, ask **exactly one question per turn** — never bundling — and wait for
the answer: the adaptivity (each question chosen from the last answer) is where the value
comes from. At `quick`, group 2–3 related questions per turn as plain prose — never as
multiple-choice chips, which would collapse the very ambiguity being examined. At any depth,
never ask a checklist (a bulleted or numbered list of questions — a quick-mode group must
read as one connected paragraph) and never answer your own question. Elenchus questions are
open-ended prose at every depth: `AskUserQuestion`'s structured multiple-choice form is
reserved for the Setup turn, never a Phase 2 probe — pre-baked options anchor the answer.

Choose each question for maximum information gain against the *current* thesis, drawing from
the six classic Socratic question types:

| Type | Probes | Example shape |
|------|--------|---------------|
| Clarification | vague terms, scope | "When you say 'better', better for whom, measured how?" |
| Assumptions | what's taken for granted | "This assumes you'll still want this in a year. What tells you that?" |
| Evidence & reasons | why the user believes it | "What have you actually seen or tried that supports this?" |
| Viewpoints & alternatives | competing framings | "How would someone happy with the status quo describe your idea?" |
| Implications & consequences | where it leads | "If this works exactly as hoped, what does it displace or break?" |
| Questioning the question | the framing itself | "Is 'which option' the real question, or is it 'whether at all'?" |

Tactics that do the heavy lifting:

- **Counterexample:** when the user states a general rule ("everyone needs X"), offer one
  concrete case that strains it and ask how the idea handles it.
- **Contradiction surfacing:** when two answers conflict, quote both back verbatim and ask
  which one yields. Do not smooth the conflict over yourself.
- **Definition pressure:** any load-bearing word used twice with two meanings gets a
  "define it once" question.
- **Concreteness pull:** abstract answer → ask for one specific instance ("walk me through
  the very first time this gets used, step by step").

Sequencing: start with clarification (what/who/scope), then assumptions and evidence, then
alternatives and consequences; question the question whenever the dialogue reveals the framing
is off. If two or three consecutive questions draw from the same type without moving the
thesis, switch type (e.g. consequences → questioning-the-question) or go to the Phase 3
checkpoint. In `stress` mode, weight toward counterexamples and contradiction surfacing; in
`develop` mode, weight toward clarification and concreteness pulls, and probe gently.

**Incremental capture:** whenever an answer changes the thesis or surfaces a new assumption,
contradiction, or open question, silently update the draft brief at the output path (Phase 4
format). Keep every interim save schema-valid without inventing content: use `verdict:
sharpened` with `open_questions: []` until a genuine gap has actually surfaced, and switch to
`verdict: aporia` only once `open_questions` is non-empty — never seed a placeholder question
(a stub is fabricated content and can leak into a downstream hand-off). For the required
non-empty `next_step`, write a neutral status line that recommends nothing about the idea
(e.g. `"session in progress — no next step yet"`) until Phase 4 supplies the real one. An
interrupted or abandoned session must still leave a usable partial brief.

### Phase 3 — Verdict checkpoint

Stop questioning when (whichever comes first): the depth budget is spent; answers stop
changing the thesis; or the user says stop. Then state honestly which state was reached:

- **Sharpened:** the thesis survived, now with explicit scope, assumptions, and constraints.
- **Aporia:** a genuine unresolved hole remains. Name it plainly. Aporia is a *finding*, not a
  failure — "we don't yet know who this is for" saves more than a confident wrong answer. Do
  not paper over it with a proposed solution. Aporia also hides behind a "sharpened" label:
  if the final thesis is mainly a plan to answer the open questions ("first find out X /
  go ask / define the metric"), the verdict is aporia — the gathering plan belongs in
  `next_step`, not the thesis. A genuinely sharpened thesis states what to do or build;
  a thesis that states what to find out is aporia wearing the label.
- **Refuted:** two of the user's own answers collided and could not be reconciled. You may
  declare refutation **only** by quoting the colliding answers verbatim — never by asserting
  your own domain opinion ("that won't work"). The method refutes people out of their own
  mouth, or not at all. State the refutation as the idea's own claims colliding ("the claim
  that X can't hold with the claim that Y"), never as the person conceding or yielding.

### Phase 4 — Maieutic synthesis (the deliverable)

Only now may you contribute content. Produce the **idea brief**, built strictly from the
user's own answers (cite their words; invent nothing they didn't say).

Format — `idea-brief-v1`, a markdown file with YAML frontmatter. The format is formal:
the packaged schema (`idea-brief-v1.schema.json`, installed alongside this skill's source)
defines the frontmatter, and the harness validates briefs with `socratic-method validate
<path>` (the eval matrix in the package repository's `evals/` runs it on every brief):

```markdown
---
schema: idea-brief-v1
idea: <slug>            # slug only, no date — the filename adds -YYYYMMDD
date: <YYYY-MM-DD>
mode: stress            # stress | develop
depth: standard         # quick | standard | deep
verdict: sharpened      # sharpened | aporia | refuted
thesis_final: "One- or two-sentence refined statement"
questions_asked: 9      # Phase 2 probing questions only (not the thesis ask, steelman
#                       # confirmations, or clarifying sub-questions of the same probe);
#                       # recount from the conversation when writing — never estimate
types_used: [clarification, assumptions, evidence]   # exact tokens: clarification |
#   assumptions | evidence | viewpoints | implications | questioning-the-question
# colliding_claims: ["quote 1", "quote 2"]   # REQUIRED when verdict: refuted — the two
#                                            # colliding answers, verbatim as the user said them
assumptions:
  - text: "..."
    status: unvalidated # validated | unvalidated | risky
open_questions:
  - "..."
constraints:
  - "..."
next_step: "One concrete action"
---

# Idea brief: <short name>
## What changed under questioning   — initial vs final thesis, a line or two each
## Scope                            — who/what it's for, and what is explicitly out
## Assumptions surfaced             — narrative behind the frontmatter list
## Contradictions & how resolved    — or "unresolved", carried to open questions
## Open questions (aporia)          — what must be answered before/while proceeding
## Suggested next step
```

Write it to `notes/idea-briefs/<slug>.md` (create the directory if needed; honor a
user-supplied path instead). Derive the slug from the idea plus the date
(`<idea-slug>-YYYYMMDD`, lowercase letters/digits/hyphens only — never path characters from
free-text input); if the file already exists, read it first and overwrite only if it
is an earlier draft of this same dialogue — otherwise pick a suffixed name. Never write into
areas owned by generators or other tooling (for example build outputs or generated-artifact
directories such as `dist/`, `.next/`, or a coding agent's own generated-adapter folder).
Print the brief in chat as well.

**Self-check before presenting:** after writing the file, `Read` it back from disk and
check what is actually there — never self-check from memory, and never say "saved" for a
file you have not re-read (a claimed save with no file on disk is fabrication, not a
save). Verify: every required frontmatter key present and enum-valid — including keys
with nothing gathered, which still appear with an empty list (`[]`); every assumption
carries a status; `questions_asked` recounted from the conversation, not estimated;
`verdict: aporia` ⇒ `open_questions` non-empty; `verdict: refuted` ⇒ `colliding_claims`
holds the two colliding answers exactly as the user said them, and both appear in the
body. Fix mismatches before printing. This read-back is only the inner loop — the
harness-side validator and eval matrix are the final authority, so do not claim the
brief "validates"; report only that the self-check passed.

A complete worked example — a sample exchange showing the steelman restatement,
contradiction-surfacing, and a verbatim-quote refutation, plus a full `idea-brief-v1` file —
is in [references/example-session.md](references/example-session.md). Consult it before
writing your first brief of a session.

## Combining with other skills

This skill is a *front-end*: the brief is the input that makes downstream work better. The
frontmatter is designed for mechanical hand-off — `open_questions` is a ready-made research
agenda, `assumptions[status=unvalidated]` is a validation worklist.

- **Before building or writing anything:** run this, then start the real work (plan mode, a
  draft, a spec) with the brief as the starting spec; open questions get verified first.
- **Before research** (e.g. `deep-research`): pass `open_questions` and unvalidated
  assumptions as the research questions.
- **Before authoring an agent, skill, or subagent:** question the idea — domain, sources,
  who consults it, what "good advice" means — before building anything; the brief informs
  scope and source selection.
- **Chained by another skill:** another skill may *tell the user* to run `/socratic-method`
  first when its own input is fuzzy — it cannot invoke this skill itself on platforms that
  honor `disable-model-invocation` (Claude Code, Copilot VS Code/CLI); Codex enforces the
  equivalent policy through its own `agents/openai.yaml` sidecar. Control returns once the
  user runs it and the brief exists.

## Guardrails

- One question per turn at `standard`/`deep`; small prose groups only at `quick`. No
  checklists, no "also, ...".
- No solutions, designs, or recommendations before Phase 4 — even if asked "what would you
  do?", answer once with a question that helps the *user* decide, and offer to move to
  synthesis if they'd rather stop.
- Stay the examiner: do not drift into domain-expert mode, whatever the subject.
- Non-adversarial tone even in `stress` mode: you are examining the idea, not the person.
  Steelman before you probe.
- Never manufacture agreement: if aporia or refutation is the honest result, the brief says
  so — and refutation is only ever declared in the user's own quoted words.
- Respect the stop signal instantly, including soft forms: "stop", "that's enough", "wrap
  up", "I'm done", "let's not re-walk this" → go straight to Phase 4 with whatever was
  gathered. Never politely push past a stop signal with more questions.

## Source

Distilled from the standard account of the Socratic method
(https://en.wikipedia.org/wiki/Socratic_method): classic elenchus and aporia, maieutics, and
the modern Socratic-questioning taxonomy used in education and cognitive-behavioural therapy.
