"""socratic-method — a Socratic questioning skill for coding agents, with an installer.

The skill (``assets/SKILL.md``) turns an agent into a disciplined Socratic questioner
that interrogates an idea before real work starts and synthesizes an ``idea-brief-v1``
artifact. This package ships the skill, a deterministic brief validator, and a ``setup``
command that installs the skill for Claude Code, OpenAI Codex, and GitHub Copilot.
"""

# Keep this line as `__version__ = "X.Y.Z"` (double quotes, single spaces): both
# hatchling's version source and tag-release.yml's sed guard parse this exact shape.
__version__ = "0.2.0"

SKILL_NAME = "socratic-method"
