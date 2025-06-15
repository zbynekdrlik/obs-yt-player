# Phase 01 – Scaffolding & Project Skeleton

## Goal
Create the initial `ytfast.py` OBS script skeleton **only**. It should:

- Define module‑level constants (see 02‑Requirements.md §Constants).
- Declare global variables (e.g. queues, locks, flags) but **do not** implement worker logic yet.
- Set up OBS script properties: Playlist URL text field, Cache Directory path field, *Sync Now* button, DEBUG level checkbox.
- Add minimal stubs for: `script_properties`, `script_load`, `script_description`, and placeholder worker thread starters.
- Include placeholder logging helper `log(msg, level="NORMAL")`.

## Commit
When complete, suggest commit message:  
> *"Initial scaffolding: OBS properties & basic structure."*

*After verification, you will run Phase 02.*  
Remember to cross‑check constants and property defaults in **02‑Requirements.md** and follow style rules in **04‑Guidelines.md**.