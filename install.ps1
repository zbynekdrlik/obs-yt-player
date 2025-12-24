#Requires -Version 5.1
<#
.SYNOPSIS
    OBS YouTube Player Installer
.DESCRIPTION
    Downloads and installs OBS YouTube Player to your OBS Studio installation.
    Supports both system-installed and portable OBS.
.EXAMPLE
    irm https://raw.githubusercontent.com/zbynekdrlik/obs-yt-player/main/install.ps1 | iex
.NOTES
    Author: OBS YouTube Player Team
    Repository: https://github.com/zbynekdrlik/obs-yt-player
#>

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # Faster downloads

# Configuration
$RepoOwner = "zbynekdrlik"
$RepoName = "obs-yt-player"
$ScriptFolder = "yt-player-main"

function Write-Header {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  OBS YouTube Player Installer" -ForegroundColor Cyan
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

function Write-Error {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message" -ForegroundColor Gray
}

function Test-PortableOBS {
    param([string]$Path)

    # Check for OBS executable in common locations
    $obsExePaths = @(
        (Join-Path $Path "bin\64bit\obs64.exe"),
        (Join-Path $Path "bin\32bit\obs32.exe"),
        (Join-Path $Path "obs64.exe")
    )

    foreach ($exePath in $obsExePaths) {
        if (Test-Path $exePath) {
            # Also verify it has the data folder structure
            $dataPath = Join-Path $Path "data"
            if (Test-Path $dataPath) {
                return $true
            }
        }
    }
    return $false
}

function Test-PortableModeEnabled {
    param([string]$Path)

    # Check for portable_mode.txt
    $portableFile = Join-Path $Path "portable_mode.txt"
    if (Test-Path $portableFile) {
        return $true
    }

    # Check for config folder (indicates portable mode was used)
    $configPath = Join-Path $Path "config\obs-studio"
    if (Test-Path $configPath) {
        return $true
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

function Get-ScriptsDirectory {
    param(
        [string]$OBSPath,
        [bool]$IsPortable
    )

    if ($IsPortable) {
        # For portable, put scripts in a scripts folder within OBS directory
        return Join-Path $OBSPath "scripts"
    } else {
        # For system install, use AppData location
        return Join-Path $env:APPDATA "obs-studio\scripts"
    }
}

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
        # If no releases, use main branch
        Write-Info "No releases found, will download from main branch"
        return $null
    }
}

function Download-Repository {
    param([string]$DestinationPath)

    $release = Get-LatestRelease

    if ($release) {
        $version = $release.tag_name
        Write-Step "Downloading version $version..."
        $downloadUrl = "https://github.com/$RepoOwner/$RepoName/archive/refs/tags/$version.zip"
        $extractFolder = "$RepoName-$($version.TrimStart('v'))"
    } else {
        Write-Step "Downloading latest from main branch..."
        $downloadUrl = "https://github.com/$RepoOwner/$RepoName/archive/refs/heads/main.zip"
        $extractFolder = "$RepoName-main"
    }

    $tempZip = Join-Path $env:TEMP "obs-yt-player-download.zip"
    $tempExtract = Join-Path $env:TEMP "obs-yt-player-extract"

    try {
        # Download
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip -UseBasicParsing
        Write-Success "Download complete"

        # Extract
        Write-Step "Extracting files..."
        if (Test-Path $tempExtract) {
            Remove-Item $tempExtract -Recurse -Force
        }
        Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

        # Find the script folder
        $sourcePath = Join-Path $tempExtract "$extractFolder\$ScriptFolder"
        if (-not (Test-Path $sourcePath)) {
            throw "Could not find $ScriptFolder in downloaded archive"
        }

        # Copy to destination
        $finalDest = Join-Path $DestinationPath $ScriptFolder
        if (Test-Path $finalDest) {
            Write-Step "Updating existing installation..."
            Remove-Item $finalDest -Recurse -Force
        }

        Copy-Item -Path $sourcePath -Destination $finalDest -Recurse
        Write-Success "Files installed to: $finalDest"

        return $finalDest

    } finally {
        # Cleanup
        if (Test-Path $tempZip) { Remove-Item $tempZip -Force }
        if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force }
    }
}

function Show-PostInstallInstructions {
    param(
        [string]$ScriptPath,
        [string]$InstanceName = "ytplay"
    )

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps in OBS Studio:" -ForegroundColor White
    Write-Host ""
    Write-Host "1. " -NoNewline -ForegroundColor Cyan
    Write-Host "Add the script:"
    Write-Host "   Tools -> Scripts -> Click '+' -> Select:" -ForegroundColor Gray
    Write-Host "   $ScriptPath\ytplay.py" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. " -NoNewline -ForegroundColor Cyan
    Write-Host "Create a scene named: " -NoNewline
    Write-Host "$InstanceName" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. " -NoNewline -ForegroundColor Cyan
    Write-Host "Add sources to your scene:"
    Write-Host "   - Media Source: " -NoNewline -ForegroundColor Gray
    Write-Host "${InstanceName}_video" -ForegroundColor Yellow
    Write-Host "     (uncheck 'Local File')" -ForegroundColor DarkGray
    Write-Host "   - Text Source:  " -NoNewline -ForegroundColor Gray
    Write-Host "${InstanceName}_title" -ForegroundColor Yellow -NoNewline
    Write-Host " (optional)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "4. " -NoNewline -ForegroundColor Cyan
    Write-Host "Configure in script properties:"
    Write-Host "   - Set your YouTube Playlist URL" -ForegroundColor Gray
    Write-Host "   - Optionally add Gemini API key for better metadata" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Documentation: " -NoNewline
    Write-Host "https://github.com/$RepoOwner/$RepoName#readme" -ForegroundColor Blue
    Write-Host ""
}

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
    Write-Error "Could not detect OBS installation automatically."
    Write-Host ""
    Write-Host "Please enter the path to your OBS installation folder" -ForegroundColor White
    Write-Host "(e.g., C:\OBS-Studio-Portable or C:\Program Files\obs-studio):" -ForegroundColor Gray
    Write-Host ""

    $customPath = Read-Host "OBS Path"

    if ([string]::IsNullOrWhiteSpace($customPath)) {
        Write-Error "No path provided. Installation cancelled."
        return $null
    }

    if (-not (Test-Path $customPath)) {
        Write-Error "Path does not exist: $customPath"
        return $null
    }

    return $customPath
}

# Main installation logic
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

        # Determine if custom path is portable
        $isPortable = Test-PortableOBS $customPath
        if (-not $isPortable) {
            # Might be a system-style install in custom location
            Write-Info "Treating as system-style installation"
        }

        $obsPath = $customPath
    }

    # Step 4: Determine scripts directory
    $scriptsDir = Get-ScriptsDirectory -OBSPath $obsPath -IsPortable $isPortable

    Write-Step "Scripts will be installed to:"
    Write-Info $scriptsDir
    Write-Host ""

    # Create scripts directory if needed
    if (-not (Test-Path $scriptsDir)) {
        Write-Step "Creating scripts directory..."
        New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
    }

    # Step 5: Download and install
    try {
        $installedPath = Download-Repository -DestinationPath $scriptsDir
        Show-PostInstallInstructions -ScriptPath $installedPath
    } catch {
        Write-Error "Installation failed: $_"
        return
    }
}

# Run the installer
Install-OBSYouTubePlayer
