# 01‑Overview

**Purpose**  
This project will generate an OBS Studio Python script (`ytfast.py`) that:

- Syncs a YouTube playlist and caches videos locally.
- Loudness‑normalises audio to −14 LUFS with FFmpeg.
- Plays videos randomly via a Media Source, updating a Text Source with metadata.
- Runs all heavy tasks in background threads so OBS stays responsive.

For detailed functional specifications see **02‑Requirements.md**.  
For OBS‑specific threading constraints see **03‑OBS_API.md**.  
For coding & output style rules see **04‑Guidelines.md**.  
Subsequent *Phase‑XX* files walk Claude through implementation step‑by‑step.

*Next → 02‑Requirements.md*
