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

## Development Workflow & Commit Requirements

### STRICT COMMIT REQUIREMENTS
**CRITICAL**: Python files (`ytfast.py`) **MUST NOT** be committed to the repository without completing ALL of the following steps:

1. **Implementation**: Claude outputs the code changes in a Markdown code block
2. **Version Update**: Claude **MUST** increment `SCRIPT_VERSION` with every code output
3. **User Testing**: User **MUST** test the script in OBS Studio
4. **Log Verification**: User **MUST** provide relevant script logs showing:
   - Script version loaded message
   - Successful execution of the implemented feature
   - No critical errors
5. **User Approval**: User **MUST** explicitly approve the implementation
6. **Commit**: Only after ALL above steps are complete, commit with the suggested message

### Testing Checklist
Before any commit, the user must verify:
- [ ] Script loads without errors
- [ ] Version number in logs matches the latest implementation
- [ ] New feature works as expected
- [ ] No regressions in existing functionality
- [ ] Logs show expected behavior
- [ ] User has explicitly stated approval

### Log Requirements
Users must provide logs showing:
```
[ytfast.py] [timestamp] Script version X.Y.Z loaded
[ytfast.py] [timestamp] [Feature-specific success messages]
[ytfast.py] [timestamp] [No critical errors]
```

### Approval Format
User must explicitly state one of:
- "Approved for commit"
- "Testing successful, ready to commit"
- "All tests passed, please commit"

**NO COMMITS WITHOUT EXPLICIT APPROVAL AND LOGS**

## Testing Version
Users should always check the OBS logs to verify the correct version is loaded:
```
[ytfast.py] [timestamp] Script version X.Y.Z loaded
```

## Commit Messages
After each Phase implementation and **successful testing with user approval**, use a concise but informative commit message (e.g. *"Add playlist sync thread"*).

Always reconcile implementations with **02‑Requirements.md** and respect environment rules in **03‑OBS_API.md**.

*Prev → 03‑OBS_API.md | Next → ../phases/Phase-01-Scaffolding.md*
