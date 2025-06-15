# 04‑Guidelines (Output & Coding Style)

## Output Rules
1. Claude **must** output one Python file `ytfast.py`, in a single Markdown ```python block — **nothing else**.
2. Include an OBS script description docstring ≤ 400 characters.
3. No external dependencies besides Python std lib and OBS‑bundled libs.

## Coding Style
- Follow PEP‑8 (≤ 120 chars per line where practical).
- Use functions/classes for clarity; comment major sections.
- Protect shared state with `threading.Lock`; wrap worker loops in `try/except`.

## Version Management
**IMPORTANT**: When implementing each phase, Claude **must** increment the `SCRIPT_VERSION` constant:
- **PATCH** increment (x.x.Z): Bug fixes, minor changes
- **MINOR** increment (x.Y.x): New features, non-breaking changes (most phases)
- **MAJOR** increment (X.x.x): Breaking changes, major refactors

Example: Phase 4 adds video processing → increment from `1.0.0` to `1.1.0`

## Development Workflow
1. **Implement**: Claude outputs the code changes in a Markdown code block
2. **Update Version**: Increment `SCRIPT_VERSION` appropriately
3. **Review & Test**: User reviews the code and tests it in OBS
4. **Commit**: Only after successful testing, commit with the suggested message

## Commit Messages
After each Phase implementation and **successful testing**, use a concise but informative commit message (e.g. *"Add playlist sync thread"*).

Always reconcile implementations with **02‑Requirements.md** and respect environment rules in **03‑OBS_API.md**.

*Prev → 03‑OBS_API.md | Next → ../phases/Phase-01-Scaffolding.md*