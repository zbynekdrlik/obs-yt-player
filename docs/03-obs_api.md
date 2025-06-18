# 03‑OBS_API (Environment & Constraints)

This file summarises key OBS scripting rules Claude **must** respect for Windows.

- OBS Python scripts run on the **main thread**; heavy work must move to background threads.
- Use `obs.timer_add` to schedule callbacks on the main thread from workers.
- Register `OBS_FRONTEND_EVENT_SCENE_CHANGED` to detect transitions; defer media switches until transition ends.
- Verify required scene (`ytfast`) exists 3 s after startup; log error if missing.
- Suppress console windows on Windows using `subprocess.STARTUPINFO` with hidden window flags.

## Windows-Specific Subprocess Handling

All subprocess calls must use:
```python
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = subprocess.SW_HIDE
```

For functional goals see **02‑Requirements.md**.  
For coding conventions see **04‑Guidelines.md**.

*Prev → 02‑Requirements.md | Next → 04‑Guidelines.md*