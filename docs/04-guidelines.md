# 04‑Guidelines (Output & Coding Style)

## Output Rules
1. Claude outputs modular code: minimal `ytfast.py` plus modules in `<scriptname>_modules/` directory
2. Main script contains only OBS interface functions; all logic goes in modules
3. Include an OBS script description docstring ≤ 400 characters in main script
4. No external dependencies besides Python std lib and OBS‑bundled libs

## Module Structure
- **Main script** (`ytfast.py`): Minimal OBS interface only
- **Modules folder** (`<scriptname>_modules/`):
  - `config.py` - Configuration constants
  - `logger.py` - Logging system
  - `state.py` - Thread-safe state management
  - `utils.py` - Utility functions
  - Individual feature modules for each component

## Coding Style
- Follow PEP‑8 (≤ 120 chars per line where practical)
- Use functions/classes for clarity; comment major sections
- Each module has single responsibility
- Protect shared state through `state.py` accessors
- Wrap worker loops in `try/except`

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
**CRITICAL**: Claude **must** increment the `SCRIPT_VERSION` constant in `config.py` with **EVERY** code change:
- **PATCH** increment (x.x.Z): Bug fixes, minor changes, iterations within a phase
- **MINOR** increment (x.Y.x): New features, completing a new phase implementation
- **MAJOR** increment (X.x.x): Breaking changes, major refactors, final releases

**Important**: The version must be incremented **every time** Claude outputs code, not just once per phase. This ensures that during testing, users can verify they are running the correct version of the code.

Examples:
- Phase 2 initial implementation: `1.0.0` → `1.1.0` (MINOR for new phase)
- Bug fix during Phase 2 testing: `1.1.0` → `1.1.1` (PATCH for iteration)
- Another iteration in Phase 2: `1.1.1` → `1.1.2` (PATCH for iteration)
- Phase 3 implementation: `1.1.2` → `1.2.0` (MINOR for new phase)
- Modular refactoring: `1.9.0` → `2.0.0` (MAJOR for architecture change)

## Development Workflow & Commit Requirements

### STRICT COMMIT REQUIREMENTS
**CRITICAL**: Code changes **MUST NOT** be committed to the repository without completing ALL of the following steps:

1. **Implementation**: Claude outputs the code changes (main script and/or modules)
2. **Version Update**: Claude **MUST** increment `SCRIPT_VERSION` in `config.py` with every code output
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

## Module Development Guidelines
- Avoid circular imports by importing at function level when necessary
- All configuration constants go in `config.py`
- All shared state goes through `state.py` with thread-safe accessors
- Heavy processing happens in background threads
- OBS API calls only on main thread
- Each module should have clear docstring explaining its purpose

## Testing Version
Users should always check the OBS logs to verify the correct version is loaded:
```
[ytfast.py] [timestamp] Script version X.Y.Z loaded
```

## Commit Messages
After each Phase implementation and **successful testing with user approval**, use a concise but informative commit message (e.g. *"Add playlist sync thread"*, *"Implement Phase 10 - Playback control"*).

Always reconcile implementations with **02‑Requirements.md** and respect environment rules in **03‑OBS_API.md**.

*Prev → 03‑OBS_API.md | Next → ../phases/Phase-01-Scaffolding.md*
