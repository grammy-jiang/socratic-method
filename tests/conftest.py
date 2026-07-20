"""Shared pytest setup.

The eval harness lives in ``evals/`` as a script directory, intentionally not packaged.
Its grader functions are pure (no LLM calls), so we make ``graders`` importable for unit
tests by putting ``evals/`` on the path — without turning it into an installable package.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))
