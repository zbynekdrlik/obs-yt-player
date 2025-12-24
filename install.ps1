#Requires -Version 5.1
<#
.SYNOPSIS
    OBS YouTube Player Installer
.DESCRIPTION
    Downloads and installs OBS YouTube Player to your OBS Studio installation.
    Supports both system-installed and portable OBS.
    Can automatically configure OBS via WebSocket if OBS is running.
.EXAMPLE
    irm https://raw.githubusercontent.com/zbynekdrlik/obs-yt-player/main/install.ps1 | iex
.NOTES
    Author: OBS YouTube Player Team
    Repository: https://github.com/zbynekdrlik/obs-yt-player
#>

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # Faster downloads

# Configuration
$InstallerVersion = "1.1.0"
$InstallerCommit = "dc0b1a7"  # Update on each commit
$RepoOwner = "zbynekdrlik"
$RepoName = "obs-yt-player"
$ScriptFolder = "yt-player-main"
$DefaultInstanceName = "ytplay"
$script:InstanceName = "ytplay"  # Will be set by user
$OBSWebSocketPort = 4455
$DefaultInstallDir = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "OBS-YouTube-Player"

# Global WebSocket state
$script:wsConnection = $null
$script:wsMessageId = 0
$script:wsPassword = ""

function Write-Header {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  OBS YouTube Player Installer" -ForegroundColor Cyan
    Write-Host "  v$InstallerVersion ($InstallerCommit)" -ForegroundColor DarkCyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "[+] $Message" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message" -ForegroundColor Gray
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[~] $Message" -ForegroundColor DarkYellow
}

#region OBS Detection Functions

function Test-PortableOBS {
    param([string]$Path)

    $obsExePaths = @(
        (Join-Path $Path "bin\64bit\obs64.exe"),
        (Join-Path $Path "bin\32bit\obs32.exe"),
        (Join-Path $Path "obs64.exe")
    )

    foreach ($exePath in $obsExePaths) {
        if (Test-Path $exePath) {
            $dataPath = Join-Path $Path "data"
            if (Test-Path $dataPath) {
                return $true
            }
        }
    }
    return $false
}

function Find-SystemOBS {
    $systemPaths = @(
        "${env:ProgramFiles}\obs-studio",
        "${env:ProgramFiles(x86)}\obs-studio",
        "$env:LOCALAPPDATA\Programs\obs-studio"
    )

    foreach ($path in $systemPaths) {
        if (Test-Path $path) {
            $obsExe = Join-Path $path "bin\64bit\obs64.exe"
            if (Test-Path $obsExe) {
                return $path
            }
        }
    }
    return $null
}

function Get-InstallDirectory {
    param(
        [string]$OBSPath,
        [bool]$IsPortable
    )

    if ($IsPortable) {
        # Portable OBS: Install inside OBS folder for easy transfer/backup
        return Join-Path $OBSPath "scripts\OBS-YouTube-Player"
    } else {
        # System OBS: Install to Documents
        return $DefaultInstallDir
    }
}

function Get-OBSConfigDirectory {
    param(
        [string]$OBSPath,
        [bool]$IsPortable
    )

    if ($IsPortable) {
        return Join-Path $OBSPath "config\obs-studio"
    } else {
        return Join-Path $env:APPDATA "obs-studio"
    }
}

function Request-InstanceName {
    Write-Host ""
    Write-Host "Instance name determines your scene name in OBS." -ForegroundColor Gray
    Write-Host "Examples: ytplay, worship, music, ambient" -ForegroundColor Gray
    Write-Host ""

    $name = Read-Host "Instance name [$DefaultInstanceName]"

    if ([string]::IsNullOrWhiteSpace($name)) {
        $name = $DefaultInstanceName
    }

    # Validate name (alphanumeric, underscore, hyphen only)
    if ($name -notmatch '^[a-zA-Z][a-zA-Z0-9_-]*$') {
        Write-ErrorMsg "Invalid name. Use only letters, numbers, underscore, hyphen. Must start with letter."
        return Request-InstanceName
    }

    return $name.ToLower()
}

function Rename-InstanceFiles {
    param(
        [string]$InstancePath,
        [string]$NewName
    )

    # Skip if using default name
    if ($NewName -eq "ytplay") {
        return $true
    }

    try {
        Write-Step "Renaming instance files to '$NewName'..."

        # Rename main script: ytplay.py -> {name}.py
        $oldScript = Join-Path $InstancePath "ytplay.py"
        $newScript = Join-Path $InstancePath "$NewName.py"
        if (Test-Path $oldScript) {
            Move-Item -Path $oldScript -Destination $newScript -Force
        }

        # Rename modules directory: ytplay_modules -> {name}_modules
        $oldModules = Join-Path $InstancePath "ytplay_modules"
        $newModules = Join-Path $InstancePath "${NewName}_modules"
        if (Test-Path $oldModules) {
            Move-Item -Path $oldModules -Destination $newModules -Force
        }

        Write-Success "Instance renamed to '$NewName'"
        return $true
    } catch {
        Write-Warning "Could not rename instance: $_"
        return $false
    }
}

function Get-ExistingInstances {
    param([string]$InstallDir)

    $instances = @()
    if (Test-Path $InstallDir) {
        Get-ChildItem -Path $InstallDir -Directory -Filter "yt-player-*" | ForEach-Object {
            $name = $_.Name -replace '^yt-player-', ''
            $version = Get-InstalledVersion -InstancePath $_.FullName
            $instances += @{
                Name = $name
                Path = $_.FullName
                Version = $version
            }
        }
    }
    return $instances
}

function Show-ExistingInstances {
    param(
        [array]$Instances,
        [string]$LatestVersion
    )

    if ($Instances.Count -eq 0) {
        return
    }

    Write-Host ""
    Write-Host "Existing instances:" -ForegroundColor Cyan

    foreach ($inst in $Instances) {
        $name = $inst.Name
        $version = if ($inst.Version) { $inst.Version } else { "unknown" }

        Write-Host "  - " -NoNewline
        Write-Host "$name" -ForegroundColor White -NoNewline
        Write-Host " (v$version)" -ForegroundColor Gray -NoNewline

        # Show update indicator if newer version available
        if ($LatestVersion -and $inst.Version -and $inst.Version -ne $LatestVersion) {
            if ($inst.Version -notmatch "^main-") {
                Write-Host " -> " -NoNewline -ForegroundColor DarkGray
                Write-Host "$LatestVersion available" -ForegroundColor Yellow -NoNewline
            }
        }
        Write-Host ""
    }
}

#endregion

#region OBS WebSocket Functions

function Test-OBSRunning {
    $obsProcess = Get-Process -Name "obs64", "obs32" -ErrorAction SilentlyContinue
    return $null -ne $obsProcess
}

function Connect-OBSWebSocket {
    param(
        [string]$Password = ""
    )

    try {
        $uri = "ws://127.0.0.1:$OBSWebSocketPort"

        $clientWebSocket = New-Object System.Net.WebSockets.ClientWebSocket
        $cts = New-Object System.Threading.CancellationTokenSource
        $cts.CancelAfter(5000)  # 5 second timeout

        $connectTask = $clientWebSocket.ConnectAsync($uri, $cts.Token)
        $connectTask.Wait()

        if ($clientWebSocket.State -ne [System.Net.WebSockets.WebSocketState]::Open) {
            return $null
        }

        # Receive Hello message
        $hello = Receive-WebSocketMessage -WebSocket $clientWebSocket -Timeout 5000
        if (-not $hello -or $hello.op -ne 0) {
            $clientWebSocket.Dispose()
            return $null
        }

        # Prepare Identify message
        $identifyData = @{
            rpcVersion = 1
        }

        # Handle authentication if required
        if ($hello.d.authentication) {
            if ([string]::IsNullOrEmpty($Password)) {
                Write-Warning "OBS WebSocket requires a password"
                $Password = Read-Host "Enter OBS WebSocket password"
            }

            $challenge = $hello.d.authentication.challenge
            $salt = $hello.d.authentication.salt

            # Generate authentication string
            $authString = Get-OBSAuthString -Password $Password -Salt $salt -Challenge $challenge
            $identifyData.authentication = $authString
        }

        # Send Identify
        $identifyMsg = @{
            op = 1
            d = $identifyData
        } | ConvertTo-Json -Compress

        Send-WebSocketMessage -WebSocket $clientWebSocket -Message $identifyMsg

        # Receive Identified response
        $identified = Receive-WebSocketMessage -WebSocket $clientWebSocket -Timeout 5000
        if (-not $identified -or $identified.op -ne 2) {
            Write-ErrorMsg "OBS WebSocket authentication failed"
            $clientWebSocket.Dispose()
            return $null
        }

        $script:wsConnection = $clientWebSocket
        return $clientWebSocket

    } catch {
        return $null
    }
}

function Get-OBSAuthString {
    param(
        [string]$Password,
        [string]$Salt,
        [string]$Challenge
    )

    $sha256 = [System.Security.Cryptography.SHA256]::Create()

    # base64(sha256(password + salt))
    $passAndSalt = $Password + $Salt
    $passSaltBytes = [System.Text.Encoding]::UTF8.GetBytes($passAndSalt)
    $passSaltHash = $sha256.ComputeHash($passSaltBytes)
    $passSaltBase64 = [Convert]::ToBase64String($passSaltHash)

    # base64(sha256(base64_secret + challenge))
    $secretAndChallenge = $passSaltBase64 + $Challenge
    $secretChallengeBytes = [System.Text.Encoding]::UTF8.GetBytes($secretAndChallenge)
    $finalHash = $sha256.ComputeHash($secretChallengeBytes)
    $finalBase64 = [Convert]::ToBase64String($finalHash)

    return $finalBase64
}

function Send-WebSocketMessage {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket,
        [string]$Message
    )

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Message)
    $segment = New-Object System.ArraySegment[byte] -ArgumentList @(,$bytes)
    $cts = New-Object System.Threading.CancellationTokenSource
    $cts.CancelAfter(5000)

    $sendTask = $WebSocket.SendAsync($segment, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $cts.Token)
    $sendTask.Wait()
}

function Receive-WebSocketMessage {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket,
        [int]$Timeout = 5000
    )

    try {
        $buffer = New-Object byte[] 65536
        $segment = New-Object System.ArraySegment[byte] -ArgumentList @(,$buffer)
        $cts = New-Object System.Threading.CancellationTokenSource
        $cts.CancelAfter($Timeout)

        $result = $WebSocket.ReceiveAsync($segment, $cts.Token)
        $result.Wait()

        if ($result.Result.MessageType -eq [System.Net.WebSockets.WebSocketMessageType]::Text) {
            $message = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $result.Result.Count)
            return $message | ConvertFrom-Json
        }
    } catch {
        return $null
    }
    return $null
}

function Send-OBSRequest {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket,
        [string]$RequestType,
        [hashtable]$RequestData = @{}
    )

    $script:wsMessageId++
    $requestId = "installer_$($script:wsMessageId)"

    $request = @{
        op = 6
        d = @{
            requestType = $RequestType
            requestId = $requestId
            requestData = $RequestData
        }
    } | ConvertTo-Json -Depth 10 -Compress

    Send-WebSocketMessage -WebSocket $WebSocket -Message $request
    $response = Receive-WebSocketMessage -WebSocket $WebSocket -Timeout 10000

    if ($response -and $response.op -eq 7 -and $response.d.requestId -eq $requestId) {
        return $response.d
    }
    return $null
}

function Close-OBSWebSocket {
    if ($script:wsConnection) {
        try {
            $cts = New-Object System.Threading.CancellationTokenSource
            $cts.CancelAfter(2000)
            $closeTask = $script:wsConnection.CloseAsync(
                [System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure,
                "Installer complete",
                $cts.Token
            )
            $closeTask.Wait()
        } catch { }
        $script:wsConnection.Dispose()
        $script:wsConnection = $null
    }
}

#endregion

#region OBS Configuration Functions

function Enable-OBSWebSocket {
    param(
        [string]$OBSPath,
        [bool]$IsPortable
    )

    try {
        # Determine config path
        if ($IsPortable) {
            $configDir = Join-Path $OBSPath "config\obs-studio\plugin_config\obs-websocket"
        } else {
            $configDir = Join-Path $env:APPDATA "obs-studio\plugin_config\obs-websocket"
        }

        $configFile = Join-Path $configDir "config.json"

        # Read existing config or create new
        $config = $null
        $existingAuth = $false

        if (Test-Path $configFile) {
            try {
                $config = Get-Content $configFile -Raw | ConvertFrom-Json
                # Check if auth is configured
                if ($config.auth_required -eq $true) {
                    $existingAuth = $true
                }
            } catch {
                $config = $null
            }
        }

        # Create directory if needed
        if (-not (Test-Path $configDir)) {
            New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        }

        if ($null -eq $config) {
            # No existing config - create fresh with no auth
            $config = @{
                server_enabled = $true
                server_port = 4455
                alerts_enabled = $false
                auth_required = $false
            }
            $config | ConvertTo-Json -Depth 10 | Set-Content $configFile -Encoding UTF8
            Write-Info "Created new WebSocket config (no authentication)"
        } elseif ($config.server_enabled -ne $true) {
            # Only enable server, preserve other settings
            $config | Add-Member -NotePropertyName "server_enabled" -NotePropertyValue $true -Force
            $config | ConvertTo-Json -Depth 10 | Set-Content $configFile -Encoding UTF8
            Write-Info "Enabled WebSocket server (preserved existing settings)"
        } else {
            Write-Info "WebSocket already enabled"
        }

        # Return whether auth is required (so we can prompt for password)
        return @{
            Success = $true
            AuthRequired = $existingAuth
        }
    } catch {
        Write-Warning "Could not configure WebSocket: $_"
        return @{
            Success = $false
            AuthRequired = $false
        }
    }
}

function Disable-OBSWebSocketAuth {
    param(
        [string]$OBSPath,
        [bool]$IsPortable
    )

    try {
        if ($IsPortable) {
            $configDir = Join-Path $OBSPath "config\obs-studio\plugin_config\obs-websocket"
        } else {
            $configDir = Join-Path $env:APPDATA "obs-studio\plugin_config\obs-websocket"
        }

        $configFile = Join-Path $configDir "config.json"

        if (Test-Path $configFile) {
            $config = Get-Content $configFile -Raw | ConvertFrom-Json
            $config | Add-Member -NotePropertyName "auth_required" -NotePropertyValue $false -Force
            $config | Add-Member -NotePropertyName "server_password" -NotePropertyValue "" -Force
            $config | ConvertTo-Json -Depth 10 | Set-Content $configFile -Encoding UTF8
            return $true
        }
        return $false
    } catch {
        Write-Warning "Could not disable authentication: $_"
        return $false
    }
}

function New-OBSScene {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket,
        [string]$SceneName
    )

    # Check if scene exists
    $scenes = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetSceneList"
    if ($scenes.requestStatus.result) {
        $existingScene = $scenes.responseData.scenes | Where-Object { $_.sceneName -eq $SceneName }
        if ($existingScene) {
            Write-Info "Scene '$SceneName' already exists"
            return $true
        }
    }

    # Create scene
    $result = Send-OBSRequest -WebSocket $WebSocket -RequestType "CreateScene" -RequestData @{
        sceneName = $SceneName
    }

    return $result.requestStatus.result
}

function New-OBSMediaSource {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket,
        [string]$SceneName,
        [string]$SourceName
    )

    # Check if source exists
    $items = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetSceneItemList" -RequestData @{
        sceneName = $SceneName
    }

    if ($items.requestStatus.result) {
        $existingSource = $items.responseData.sceneItems | Where-Object { $_.sourceName -eq $SourceName }
        if ($existingSource) {
            Write-Info "Source '$SourceName' already exists"
            return $true
        }
    }

    # Create media source
    $result = Send-OBSRequest -WebSocket $WebSocket -RequestType "CreateInput" -RequestData @{
        sceneName = $SceneName
        inputName = $SourceName
        inputKind = "ffmpeg_source"
        inputSettings = @{
            local_file = ""
            is_local_file = $false
            looping = $false
            restart_on_activate = $false
        }
    }

    return $result.requestStatus.result
}

function New-OBSTextSource {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket,
        [string]$SceneName,
        [string]$SourceName
    )

    # Check if source exists
    $items = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetSceneItemList" -RequestData @{
        sceneName = $SceneName
    }

    if ($items.requestStatus.result) {
        $existingSource = $items.responseData.sceneItems | Where-Object { $_.sourceName -eq $SourceName }
        if ($existingSource) {
            Write-Info "Source '$SourceName' already exists"
            return $true
        }
    }

    # Create text source (GDI+ on Windows) with simple settings
    # Note: Font settings use a specific format in OBS
    $result = Send-OBSRequest -WebSocket $WebSocket -RequestType "CreateInput" -RequestData @{
        sceneName = $SceneName
        inputName = $SourceName
        inputKind = "text_gdiplus_v2"
        inputSettings = @{
            text = ""
        }
    }

    if (-not $result.requestStatus.result) {
        Write-Warning "Text source creation failed: $($result.requestStatus.comment)"
    }

    return $result.requestStatus.result
}

#endregion

#region Download Functions

function Get-LatestRelease {
    Write-Step "Fetching latest release information..."

    $apiUrl = "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"

    try {
        $release = Invoke-RestMethod -Uri $apiUrl -Headers @{
            "Accept" = "application/vnd.github.v3+json"
            "User-Agent" = "OBS-YouTube-Player-Installer"
        }
        return $release
    } catch {
        Write-Info "No releases found, will download from main branch"
        return $null
    }
}

function Get-InstalledVersion {
    param([string]$InstancePath)

    $versionFile = Join-Path $InstancePath "VERSION"
    if (Test-Path $versionFile) {
        return (Get-Content $versionFile -Raw).Trim()
    }
    return $null
}

function Write-VersionFile {
    param(
        [string]$InstancePath,
        [string]$Version
    )

    $versionFile = Join-Path $InstancePath "VERSION"
    $Version | Set-Content -Path $versionFile -Encoding UTF8 -NoNewline
}

function Download-Repository {
    param(
        [string]$DestinationPath,
        [string]$InstanceName,
        $Release = $null
    )

    # Use passed release or fetch if not provided
    if (-not $Release) {
        $Release = Get-LatestRelease
    }

    $script:InstalledVersion = $null

    if ($Release) {
        $version = $Release.tag_name
        $script:InstalledVersion = $version
        Write-Host ""
        Write-Host "  Release version: " -NoNewline
        Write-Host "$version" -ForegroundColor Green
        Write-Host ""
        $downloadUrl = "https://github.com/$RepoOwner/$RepoName/archive/refs/tags/$version.zip"
        $extractFolder = "$RepoName-$($version.TrimStart('v'))"
    } else {
        $version = "main-$(Get-Date -Format 'yyyyMMdd')"
        $script:InstalledVersion = $version
        Write-Host ""
        Write-Host "  Development version: " -NoNewline
        Write-Host "$version" -ForegroundColor Yellow
        Write-Host ""
        $downloadUrl = "https://github.com/$RepoOwner/$RepoName/archive/refs/heads/main.zip"
        $extractFolder = "$RepoName-main"
    }

    Write-Step "Downloading..."

    $tempZip = Join-Path $env:TEMP "obs-yt-player-download.zip"
    $tempExtract = Join-Path $env:TEMP "obs-yt-player-extract"

    # Instance folder: yt-player-{name}
    $instanceFolder = "yt-player-$InstanceName"
    $finalDest = Join-Path $DestinationPath $instanceFolder

    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip -UseBasicParsing
        Write-Success "Download complete"

        Write-Step "Extracting files..."
        if (Test-Path $tempExtract) {
            Remove-Item $tempExtract -Recurse -Force
        }
        Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

        $sourcePath = Join-Path $tempExtract "$extractFolder\$ScriptFolder"
        if (-not (Test-Path $sourcePath)) {
            throw "Could not find $ScriptFolder in downloaded archive"
        }

        if (Test-Path $finalDest) {
            Write-Step "Updating existing installation..."
            # Preserve cache directory
            $cacheDir = Join-Path $finalDest "cache"
            $cacheBackup = Join-Path $env:TEMP "obs-yt-player-cache-backup"
            if (Test-Path $cacheDir) {
                Write-Info "Preserving cache directory..."
                if (Test-Path $cacheBackup) { Remove-Item $cacheBackup -Recurse -Force }
                Copy-Item -Path $cacheDir -Destination $cacheBackup -Recurse
            }
            Remove-Item $finalDest -Recurse -Force
        }

        # Copy template to instance folder
        Copy-Item -Path $sourcePath -Destination $finalDest -Recurse

        # Write VERSION file with installed version
        Write-VersionFile -InstancePath $finalDest -Version $script:InstalledVersion
        Write-Info "Version $($script:InstalledVersion) recorded"

        # Restore cache if backed up
        if (Test-Path $cacheBackup) {
            $newCacheDir = Join-Path $finalDest "cache"
            if (Test-Path $newCacheDir) { Remove-Item $newCacheDir -Recurse -Force }
            Move-Item -Path $cacheBackup -Destination $newCacheDir
            Write-Info "Cache restored"
        }

        Write-Success "Files installed to: $finalDest"

        return $finalDest

    } finally {
        if (Test-Path $tempZip) { Remove-Item $tempZip -Force }
        if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force }
    }
}

#endregion

#region User Prompts

function Confirm-Installation {
    param(
        [string]$Path,
        [string]$Type
    )

    Write-Host ""
    Write-Host "Detected " -NoNewline
    Write-Host "$Type OBS" -ForegroundColor Cyan -NoNewline
    Write-Host " at:"
    Write-Host "  $Path" -ForegroundColor Yellow
    Write-Host ""

    $response = Read-Host "Install OBS YouTube Player here? (Y/n)"
    return ($response -eq "" -or $response -ieq "y" -or $response -ieq "yes")
}

function Request-CustomPath {
    Write-Host ""
    Write-ErrorMsg "Could not detect OBS installation automatically."
    Write-Host ""
    Write-Host "Please enter the path to your OBS installation folder" -ForegroundColor White
    Write-Host "(e.g., C:\OBS-Studio-Portable or C:\Program Files\obs-studio):" -ForegroundColor Gray
    Write-Host ""

    $customPath = Read-Host "OBS Path"

    if ([string]::IsNullOrWhiteSpace($customPath)) {
        Write-ErrorMsg "No path provided. Installation cancelled."
        return $null
    }

    if (-not (Test-Path $customPath)) {
        Write-ErrorMsg "Path does not exist: $customPath"
        return $null
    }

    return $customPath
}

function Request-PlaylistURL {
    $defaultURL = "https://www.youtube.com/playlist?list=PLFdHTR758BvdEXF1tZ_3g8glRuev6EC6U"

    Write-Host ""
    Write-Host "Enter your YouTube playlist URL" -ForegroundColor White
    Write-Host "Default (press Enter): " -NoNewline -ForegroundColor Gray
    Write-Host $defaultURL -ForegroundColor DarkCyan
    Write-Host ""

    $url = Read-Host "Playlist URL"

    if ([string]::IsNullOrWhiteSpace($url)) {
        Write-Info "Using default playlist"
        return $defaultURL
    }
    return $url
}

#endregion

#region Post-Install

function Show-ManualInstructions {
    param(
        [string]$ScriptPath
    )

    Write-Host ""
    # Determine the script filename based on instance name
    $scriptFile = "$($script:InstanceName).py"
    $fullScriptPath = Join-Path $ScriptPath $scriptFile
    $instanceName = $script:InstanceName

    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  Manual Setup Required" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "OBS is not running or WebSocket is not available." -ForegroundColor White
    Write-Host "Please complete these steps manually:" -ForegroundColor White
    Write-Host ""
    Write-Host "1. " -NoNewline -ForegroundColor Cyan
    Write-Host "Open OBS Studio"
    Write-Host ""
    Write-Host "2. " -NoNewline -ForegroundColor Cyan
    Write-Host "Add the script:"
    Write-Host "   Tools -> Scripts -> Click '+' -> Select:" -ForegroundColor Gray
    Write-Host "   $fullScriptPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. " -NoNewline -ForegroundColor Cyan
    Write-Host "Create a scene named: " -NoNewline
    Write-Host "$instanceName" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "4. " -NoNewline -ForegroundColor Cyan
    Write-Host "Add sources to your scene:"
    Write-Host "   - Media Source: " -NoNewline -ForegroundColor Gray
    Write-Host "${instanceName}_video" -ForegroundColor Yellow
    Write-Host "     (uncheck 'Local File')" -ForegroundColor DarkGray
    Write-Host "   - Text Source:  " -NoNewline -ForegroundColor Gray
    Write-Host "${instanceName}_title" -ForegroundColor Yellow -NoNewline
    Write-Host " (optional)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "5. " -NoNewline -ForegroundColor Cyan
    Write-Host "Configure in script properties:"
    Write-Host "   - Set your YouTube Playlist URL" -ForegroundColor Gray
    Write-Host ""
}

function Show-SuccessMessage {
    param(
        [string]$ScriptPath,
        [bool]$AutoConfigured,
        [string]$PlaylistURL
    )

    # Determine the script filename based on instance name
    $scriptFile = "$($script:InstanceName).py"
    $fullScriptPath = Join-Path $ScriptPath $scriptFile

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Instance: " -NoNewline
    Write-Host "$($script:InstanceName)" -ForegroundColor Cyan
    Write-Host "Version:  " -NoNewline
    Write-Host "$($script:InstalledVersion)" -ForegroundColor Green
    Write-Host ""

    if ($AutoConfigured) {
        Write-Success "Scene '$($script:InstanceName)' created with sources"
        Write-Host ""
        Write-Host "Remaining step in OBS Studio:" -ForegroundColor White
        Write-Host ""
        Write-Host "1. " -NoNewline -ForegroundColor Cyan
        Write-Host "Add the script:"
        Write-Host "   Tools -> Scripts -> Click '+' -> Select:" -ForegroundColor Gray
        Write-Host "   $fullScriptPath" -ForegroundColor Yellow

        if (-not [string]::IsNullOrEmpty($PlaylistURL)) {
            Write-Host ""
            Write-Host "2. " -NoNewline -ForegroundColor Cyan
            Write-Host "Set playlist URL in script properties:" -ForegroundColor White
            Write-Host "   $PlaylistURL" -ForegroundColor Yellow
        } else {
            Write-Host ""
            Write-Host "2. " -NoNewline -ForegroundColor Cyan
            Write-Host "Configure playlist URL in script properties" -ForegroundColor White
        }
    } else {
        Show-ManualInstructions -ScriptPath $ScriptPath
    }

    Write-Host ""
    Write-Host "To add more instances, run installer again with different name." -ForegroundColor Gray
    Write-Host ""
    Write-Host "Documentation: " -NoNewline
    Write-Host "https://github.com/$RepoOwner/$RepoName#readme" -ForegroundColor Blue
    Write-Host ""
}

#endregion

#region Main Installation

function Install-OBSYouTubePlayer {
    Write-Header

    $currentDir = Get-Location
    $obsPath = $null
    $isPortable = $false

    # Step 1: Check if running in a portable OBS folder
    Write-Step "Checking current directory for portable OBS..."

    if (Test-PortableOBS $currentDir) {
        Write-Success "Found portable OBS in current directory"
        $isPortable = $true

        if (Confirm-Installation -Path $currentDir -Type "Portable") {
            $obsPath = $currentDir
        }
    }

    # Step 2: If not found or declined, check system installation
    if (-not $obsPath) {
        Write-Step "Checking for system OBS installation..."

        $systemOBS = Find-SystemOBS
        if ($systemOBS) {
            Write-Success "Found system OBS installation"

            if (Confirm-Installation -Path $systemOBS -Type "System") {
                $obsPath = $systemOBS
                $isPortable = $false
            }
        }
    }

    # Step 3: If still no path, ask for custom path
    if (-not $obsPath) {
        $customPath = Request-CustomPath
        if (-not $customPath) {
            return
        }

        $isPortable = Test-PortableOBS $customPath
        if (-not $isPortable) {
            Write-Info "Treating as system-style installation"
        }

        $obsPath = $customPath
    }

    # Step 4: Determine install directory
    # - Portable OBS: Inside OBS folder (scripts\OBS-YouTube-Player)
    # - System OBS: Documents\OBS-YouTube-Player
    $installDir = Get-InstallDirectory -OBSPath $obsPath -IsPortable $isPortable

    Write-Step "Install location:"
    if ($isPortable) {
        Write-Info "$installDir (inside portable OBS)"
    } else {
        Write-Info "$installDir (Documents folder)"
    }

    # Check for latest release version first
    Write-Step "Checking for latest version..."
    $release = Get-LatestRelease
    $latestVersion = if ($release) { $release.tag_name } else { $null }

    # Show existing instances with version info
    $existingInstances = Get-ExistingInstances -InstallDir $installDir
    Show-ExistingInstances -Instances $existingInstances -LatestVersion $latestVersion

    # Step 5: Get instance name
    $script:InstanceName = Request-InstanceName

    # Check if instance already exists
    $instancePath = Join-Path $installDir "yt-player-$($script:InstanceName)"
    if (Test-Path $instancePath) {
        $existingVersion = Get-InstalledVersion -InstancePath $instancePath
        Write-Warning "Instance '$($script:InstanceName)' already exists"

        if ($existingVersion) {
            Write-Host "  Current version: " -NoNewline
            Write-Host "$existingVersion" -ForegroundColor Gray

            if ($latestVersion -and $existingVersion -ne $latestVersion) {
                Write-Host "  Latest version:  " -NoNewline
                Write-Host "$latestVersion" -ForegroundColor Green
            }
        }

        Write-Host ""
        $update = Read-Host "Update this instance? (Y/n)"
        if ($update -ine "" -and $update -ine "y" -and $update -ine "yes") {
            Write-Info "Installation cancelled"
            return
        }
    }

    Write-Host ""
    Write-Step "Scripts will be installed to:"
    Write-Info $instancePath
    Write-Host ""

    if (-not (Test-Path $installDir)) {
        Write-Step "Creating install directory..."
        New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    }

    # Step 6: Download and install files
    try {
        $installedPath = Download-Repository -DestinationPath $installDir -InstanceName $script:InstanceName -Release $release

        # Rename files if not using default name
        if ($script:InstanceName -ne "ytplay") {
            Rename-InstanceFiles -InstancePath $installedPath -NewName $script:InstanceName
        }
    } catch {
        Write-ErrorMsg "Installation failed: $_"
        return
    }

    # Step 7: Ask for playlist URL
    $playlistURL = Request-PlaylistURL

    # Step 8: Try to configure OBS via WebSocket
    $autoConfigured = $false

    Write-Host ""
    Write-Step "Checking if OBS is running..."

    $obsRunning = Test-OBSRunning

    if (-not $obsRunning) {
        Write-Info "OBS is not running"
        Write-Host ""
        $startOBS = Read-Host "Start OBS now to auto-configure scene/sources? (Y/n)"

        if ($startOBS -eq "" -or $startOBS -ieq "y" -or $startOBS -ieq "yes") {
            # Enable WebSocket in OBS config before starting
            Write-Step "Configuring OBS WebSocket..."
            $wsConfig = Enable-OBSWebSocket -OBSPath $obsPath -IsPortable $isPortable

            if ($wsConfig.Success) {
                Write-Success "WebSocket configuration ready"

                # If auth is required, offer to disable or enter password
                if ($wsConfig.AuthRequired) {
                    Write-Warning "WebSocket authentication is enabled"
                    Write-Host ""
                    Write-Host "Options:" -ForegroundColor White
                    Write-Host "  1. Enter your WebSocket password" -ForegroundColor Gray
                    Write-Host "  2. Disable authentication (recommended for local use)" -ForegroundColor Gray
                    Write-Host ""
                    $authChoice = Read-Host "Choose (1 or 2)"

                    if ($authChoice -eq "2") {
                        # Disable authentication
                        $disableResult = Disable-OBSWebSocketAuth -OBSPath $obsPath -IsPortable $isPortable
                        if ($disableResult) {
                            Write-Success "Authentication disabled"
                        }
                    } else {
                        $script:wsPassword = Read-Host "Enter your OBS WebSocket password"
                    }
                }
            }

            Write-Step "Starting OBS Studio..."

            # Find OBS executable
            $obsExe = Join-Path $obsPath "bin\64bit\obs64.exe"
            if (-not (Test-Path $obsExe)) {
                $obsExe = Join-Path $obsPath "bin\32bit\obs32.exe"
            }

            if (Test-Path $obsExe) {
                # Start OBS from its own directory (required for locale files)
                $obsDir = Split-Path -Parent $obsExe
                Start-Process -FilePath $obsExe -WorkingDirectory $obsDir
                Write-Info "Waiting for OBS to start (up to 30 seconds)..."

                # Wait for OBS to start (up to 30 seconds)
                $waitTime = 0
                while (-not (Test-OBSRunning) -and $waitTime -lt 30) {
                    Start-Sleep -Seconds 2
                    $waitTime += 2
                    Write-Host "." -NoNewline
                }
                Write-Host ""

                if (Test-OBSRunning) {
                    Write-Success "OBS started successfully"
                    # Give OBS time to fully initialize WebSocket server
                    Write-Info "Waiting 8 seconds for WebSocket to initialize..."
                    Start-Sleep -Seconds 8

                    # Check again - OBS might have crashed
                    if (Test-OBSRunning) {
                        $obsRunning = $true
                    } else {
                        Write-Warning "OBS closed unexpectedly (check for errors in OBS)"
                    }
                } else {
                    Write-Warning "OBS did not start within 30 seconds"
                }
            } else {
                Write-Warning "Could not find OBS executable at: $obsExe"
            }
        }
    } else {
        $obsRunning = $true
    }

    if ($obsRunning -and (Test-OBSRunning)) {
        Write-Step "Connecting to OBS WebSocket..."

        # Use saved password if available
        $ws = Connect-OBSWebSocket -Password $script:wsPassword

        if ($ws) {
            Write-Success "Connected to OBS WebSocket"
            Write-Step "Creating scene and sources..."

            try {
                $instName = $script:InstanceName

                # Create scene
                if (New-OBSScene -WebSocket $ws -SceneName $instName) {
                    Write-Success "Scene '$instName' ready"
                }

                # Create media source
                if (New-OBSMediaSource -WebSocket $ws -SceneName $instName -SourceName "${instName}_video") {
                    Write-Success "Media source '${instName}_video' ready"
                }

                # Create text source
                if (New-OBSTextSource -WebSocket $ws -SceneName $instName -SourceName "${instName}_title") {
                    Write-Success "Text source '${instName}_title' ready"
                }

                $autoConfigured = $true

            } catch {
                Write-Warning "Could not fully configure OBS: $_"
            } finally {
                Close-OBSWebSocket
            }
        } else {
            Write-Warning "Could not connect to OBS WebSocket"
            Write-Info "Make sure WebSocket is enabled: Tools -> WebSocket Server Settings"
            Write-Info "OBS 28+ has WebSocket built-in, older versions need obs-websocket plugin"
        }
    } else {
        Write-Info "OBS is not running"
    }

    # Step 8: Show completion message
    Show-SuccessMessage -ScriptPath $installedPath -AutoConfigured $autoConfigured -PlaylistURL $playlistURL
}

# Run the installer
Install-OBSYouTubePlayer

#endregion
