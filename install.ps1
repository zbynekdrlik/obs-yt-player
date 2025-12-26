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
$ScriptVersion = "v4.3.0-dev.2"  # Set to "vX.Y.Z" for releases
$RepoOwner = "zbynekdrlik"
$RepoName = "obs-yt-player"
$RepoBranch = "main"  # Branch to download from (when no release)
$ScriptFolder = "yt-player-main"
$DefaultInstanceName = "ytplay"
$script:InstanceName = "ytplay"  # Will be set by user
$OBSWebSocketPort = 4455
$DefaultInstallDir = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "OBS-YouTube-Player"

# Global WebSocket state
$script:wsConnection = $null
$script:wsMessageId = 0
$script:wsPassword = ""
$script:DebugMode = $env:YTPLAY_DEBUG -eq "1"

function Write-Header {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  OBS YouTube Player Installer " -NoNewline -ForegroundColor Cyan
    if ($ScriptVersion -match "dev") {
        Write-Host "[$ScriptVersion]" -ForegroundColor Yellow
    } else {
        Write-Host "[$ScriptVersion]" -ForegroundColor Green
    }
    Write-Host "========================================" -ForegroundColor Cyan
    if ($script:DebugMode) {
        Write-Host "  [DEBUG MODE ENABLED]" -ForegroundColor Magenta
    }
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

function Write-Debug {
    param([string]$Message)
    if ($script:DebugMode) {
        Write-Host "[DEBUG] $Message" -ForegroundColor Magenta
    }
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
    # Use playlist name as default if available, otherwise use DefaultInstanceName
    $defaultName = if ($script:SelectedPlaylistName) { $script:SelectedPlaylistName } else { $DefaultInstanceName }

    Write-Host ""
    Write-Host "Instance name determines your scene name in OBS." -ForegroundColor Gray
    Write-Host ""

    $name = Read-Host "Instance name [$defaultName]"

    if ([string]::IsNullOrWhiteSpace($name)) {
        $name = $defaultName
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
        Write-Host "  - " -NoNewline
        Write-Host "$name" -ForegroundColor White
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

        $null = Send-WebSocketMessage -WebSocket $clientWebSocket -Message $identifyMsg

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

    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Message)
        $segment = New-Object System.ArraySegment[byte] -ArgumentList @(,$bytes)
        $cts = New-Object System.Threading.CancellationTokenSource
        $cts.CancelAfter(5000)

        $sendTask = $WebSocket.SendAsync($segment, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $cts.Token)
        $sendTask.Wait()
        return $true
    } catch {
        Write-Debug "Send-WebSocketMessage failed: $($_.Exception.Message)"
        return $false
    }
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

    # Check connection state
    if ($WebSocket.State -ne [System.Net.WebSockets.WebSocketState]::Open) {
        Write-Debug "WebSocket not open (state: $($WebSocket.State)), attempting reconnect..."
        $newWs = Connect-OBSWebSocket -Password $script:wsPassword
        if ($newWs) {
            $script:wsConnection = $newWs
            $WebSocket = $newWs
            Write-Debug "Reconnected successfully"
        } else {
            Write-Debug "Reconnect failed"
            return $null
        }
    }

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

    Write-Debug "Sending: $RequestType (state: $($WebSocket.State))"
    $sendResult = Send-WebSocketMessage -WebSocket $WebSocket -Message $request
    if (-not $sendResult) {
        Write-Debug "Send failed for: $RequestType"
        return $null
    }

    # Wait for response, skipping any events (OpCode 5) that arrive first
    $maxAttempts = 10  # Max messages to skip before giving up
    for ($attempt = 0; $attempt -lt $maxAttempts; $attempt++) {
        $response = Receive-WebSocketMessage -WebSocket $WebSocket -Timeout 5000

        if (-not $response) {
            Write-Debug "Response: $RequestType -> TIMEOUT (attempt $($attempt + 1))"
            continue
        }

        # Skip events (OpCode 5) - they arrive when OBS state changes
        if ($response.op -eq 5) {
            $eventType = $response.d.eventType
            Write-Debug "Skipping event: $eventType"
            continue
        }

        # Check for our response (OpCode 7)
        if ($response.op -eq 7 -and $response.d.requestId -eq $requestId) {
            $success = $response.d.requestStatus.result
            $code = $response.d.requestStatus.code
            Write-Debug "Response: $RequestType -> success=$success, code=$code"
            return $response.d
        }

        Write-Debug "Response: $RequestType -> unexpected op=$($response.op)"
    }

    Write-Debug "Response: $RequestType -> gave up after $maxAttempts attempts (state: $($WebSocket.State))"
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

    Write-Debug "New-OBSScene: Checking for scene '$SceneName'"

    # Check if scene exists
    $scenes = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetSceneList"
    if ($scenes -and $scenes.requestStatus.result) {
        $sceneNames = ($scenes.responseData.scenes | ForEach-Object { $_.sceneName }) -join ", "
        Write-Debug "New-OBSScene: Found scenes: $sceneNames"
        $existingScene = $scenes.responseData.scenes | Where-Object { $_.sceneName -eq $SceneName }
        if ($existingScene) {
            Write-Info "Scene '$SceneName' already exists"
            return $true
        }
    } elseif (-not $scenes) {
        # GetSceneList timed out - OBS might not be ready
        Write-Debug "New-OBSScene: GetSceneList returned null"
        return $false
    }

    # Try to create scene
    Write-Debug "New-OBSScene: Creating scene '$SceneName'"
    $result = Send-OBSRequest -WebSocket $WebSocket -RequestType "CreateScene" -RequestData @{
        sceneName = $SceneName
    }

    if (-not $result) {
        Write-Debug "New-OBSScene: CreateScene returned null"
        return $false
    }

    # Scene created successfully
    if ($result.requestStatus.result) {
        Write-Debug "New-OBSScene: Scene created successfully"
        return $true
    }

    # If creation failed because scene already exists (code 601), treat as success
    if ($result.requestStatus.code -eq 601) {
        Write-Info "Scene '$SceneName' already exists"
        return $true
    }

    Write-Debug "New-OBSScene: CreateScene failed with code $($result.requestStatus.code)"
    return $false
}

function New-OBSMediaSource {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket,
        [string]$SceneName,
        [string]$SourceName
    )

    # Check if source exists via GetInputList (more reliable than scene items)
    $inputs = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetInputList"
    if ($inputs -and $inputs.requestStatus.result) {
        $existingInput = $inputs.responseData.inputs | Where-Object { $_.inputName -eq $SourceName }
        if ($existingInput) {
            Write-Info "Source '$SourceName' already exists"
            return $true
        }
    }

    # Also check scene items as fallback
    $items = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetSceneItemList" -RequestData @{
        sceneName = $SceneName
    }

    if ($items -and $items.requestStatus.result) {
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
            is_local_file = $true  # CRITICAL: Must be true for local file playback
            looping = $false
            restart_on_activate = $true  # Restart video when scene becomes active
            hw_decode = $true  # Hardware decoding for better performance
            close_when_inactive = $true  # Release resources when not in use
        }
    }

    if ($null -eq $result) {
        Write-Warning "Media source creation failed: No response from OBS (timeout)"
        return $false
    }

    if (-not $result.requestStatus.result) {
        $errorMsg = if ($result.requestStatus.comment) { $result.requestStatus.comment } else { "Unknown error (code: $($result.requestStatus.code))" }
        Write-Warning "Media source creation failed: $errorMsg"
        return $false
    }

    return $true
}

function New-OBSTextSource {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket,
        [string]$SceneName,
        [string]$SourceName
    )

    # Check if source exists via GetInputList (more reliable than scene items)
    $inputs = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetInputList"
    if ($inputs -and $inputs.requestStatus.result) {
        $existingInput = $inputs.responseData.inputs | Where-Object { $_.inputName -eq $SourceName }
        if ($existingInput) {
            Write-Info "Source '$SourceName' already exists"
            return $true
        }
    }

    # Also check scene items as fallback
    $items = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetSceneItemList" -RequestData @{
        sceneName = $SceneName
    }

    if ($items -and $items.requestStatus.result) {
        $existingSource = $items.responseData.sceneItems | Where-Object { $_.sourceName -eq $SourceName }
        if ($existingSource) {
            Write-Info "Source '$SourceName' already exists"
            return $true
        }
    }

    # Query OBS for available input kinds and find a text source type
    $kindsResult = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetInputKindList" -RequestData @{
        unversioned = $false
    }

    $textKind = $null
    if ($kindsResult -and $kindsResult.requestStatus.result) {
        $kinds = $kindsResult.responseData.inputKinds
        # Look for text source types (prefer GDI+ on Windows, FreeType on others)
        $textPatterns = @("text_gdiplus", "text_ft2_source")
        foreach ($pattern in $textPatterns) {
            $match = $kinds | Where-Object { $_ -like "$pattern*" } | Select-Object -First 1
            if ($match) {
                $textKind = $match
                break
            }
        }
    }

    # Default text settings for reasonable appearance
    $defaultTextSettings = @{
        text = ""
        font = @{
            face = "Arial"
            size = 48
            style = "Regular"
            flags = 0
        }
        color = 16777215  # White (0xFFFFFF)
        outline = $true
        outline_color = 0  # Black
        outline_size = 2
    }

    # If kind detection failed, try common types directly
    if (-not $textKind) {
        $fallbackTypes = @("text_gdiplus_v2", "text_gdiplus_v3", "text_gdiplus", "text_ft2_source_v2", "text_ft2_source")
        foreach ($tryKind in $fallbackTypes) {
            $result = Send-OBSRequest -WebSocket $WebSocket -RequestType "CreateInput" -RequestData @{
                sceneName = $SceneName
                inputName = $SourceName
                inputKind = $tryKind
                inputSettings = $defaultTextSettings
            }
            if ($result -and $result.requestStatus.result) {
                return $true
            }
        }
        Write-Warning "Text source creation failed: No compatible text source type found"
        return $false
    }

    $result = Send-OBSRequest -WebSocket $WebSocket -RequestType "CreateInput" -RequestData @{
        sceneName = $SceneName
        inputName = $SourceName
        inputKind = $textKind
        inputSettings = $defaultTextSettings
    }

    if ($result -and $result.requestStatus.result) {
        return $true
    }

    $errorMsg = if ($result.requestStatus.comment) { $result.requestStatus.comment } else { "Unknown error" }
    Write-Warning "Text source creation failed: $errorMsg"
    return $false
}

function Set-OBSSourceTransform {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket,
        [string]$SceneName,
        [string]$SourceName,
        [hashtable]$Transform
    )

    # Get scene item ID
    $items = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetSceneItemList" -RequestData @{
        sceneName = $SceneName
    }

    if (-not $items -or -not $items.requestStatus.result) {
        return $false
    }

    $item = $items.responseData.sceneItems | Where-Object { $_.sourceName -eq $SourceName }
    if (-not $item) {
        return $false
    }

    $result = Send-OBSRequest -WebSocket $WebSocket -RequestType "SetSceneItemTransform" -RequestData @{
        sceneName = $SceneName
        sceneItemId = $item.sceneItemId
        sceneItemTransform = $Transform
    }

    return ($result -and $result.requestStatus.result)
}

function Get-OBSVideoSettings {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket
    )

    $result = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetVideoSettings"
    if ($result -and $result.requestStatus.result) {
        return @{
            Width = $result.responseData.baseWidth
            Height = $result.responseData.baseHeight
        }
    }
    return $null
}

function Get-OBSCurrentSceneCollection {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket
    )

    $result = Send-OBSRequest -WebSocket $WebSocket -RequestType "GetSceneCollectionList"
    if ($result -and $result.requestStatus.result) {
        return $result.responseData.currentSceneCollectionName
    }
    return $null
}

function Register-OBSScript {
    param(
        [string]$OBSPath,
        [bool]$IsPortable,
        [string]$ScriptPath,
        [string]$SceneCollectionName,
        [string]$PlaylistURL = ""
    )

    try {
        # Determine scenes directory
        if ($IsPortable) {
            $scenesDir = Join-Path $OBSPath "config\obs-studio\basic\scenes"
        } else {
            $scenesDir = Join-Path $env:APPDATA "obs-studio\basic\scenes"
        }

        # Find scene collection file
        $sceneFile = Join-Path $scenesDir "$SceneCollectionName.json"
        if (-not (Test-Path $sceneFile)) {
            Write-Warning "Scene collection file not found: $sceneFile"
            return $false
        }

        # Read and parse JSON
        $content = Get-Content $sceneFile -Raw -Encoding UTF8
        $sceneData = $content | ConvertFrom-Json

        # Check if modules array exists, create if not
        if (-not $sceneData.PSObject.Properties['modules']) {
            $sceneData | Add-Member -NotePropertyName "modules" -NotePropertyValue @{
                'scripts-tool' = @()
            } -Force
        } elseif (-not $sceneData.modules.PSObject.Properties['scripts-tool']) {
            $sceneData.modules | Add-Member -NotePropertyName "scripts-tool" -NotePropertyValue @() -Force
        }

        # Build script settings
        $scriptSettings = [PSCustomObject]@{}
        if (-not [string]::IsNullOrEmpty($PlaylistURL)) {
            $scriptSettings | Add-Member -NotePropertyName "playlist_url" -NotePropertyValue $PlaylistURL -Force
        }
        if (-not [string]::IsNullOrEmpty($script:GeminiApiKey)) {
            $scriptSettings | Add-Member -NotePropertyName "gemini_api_key" -NotePropertyValue $script:GeminiApiKey -Force
        }

        # Check if script already registered
        $scripts = @($sceneData.modules.'scripts-tool')
        $existingIndex = -1
        for ($i = 0; $i -lt $scripts.Count; $i++) {
            if ($scripts[$i].path -eq $ScriptPath) {
                $existingIndex = $i
                break
            }
        }

        if ($existingIndex -ge 0) {
            # Update existing script settings
            Write-Info "Updating script settings..."
            $scripts[$existingIndex].settings = $scriptSettings
        } else {
            # Add new script entry
            $scriptEntry = [PSCustomObject]@{
                path = $ScriptPath
                settings = $scriptSettings
            }
            $scripts += $scriptEntry
        }

        $sceneData.modules.'scripts-tool' = $scripts

        # Write back to file
        $sceneData | ConvertTo-Json -Depth 20 | Set-Content $sceneFile -Encoding UTF8

        return $true
    } catch {
        Write-Warning "Failed to register script: $_"
        return $false
    }
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
        Write-Host "  Installing: " -NoNewline
        Write-Host "$version" -ForegroundColor Green
        Write-Host ""
        $downloadUrl = "https://github.com/$RepoOwner/$RepoName/archive/refs/tags/$version.zip"
        $extractFolder = "$RepoName-$($version.TrimStart('v'))"
    } else {
        # Download from configured branch (development mode)
        $branchName = $RepoBranch -replace '/', '-'
        $version = "$branchName-$(Get-Date -Format 'yyyyMMdd')"
        $script:InstalledVersion = $version
        Write-Host ""
        Write-Host "  Installing: " -NoNewline
        Write-Host "$version (dev)" -ForegroundColor Yellow
        Write-Host ""
        $downloadUrl = "https://github.com/$RepoOwner/$RepoName/archive/refs/heads/$RepoBranch.zip"
        $extractFolder = "$RepoName-$branchName"
    }

    Write-Step "Downloading..."

    $tempZip = Join-Path $env:TEMP "obs-yt-player-download.zip"
    $tempExtract = Join-Path $env:TEMP "obs-yt-player-extract"

    # Instance folder: yt-player-{name}
    $instanceFolder = "yt-player-$InstanceName"
    $finalDest = Join-Path $DestinationPath $instanceFolder

    # Initialize cache backup path
    $cacheBackup = Join-Path $env:TEMP "obs-yt-player-cache-backup"
    $cacheWasBackedUp = $false

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

        $updateMode = $false
        if (Test-Path $finalDest) {
            $updateMode = $true
            Write-Step "Updating existing installation..."
            # Preserve cache directory
            $cacheDir = Join-Path $finalDest "cache"
            if (Test-Path $cacheDir) {
                Write-Info "Preserving cache directory..."
                if (Test-Path $cacheBackup) { Remove-Item $cacheBackup -Recurse -Force }
                Copy-Item -Path $cacheDir -Destination $cacheBackup -Recurse -ErrorAction SilentlyContinue
                $cacheWasBackedUp = $true
            }
            # Try to remove the old installation
            try {
                Remove-Item $finalDest -Recurse -Force -ErrorAction Stop
                $updateMode = $false  # Full removal succeeded, treat as fresh install
            } catch {
                # Some files may be locked (e.g., log files if OBS is running)
                Write-Warning "Some files are locked by OBS - will update in place..."
            }
        }

        # Copy/update files
        if ($updateMode) {
            # Copy over existing installation (locked files will be skipped but won't fail)
            Copy-Item -Path "$sourcePath\*" -Destination $finalDest -Recurse -Force
        } else {
            # Fresh install
            Copy-Item -Path $sourcePath -Destination $finalDest -Recurse
        }

        # Write VERSION file with installed version
        Write-VersionFile -InstancePath $finalDest -Version $script:InstalledVersion
        Write-Info "Version $($script:InstalledVersion) recorded"

        # Restore cache if backed up
        if ($cacheWasBackedUp -and (Test-Path $cacheBackup)) {
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

function Request-GeminiApiKey {
    Write-Host ""
    Write-Host "Gemini API key (optional, for better song/artist detection)" -ForegroundColor White
    Write-Host "Get free key at: " -NoNewline -ForegroundColor Gray
    Write-Host "https://makersuite.google.com/app/apikey" -ForegroundColor Blue
    Write-Host ""

    $key = Read-Host "Gemini API key (Enter to skip)"

    if ([string]::IsNullOrWhiteSpace($key)) {
        Write-Info "Skipping Gemini - will use basic title parsing"
        return $null
    }

    Write-Success "Gemini API key configured"
    return $key
}

function Request-PlaylistURL {
    # Predefined playlists
    $playlists = @(
        @{ Name = "ytfast"; Desc = "Fast/upbeat music"; URL = "https://www.youtube.com/watch?v=9vpwt0LdFhs&list=PLFdHTR758BvdEXF1tZ_3g8glRuev6EC6U" }
        @{ Name = "ytslow"; Desc = "Slow/calm music"; URL = "https://www.youtube.com/watch?v=iWuqiILKtgc&list=PLFdHTR758Bvd9c7dKV-ZZFQ1jg30ahHFq" }
        @{ Name = "yt90s"; Desc = "90s hits"; URL = "https://www.youtube.com/watch?v=r1_MOB2kJ_U&list=PLFdHTR758BvfM0XYF6Q2nEDnW0CqHXI17" }
        @{ Name = "ytwarmup"; Desc = "Warmup music"; URL = "https://www.youtube.com/watch?v=N50kF0FE3hM&list=PLFdHTR758BvcHRX3nVKMEPHuBdU75dBVE" }
        @{ Name = "ytworship"; Desc = "Worship songs"; URL = "https://www.youtube.com/watch?v=poFZcg6f4J4&list=PLFdHTR758BveEaqE5BWIQI7ukkijjdbbG" }
        @{ Name = "ytpresence"; Desc = "Presence/ambient"; URL = "https://www.youtube.com/watch?v=mYjdVQX2cJQ&list=PLFdHTR758BveAZ9YDY4ALy9iGxQVrkGRl" }
        @{ Name = "ytchristmas"; Desc = "Christmas music"; URL = "https://www.youtube.com/watch?v=aC2LUPJ3dOk&list=PLFdHTR758BvfFgZlzcL17qvB307ysgHvn" }
        @{ Name = "ytyoung"; Desc = "Youth/young music"; URL = "https://www.youtube.com/watch?v=NQJyrsHn9K8&list=PLFdHTR758Bvegbr-HbkHM_C6-SwOP6xVE" }
    )

    Write-Host ""
    Write-Host "Select a playlist:" -ForegroundColor White
    Write-Host ""

    for ($i = 0; $i -lt $playlists.Count; $i++) {
        $num = $i + 1
        $name = $playlists[$i].Name
        $desc = $playlists[$i].Desc
        Write-Host "  $num. " -NoNewline -ForegroundColor Cyan
        Write-Host "$name" -NoNewline -ForegroundColor White
        Write-Host " - $desc" -ForegroundColor Gray
    }

    $customNum = $playlists.Count + 1
    Write-Host "  $customNum. " -NoNewline -ForegroundColor Cyan
    Write-Host "Custom URL" -ForegroundColor White
    Write-Host ""

    $choice = Read-Host "Choice [1]"

    if ([string]::IsNullOrWhiteSpace($choice)) {
        $choice = 1
    }

    $choiceNum = [int]$choice
    if ($choiceNum -ge 1 -and $choiceNum -le $playlists.Count) {
        $selected = $playlists[$choiceNum - 1]
        Write-Success "Selected: $($selected.Name)"
        $script:SelectedPlaylistName = $selected.Name
        return $selected.URL
    } elseif ($choiceNum -eq $customNum) {
        Write-Host ""
        $url = Read-Host "Enter playlist URL"
        $script:SelectedPlaylistName = $null
        if ([string]::IsNullOrWhiteSpace($url)) {
            Write-Warning "No URL entered, using default"
            $script:SelectedPlaylistName = $playlists[0].Name
            return $playlists[0].URL
        }
        return $url
    } else {
        Write-Warning "Invalid choice, using default"
        $script:SelectedPlaylistName = $playlists[0].Name
        return $playlists[0].URL
    }
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
        [bool]$ScriptRegistered = $false,
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
        Write-Success "OBS scene and sources configured automatically"
        Write-Host ""
        Write-Host "Remaining step:" -ForegroundColor White
        Write-Host ""
        Write-Host "  Add the script in OBS:" -ForegroundColor Gray
        Write-Host "  Tools -> Scripts -> Click '+' -> Select:" -ForegroundColor Gray
        Write-Host "  $fullScriptPath" -ForegroundColor Yellow
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

    if ($latestVersion) {
        Write-Success "Latest release: $latestVersion"
    }

    # Step 5: Select playlist first (determines default instance name)
    $playlistURL = Request-PlaylistURL

    # Step 5b: Ask for Gemini API key
    $script:GeminiApiKey = Request-GeminiApiKey

    # Show existing instances
    $existingInstances = Get-ExistingInstances -InstallDir $installDir
    Show-ExistingInstances -Instances $existingInstances -LatestVersion $latestVersion

    # Step 6: Get instance name (defaults to playlist name)
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

        # Check if OBS is running - it may lock files during update
        if (Test-OBSRunning) {
            Write-Host ""
            Write-Warning "OBS is currently running"
            Write-Host "  The script may have files locked that need to be updated." -ForegroundColor Gray
            Write-Host "  Please close OBS before continuing, or unload the script." -ForegroundColor Gray
            Write-Host ""
            $continue = Read-Host "Continue anyway? (y/N)"
            if ($continue -ine "y" -and $continue -ine "yes") {
                Write-Info "Please close OBS and run the installer again"
                return
            }
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

    # Step 7: Try to configure OBS via WebSocket
    $autoConfigured = $false
    $scriptRegistered = $false

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
                    # Give OBS time to fully initialize (WebSocket + UI + internal state)
                    Write-Info "Waiting for OBS to fully initialize..."
                    Start-Sleep -Seconds 20

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
        # OBS is already running
        Write-Success "OBS is already running"

        # Check if WebSocket auth is configured
        $wsConfig = Enable-OBSWebSocket -OBSPath $obsPath -IsPortable $isPortable
        if ($wsConfig.AuthRequired) {
            Write-Warning "WebSocket authentication is enabled"
            Write-Host ""
            $script:wsPassword = Read-Host "Enter your OBS WebSocket password (or press Enter to skip auto-config)"
            if ([string]::IsNullOrEmpty($script:wsPassword)) {
                Write-Info "Skipping auto-configuration"
                $obsRunning = $false
            }
        }
    }

    if ($obsRunning -and (Test-OBSRunning)) {
        Write-Step "Connecting to OBS WebSocket..."

        # Try to connect with retries
        $ws = $null
        for ($attempt = 1; $attempt -le 5; $attempt++) {
            $ws = Connect-OBSWebSocket -Password $script:wsPassword
            if ($ws) {
                break
            }
            if ($attempt -lt 5) {
                Write-Info "Connection failed, retrying... ($attempt/5)"
                Start-Sleep -Seconds 2
            }
        }

        if ($ws) {
            Write-Success "Connected to OBS WebSocket"
            Write-Step "Creating scene and sources..."

            try {
                $instName = $script:InstanceName
                $maxRetries = 8
                $retryDelay = 3

                # Create scene (with retry)
                $sceneCreated = $false
                for ($i = 1; $i -le $maxRetries; $i++) {
                    $result = New-OBSScene -WebSocket $ws -SceneName $instName
                    if ($result) {
                        Write-Success "Scene '$instName' ready"
                        $sceneCreated = $true
                        break
                    }
                    if ($i -lt $maxRetries) {
                        Write-Info "OBS not ready, retrying... ($i/$maxRetries)"
                        Start-Sleep -Seconds $retryDelay
                    }
                }

                $mediaCreated = $false
                $textCreated = $false

                if ($sceneCreated) {
                    # Give OBS time to fully register the scene before creating sources
                    Start-Sleep -Seconds 2

                    # Create media source (with retry)
                    for ($i = 1; $i -le $maxRetries; $i++) {
                        if (New-OBSMediaSource -WebSocket $ws -SceneName $instName -SourceName "${instName}_video") {
                            Write-Success "Media source '${instName}_video' ready"
                            $mediaCreated = $true
                            break
                        }
                        if ($i -lt $maxRetries) {
                            Start-Sleep -Seconds $retryDelay
                        }
                    }

                    # Create text source (with retry)
                    for ($i = 1; $i -le $maxRetries; $i++) {
                        if (New-OBSTextSource -WebSocket $ws -SceneName $instName -SourceName "${instName}_title") {
                            Write-Success "Text source '${instName}_title' ready"
                            $textCreated = $true
                            break
                        }
                        if ($i -lt $maxRetries) {
                            Start-Sleep -Seconds $retryDelay
                        }
                    }

                    # Position sources on canvas
                    $videoSettings = Get-OBSVideoSettings -WebSocket $ws
                    if ($videoSettings) {
                        $canvasWidth = $videoSettings.Width
                        $canvasHeight = $videoSettings.Height

                        # Video: stretch to fill screen
                        if ($mediaCreated) {
                            Set-OBSSourceTransform -WebSocket $ws -SceneName $instName -SourceName "${instName}_video" -Transform @{
                                boundsType = "OBS_BOUNDS_STRETCH"
                                boundsWidth = $canvasWidth
                                boundsHeight = $canvasHeight
                                positionX = 0
                                positionY = 0
                            } | Out-Null
                        }

                        # Text: bottom of screen, full width (subtitle position)
                        if ($textCreated) {
                            Set-OBSSourceTransform -WebSocket $ws -SceneName $instName -SourceName "${instName}_title" -Transform @{
                                positionX = 0
                                positionY = [int]($canvasHeight - 80)
                                boundsType = "OBS_BOUNDS_SCALE_INNER"
                                boundsWidth = $canvasWidth
                                boundsHeight = 80
                                boundsAlignment = 0  # Center
                                alignment = 9  # Bottom-left (anchor point)
                            } | Out-Null
                        }
                    }
                }

                # Only mark as auto-configured if scene was created
                if ($sceneCreated) {
                    $autoConfigured = $true
                    if (-not $mediaCreated -or -not $textCreated) {
                        Write-Warning "Some sources could not be created automatically"
                    }

                    # Note: Script registration via JSON is unreliable, so we always show manual instructions
                    # The scene and sources are the complex part - adding a script is just one click
                } else {
                    Write-Warning "Could not create scene - OBS may need more time to initialize"
                    Write-Info "Please create the scene manually after OBS is fully loaded"
                }

            } catch {
                Write-Warning "Could not fully configure OBS: $_"
            } finally {
                Close-OBSWebSocket
            }
        } else {
            # Connection failed - diagnose and offer retry
            $retryConnection = $true
            while ($retryConnection) {
                Write-Host ""
                Write-ErrorMsg "Could not connect to OBS WebSocket"
                Write-Host ""

                # Diagnose the issue
                Write-Step "Diagnosing connection issue..."

                $diagnosis = @()

                # Check if OBS is still running
                if (-not (Test-OBSRunning)) {
                    $diagnosis += "OBS is not running"
                }

                # Check WebSocket config
                $wsConfigPath = if ($isPortable) {
                    Join-Path $obsPath "config\obs-studio\plugin_config\obs-websocket\config.json"
                } else {
                    Join-Path $env:APPDATA "obs-studio\plugin_config\obs-websocket\config.json"
                }

                if (Test-Path $wsConfigPath) {
                    try {
                        $wsConf = Get-Content $wsConfigPath -Raw | ConvertFrom-Json
                        if ($wsConf.server_enabled -eq $false) {
                            $diagnosis += "WebSocket server is disabled in OBS"
                        }
                        if ($wsConf.auth_required -eq $true -and [string]::IsNullOrEmpty($script:wsPassword)) {
                            $diagnosis += "WebSocket requires password but none provided"
                        }
                    } catch {}
                } else {
                    $diagnosis += "WebSocket config file not found (OBS may need to run once first)"
                }

                # Show diagnosis
                if ($diagnosis.Count -gt 0) {
                    Write-Host ""
                    Write-Host "Possible issues found:" -ForegroundColor Yellow
                    foreach ($issue in $diagnosis) {
                        Write-Host "  - $issue" -ForegroundColor Gray
                    }
                }

                Write-Host ""
                Write-Host "Options:" -ForegroundColor White
                Write-Host "  1. Retry connection" -ForegroundColor Gray
                Write-Host "  2. Enter/change WebSocket password" -ForegroundColor Gray
                Write-Host "  3. Skip auto-configuration (manual setup)" -ForegroundColor Gray
                Write-Host ""
                $choice = Read-Host "Choose (1-3)"

                switch ($choice) {
                    "1" {
                        Write-Step "Retrying connection..."
                        Start-Sleep -Seconds 2
                        $ws = Connect-OBSWebSocket -Password $script:wsPassword
                        if ($ws) {
                            Write-Success "Connected!"
                            # Continue with source creation...
                            $retryConnection = $false
                            # Repeat source creation logic
                            Write-Step "Creating scene and sources..."
                            try {
                                $instName = $script:InstanceName
                                $maxRetries = 5
                                $retryDelay = 2
                                $sceneCreated = $false
                                for ($i = 1; $i -le $maxRetries; $i++) {
                                    if (New-OBSScene -WebSocket $ws -SceneName $instName) {
                                        Write-Success "Scene '$instName' ready"
                                        $sceneCreated = $true
                                        break
                                    }
                                    if ($i -lt $maxRetries) {
                                        Write-Info "OBS not ready, retrying... ($i/$maxRetries)"
                                        Start-Sleep -Seconds $retryDelay
                                    }
                                }
                                if ($sceneCreated) {
                                    for ($i = 1; $i -le $maxRetries; $i++) {
                                        if (New-OBSMediaSource -WebSocket $ws -SceneName $instName -SourceName "${instName}_video") {
                                            Write-Success "Media source '${instName}_video' ready"
                                            break
                                        }
                                        if ($i -lt $maxRetries) { Start-Sleep -Seconds $retryDelay }
                                    }
                                    for ($i = 1; $i -le $maxRetries; $i++) {
                                        if (New-OBSTextSource -WebSocket $ws -SceneName $instName -SourceName "${instName}_title") {
                                            Write-Success "Text source '${instName}_title' ready"
                                            break
                                        }
                                        if ($i -lt $maxRetries) { Start-Sleep -Seconds $retryDelay }
                                    }

                                    # Register the script in OBS
                                    Write-Step "Registering script in OBS..."
                                    $sceneCollection = Get-OBSCurrentSceneCollection -WebSocket $ws
                                    if ($sceneCollection) {
                                        $scriptFilePath = Join-Path $installedPath "$instName.py"
                                        if (Register-OBSScript -OBSPath $obsPath -IsPortable $isPortable -ScriptPath $scriptFilePath -SceneCollectionName $sceneCollection -PlaylistURL $playlistURL) {
                                            Write-Success "Script registered (restart OBS to load)"
                                            $scriptRegistered = $true
                                        }
                                    }

                                    $autoConfigured = $true
                                }
                            } catch {
                                Write-Warning "Error: $_"
                            } finally {
                                Close-OBSWebSocket
                            }
                        }
                    }
                    "2" {
                        $script:wsPassword = Read-Host "Enter WebSocket password"
                    }
                    default {
                        Write-Info "Skipping auto-configuration"
                        $retryConnection = $false
                    }
                }
            }
        }
    } else {
        Write-Info "OBS is not running - skipping auto-configuration"
    }

    # Step 9: Show completion message
    Show-SuccessMessage -ScriptPath $installedPath -AutoConfigured $autoConfigured -ScriptRegistered $scriptRegistered -PlaylistURL $playlistURL
}

# Run the installer
Install-OBSYouTubePlayer

#endregion
