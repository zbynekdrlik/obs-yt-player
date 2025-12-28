# Windows Remote Testing Guide

This document describes how to test the OBS YouTube Player installer on remote Windows machines via SSH.

## Prerequisites

- SSH access to Windows machine with OpenSSH server
- `sshpass` installed on Linux for non-interactive SSH
- Target machine credentials in `TARGETS.md`

## Connection Pattern

```bash
# Basic connection with password
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no USER@IP "command"

# Copy files to Windows
sshpass -p 'PASSWORD' scp -o StrictHostKeyChecking=no localfile USER@IP:"c:/path/to/dest"
```

## Running PowerShell Commands

### Simple Commands
```bash
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -Command "Get-Process"'
```

### Complex Commands (use script files)
For complex PowerShell with special characters, escaping becomes problematic. Instead:

1. Write script to local file
2. Copy to Windows
3. Execute via PowerShell

```bash
# Write script locally
cat > /tmp/script.ps1 << 'EOF'
# PowerShell code here
Write-Host "Hello"
EOF

# Copy and execute
sshpass -p 'PASSWORD' scp /tmp/script.ps1 USER@IP:"c:/Users/USER/Desktop/script.ps1"
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -ExecutionPolicy Bypass -File c:\Users\USER\Desktop\script.ps1'
```

## Starting GUI Applications (OBS)

GUI apps started via SSH run in session 0 (invisible). Use Task Scheduler with `/IT` flag:

### Method 1: PowerShell Scheduled Task
```bash
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -Command "
$action = New-ScheduledTaskAction -Execute \"c:\\path\\to\\app.exe\"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(5)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId \"USERNAME\" -LogonType Interactive
Register-ScheduledTask -TaskName \"StartApp\" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
Start-ScheduledTask -TaskName \"StartApp\"
"'
```

### Method 2: Batch File + schtasks
```bash
# Create batch file
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -Command "
Set-Content -Path c:\\Users\\USER\\Desktop\\start_obs.bat -Value @\"
cd /d c:\\path\\to\\obs\\bin\\64bit
start \"\" obs64.exe -p
\"@ -Encoding ASCII
"'

# Create and run task (note: schtasks via SSH is tricky with escaping)
```

### Portable OBS
Always start with `-p` flag for portable mode:
```
obs64.exe -p
```

## OBS WebSocket Testing

### Check if WebSocket port is listening
```bash
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -Command "Test-NetConnection -ComputerName localhost -Port 4459 | Select-Object TcpTestSucceeded"'
```

### WebSocket Connection Script
See `/scripts/test_websocket.ps1` for a reusable WebSocket test script.

## Common Testing Workflow

### 1. Check OBS is running
```bash
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -Command "Get-Process obs64,cg -ErrorAction SilentlyContinue | Select-Object Name,Id"'
```

### 2. Kill OBS if needed
```bash
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -Command "Stop-Process -Name obs64,cg -Force -ErrorAction SilentlyContinue"'
```

### 3. Find OBS logs (portable)
```bash
sshpass -p 'PASSWORD' ssh USER@IP 'powershell -Command "Get-ChildItem \"c:\\path\\to\\obs\\config\\obs-studio\\logs\" | Sort-Object LastWriteTime -Descending | Select-Object -First 1"'
```

### 4. Read OBS logs
```bash
sshpass -p 'PASSWORD' ssh USER@IP "powershell -Command \"Get-Content 'c:\\path\\to\\log.txt' -Tail 50\""
```

### 5. Run installer non-interactively
Set environment variables before running:
```powershell
[Environment]::SetEnvironmentVariable("YTPLAY_AUTO_CONFIRM", "1", "Process")
[Environment]::SetEnvironmentVariable("YTPLAY_OBS_PATH", "c:\path\to\obs", "Process")
[Environment]::SetEnvironmentVariable("YTPLAY_PLAYLIST_URL", "1", "Process")
$env:YTPLAY_AUTO_CONFIRM = "1"
$env:YTPLAY_OBS_PATH = "c:\path\to\obs"
& c:\path\to\install.ps1
```

## Portable OBS Paths

| Component | Path |
|-----------|------|
| OBS executable | `{OBS_PATH}\bin\64bit\obs64.exe` (or renamed) |
| OBS config | `{OBS_PATH}\config\obs-studio\` |
| OBS logs | `{OBS_PATH}\config\obs-studio\logs\` |
| WebSocket config | `{OBS_PATH}\config\obs-studio\plugin_config\obs-websocket\config.json` |
| Scripts | `{OBS_PATH}\scripts\` |

## Troubleshooting

### PowerShell output not showing via SSH
- Use `Write-Output` instead of `Write-Host`
- Or write to a file and read it back

### WebSocket connection failing
1. Check port is listening: `Test-NetConnection`
2. Check OBS is running with WebSocket enabled
3. Check auth settings in WebSocket config

### Scheduled task not running
- Ensure user is logged in to desktop
- Use `/IT` flag for interactive session
- Check Task Scheduler history for errors

### Environment variables not passing
- Set both ways: `[Environment]::SetEnvironmentVariable()` AND `$env:VAR = "value"`
- For scheduled tasks, variables must be set in the script itself
