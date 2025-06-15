# 04‑Guidelines (Output & Coding Style)

## Output Rules
1. Claude **must** output one Python file `ytfast.py`, in a single Markdown ```python block — **nothing else**.
2. Include an OBS script description docstring ≤ 400 characters.
3. No external dependencies besides Python std lib and OBS‑bundled libs.

## Coding Style
- Follow PEP‑8 (≤ 120 chars per line where practical).
- Use functions/classes for clarity; comment major sections.
- Protect shared state with `threading.Lock`; wrap worker loops in `try/except`.

## Commit Messages
After each Phase prompt, propose a concise but informative commit message (e.g. *"Add playlist sync thread"*).

Always reconcile implementations with **02‑Requirements.md** and respect environment rules in **03‑OBS_API.md**.

*Prev → 03‑OBS_API.md | Next → 05‑Phase‑01‑Scaffolding.md*