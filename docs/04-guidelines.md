# 04‑Guidelines (Output & Coding Style)

## Output Rules
1. Claude outputs modular code: minimal main script plus modules in shared `ytplay_modules/` directory
2. Main script contains only OBS interface functions; all logic goes in modules
3. Include an OBS script description docstring ≤ 400 characters in main script
4. No external dependencies besides Python std lib and OBS‑bundled libs

## Module Structure (v3.5.0+ Common Modules Architecture)
- **Main scripts** (`ytplay.py`, `yt_worship.py`, etc.): Minimal OBS interface only
- **Shared modules folder** (`ytplay_modules/`):
  - `config.py` - Configuration constants
  - `logger.py` - Logging system with script identification
  - `state.py` - Thread-safe state management with script context
  - `utils.py` - Utility functions
  - Individual feature modules for each component

## Script Identification
- Each script identifies itself by its filename
- Script name is stored in state module on initialization
- All modules access script name from state when needed
- Enables proper logging and scene management for multiple instances

## Coding Style
- Follow PEP‑8 (≤ 120 chars per line where practical)
- Use functions/classes for clarity; comment major sections
- Each module has single responsibility
- Protect shared state through `state.py` accessors
- Wrap worker loops in `try/except`

## Logging Guidelines
- Use thread-aware logging to handle OBS's behavior with background threads
- Implement with a single `log(message)` function that detects thread context
- Script name is retrieved from state module for identification
- Format depends on whether code is running on main thread or background thread:
  - Main thread: `print(f"[{timestamp}] {message}")`
  - Background thread: `print(f"[{timestamp}] [{script_name}] {message}")`
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
- Common modules implementation: `3.4.4` → `3.5.0` (MAJOR for architecture change)
- Bug fix during testing: `3.5.0` → `3.5.1` (PATCH for iteration)
- Another iteration: `3.5.1` → `3.5.2` (PATCH for iteration)
- New feature addition: `3.5.2` → `3.6.0` (MINOR for new feature)

## Development Workflow & Feature Branch Updates

### IMMEDIATE FEATURE BRANCH APPLICATION
**IMPORTANT**: When working on a feature branch, Claude should **immediately apply changes** to that branch after outputting code. This ensures:
- The feature branch stays up-to-date with all iterations
- Testing can be done against the latest code
- No manual copying of changes is required

### Feature Branch Workflow
1. **Implementation**: Claude outputs the code changes (main script and/or modules)
2. **Version Update**: Claude **MUST** increment `SCRIPT_VERSION` in `config.py` with every code output
3. **Immediate Application**: Claude immediately commits changes to the active feature branch
4. **User Testing**: User tests the updated code from the feature branch
5. **Iteration**: Based on test results, Claude makes fixes and immediately applies them
6. **Pull Request**: Once feature is complete and tested, create PR to merge into main

### Testing During Development
While working on a feature branch:
- Changes are applied immediately after each iteration
- User pulls latest changes from feature branch to test
- Logs should show incrementing version numbers with each test
- Quick iteration cycle without manual file management

### Log Requirements
Users should provide logs showing:
```
[ytplay.py] [timestamp] Script version X.Y.Z loaded
[ytplay.py] [timestamp] [Feature-specific success messages]
[ytplay.py] [timestamp] [No critical errors]
```

### Final PR Requirements
Before merging feature branch to main:
- [ ] All tests pass
- [ ] Feature works as expected
- [ ] No regressions
- [ ] Clean commit history
- [ ] PR description includes test results

## Module Development Guidelines
- Avoid circular imports by importing at function level when necessary
- All configuration constants go in `config.py`
- All shared state goes through `state.py` with thread-safe accessors
- Heavy processing happens in background threads
- OBS API calls only on main thread
- Each module should have clear docstring explaining its purpose
- Modules must handle script identification through state module

## Multi-Instance Support
- Multiple scripts can run simultaneously sharing the same modules
- Each script maintains its own:
  - Scene name (matching script filename)
  - Cache directory
  - Configuration and state
  - Log identification
- Example setup:
  ```
  ytplay.py       → Scene: ytplay
  yt_worship.py   → Scene: yt_worship
  yt_ambient.py   → Scene: yt_ambient
  ```

## Testing Version
Users should always check the OBS logs to verify the correct version is loaded:
```
[ytplay.py] [timestamp] Script version X.Y.Z loaded
```

## Development Workflow - Branches and Pull Requests

### Branch-Based Development
All changes to the codebase **MUST** be made through feature branches and pull requests:

1. **Create Feature Branch**: 
   - Branch from `main` for each new feature or fix
   - Use descriptive branch names: `feature/common-modules`, `fix/metadata-parsing`, `refactor/state-management`

2. **Develop and Test**:
   - Make changes in the feature branch
   - **Claude applies changes immediately to the branch**
   - Test directly from the feature branch
   - Iterate quickly with immediate updates

3. **Create Pull Request**:
   - Once feature is complete and tested
   - Create a PR with clear description of changes
   - Include testing results and logs in PR description
   - Reference any related issues

4. **Review and Merge**:
   - Review code changes
   - Verify testing was completed
   - Merge only after approval

### Benefits of PR Workflow
- **Code Review**: All changes are reviewed before merging
- **History**: Clear record of what changed and why
- **Rollback**: Easy to revert changes if issues arise
- **Collaboration**: Multiple people can work on different features
- **CI/CD**: Can add automated testing in the future

### Example Workflow
```bash
# Working on feature branch
git checkout feature/common-modules-redesign

# Claude makes changes, they are immediately committed
# User pulls and tests

# After testing and approval, create PR on GitHub
```

## Commit Messages
Use clear, descriptive commit messages that explain what changed and why. For feature branches, commits can be more granular during development. The final merge commit should summarize all changes in the PR.

Always reconcile implementations with **02‑Requirements.md** and respect environment rules in **03‑OBS_API.md**.

*Prev → 03‑OBS_API.md | Next → ../phases/Phase-01-Scaffolding.md*