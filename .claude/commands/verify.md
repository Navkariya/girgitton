---
description: Lint + type + test pipeline (ruff, mypy, pytest)
---

Verify the Girgitton codebase end-to-end:

1. `ruff check src/ tests/`
2. `ruff format --check src/ tests/`
3. `mypy src/girgitton`
4. `pytest -q`
5. `bandit -r src/ -ll`

Report any failures with file:line references and suggested fixes.
