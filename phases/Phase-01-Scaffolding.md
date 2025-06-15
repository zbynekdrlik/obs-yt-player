# Phase 01 – Scaffolding & Project Skeleton

## Goal
Create the initial `ytfast.py` OBS script skeleton **only**. It should:

- Define module‑level constants (see 02‑Requirements.md §Constants).
- Declare global variables (e.g. queues, locks, flags) but **do not** implement worker logic yet.
- Set up OBS script properties: Playlist URL text field, Cache Directory path field, *Sync Now* button, DEBUG level checkbox.
- Add minimal stubs for: `script_properties`, `script_load`, `script_description`, and placeholder worker thread starters.
- Include placeholder logging helper `log(msg, level="NORMAL")`.

## Requirements Reference
This phase sets up the foundation for all requirements in `02-requirements.md`.

## Key Implementation Points
- Follow output rules from `04-guidelines.md` (single Python file, ≤400 char docstring)
- Respect OBS constraints from `03-obs_api.md` (main thread awareness)
- Set up proper threading infrastructure with locks and queues

## Testing Before Commit
1. Load script in OBS Scripts menu
2. Verify all properties appear correctly (URL, cache dir, sync button, debug checkbox)
3. Check that script loads without errors
4. Verify scene check runs after 3 seconds
5. Ensure default values are set correctly
6. Check log output shows proper timestamps and levels

## Commit
After successful testing, commit with message:  
> *"Initial scaffolding: OBS properties & basic structure."*

*After verification, proceed to Phase 02.*