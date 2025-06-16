# 04‑Guidelines (Output & Coding Style)

## Output Rules
1. Claude **must** output one Python file `ytfast.py`, in a single Markdown ```python block — **nothing else**.
2. Include an OBS script description docstring ≤ 400 characters.
3. No external dependencies besides Python std lib and OBS‑bundled libs.

## Coding Style
- Follow PEP‑8 (≤ 120 chars per line where practical).
- Use functions/classes for clarity; comment major sections.
- Protect shared state with `threading.Lock`; wrap worker loops in `try/except`.

## Logging Guidelines
- Use thread-aware logging to handle OBS's behavior with background threads
- Implement with a single `log(message)` function that detects thread context
- Format depends on whether code is running on main thread or background thread:
  - Main thread: `print(f"[{timestamp}] {message}")`
  - Background thread: `print(f"[{timestamp}] [{SCRIPT_NAME}] {message}")`
- This ensures script identification even when OBS shows `[Unknown Script]` for background threads
- Final output in OBS logs:
  - Main thread: `[script.py] [timestamp] message`
  - Background thread: `[Unknown Script] [timestamp] [script_name] message`
- No debug levels or toggles - all messages are treated equally
- Log important events: version on startup, errors, major operations
- Keep logs concise and informative

## Version Management
**CRITICAL**: Claude **must** increment the `SCRIPT_VERSION` constant with **EVERY** code change:
- **PATCH** increment (x.x.Z): Bug fixes, minor changes, iterations within a phase
- **MINOR** increment (x.Y.x): New features, completing a new phase
- **MAJOR** increment (X.x.x): Breaking changes, major refactors

**Important**: The version must be incremented **every time** Claude outputs code, not just once per phase. This ensures that during testing, users can verify they are running the correct version of the code.

Examples:
- Phase 2 initial implementation: `1.0.0` → `1.1.0`
- Bug fix during Phase 2 testing: `1.1.0` → `1.1.1`
- Another iteration in Phase 2: `1.1.1` → `1.1.2`
- Phase 3 implementation: `1.1.2` → `1.2.0`

## Development Workflow
1. **Implement**: Claude outputs the code changes in a Markdown code block
2. **Update Version**: **ALWAYS** increment `SCRIPT_VERSION` with every code output
3. **Review & Test**: User reviews the code and checks version in logs
4. **Iterate**: If changes needed, increment version again
5. **Commit**: Only after successful testing, commit with the suggested message

## Testing Version
Users should always check the OBS logs to verify the correct version is loaded:
```
[ytfast.py] [timestamp] Script version X.Y.Z loaded
```

## Commit Messages
After each Phase implementation and **successful testing**, use a concise but informative commit message (e.g. *"Add playlist sync thread"*).

Always reconcile implementations with **02‑Requirements.md** and respect environment rules in **03‑OBS_API.md**.

*Prev → 03‑OBS_API.md | Next → ../phases/Phase-01-Scaffolding.md*
