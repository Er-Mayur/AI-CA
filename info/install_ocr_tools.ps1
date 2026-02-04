# OCR Tools Installation Script for Windows
# This script installs Poppler and Tesseract OCR for PDF text extraction

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "OCR Tools Installation Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "PATH modifications will be for current user only" -ForegroundColor Yellow
    Write-Host ""
}

# Create tools directory
$toolsDir = "$env:USERPROFILE\ocr_tools"
if (-not (Test-Path $toolsDir)) {
    New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
    Write-Host "Created tools directory: $toolsDir" -ForegroundColor Green
}

# Function to download and extract ZIP
function Install-FromZip {
    param(
        [string]$Name,
        [string]$DownloadUrl,
        [string]$InstallPath,
        [string]$BinPath
    )
    
    Write-Host "Installing $Name..." -ForegroundColor Cyan
    
    # Check if already installed
    if (Test-Path $BinPath) {
        Write-Host "$Name appears to be already installed at: $InstallPath" -ForegroundColor Yellow
        return $true
    }
    
    # Download
    $zipPath = Join-Path $env:TEMP "$Name.zip"
    Write-Host "Downloading $Name from $DownloadUrl..." -ForegroundColor Yellow
    Write-Host "This may take a few minutes..." -ForegroundColor Yellow
    
    try {
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $zipPath -UseBasicParsing
        Write-Host "Download complete!" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to download $Name" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download manually:" -ForegroundColor Yellow
        Write-Host "  $DownloadUrl" -ForegroundColor Yellow
        return $false
    }
    
    # Extract
    Write-Host "Extracting $Name..." -ForegroundColor Yellow
    try {
        Expand-Archive -Path $zipPath -DestinationPath $InstallPath -Force
        Write-Host "Extraction complete!" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to extract $Name" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        return $false
    }
    
    # Cleanup
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
    
    return $true
}

# Function to add to PATH
function Add-ToPath {
    param([string]$PathToAdd)
    
    if (-not (Test-Path $PathToAdd)) {
        Write-Host "WARNING: Path does not exist: $PathToAdd" -ForegroundColor Red
        return $false
    }
    
    # Check if already in PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -like "*$PathToAdd*") {
        Write-Host "Path already in PATH variable" -ForegroundColor Yellow
        return $true
    }
    
    # Add to PATH
    try {
        $newPath = $currentPath + ";$PathToAdd"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host "Added to PATH: $PathToAdd" -ForegroundColor Green
        
        # Also add to current session
        $env:Path += ";$PathToAdd"
        return $true
    } catch {
        Write-Host "WARNING: Could not add to PATH permanently (requires admin)" -ForegroundColor Yellow
        Write-Host "Adding to current session PATH only..." -ForegroundColor Yellow
        $env:Path += ";$PathToAdd"
        return $true
    }
}

# Install Poppler
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 1: Installing Poppler" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Poppler latest release URL (you may need to update this)
$popplerUrl = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
$popplerDir = "$toolsDir\poppler"
$popplerBin = "$popplerDir\poppler-23.11.0\Library\bin"

$popplerInstalled = Install-FromZip -Name "Poppler" -DownloadUrl $popplerUrl -InstallPath $popplerDir -BinPath $popplerBin

if ($popplerInstalled) {
    # Find actual bin directory (version may vary)
    $popplerBinDirs = Get-ChildItem -Path $popplerDir -Recurse -Directory -Filter "bin" -ErrorAction SilentlyContinue
    if ($popplerBinDirs) {
        $actualBinPath = $popplerBinDirs[0].FullName
        Write-Host "Found Poppler bin directory: $actualBinPath" -ForegroundColor Green
        Add-ToPath -PathToAdd $actualBinPath
    } else {
        # Try alternative paths
        $altPaths = @(
            "$popplerDir\poppler-23.11.0\Library\bin",
            "$popplerDir\poppler\Library\bin",
            "$popplerDir\bin"
        )
        foreach ($altPath in $altPaths) {
            if (Test-Path $altPath) {
                Write-Host "Found Poppler bin directory: $altPath" -ForegroundColor Green
                Add-ToPath -PathToAdd $altPath
                break
            }
        }
    }
}

Write-Host ""

# Install Tesseract
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 2: Installing Tesseract OCR" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Tesseract installer URL
$tesseractUrl = "https://github.com/UB-Mannheim/tesseract/wiki"
Write-Host "Tesseract requires manual installation:" -ForegroundColor Yellow
Write-Host "1. Download installer from: $tesseractUrl" -ForegroundColor Yellow
Write-Host "2. Run the installer" -ForegroundColor Yellow
Write-Host "3. Make sure to check 'Add to PATH' during installation" -ForegroundColor Yellow
Write-Host ""

# Check common installation paths
$tesseractPaths = @(
    "C:\Program Files\Tesseract-OCR",
    "C:\Program Files (x86)\Tesseract-OCR",
    "C:\Tesseract-OCR"
)

$tesseractFound = $false
foreach ($path in $tesseractPaths) {
    if (Test-Path "$path\tesseract.exe") {
        Write-Host "Found Tesseract at: $path" -ForegroundColor Green
        Add-ToPath -PathToAdd $path
        $tesseractFound = $true
        break
    }
}

if (-not $tesseractFound) {
    Write-Host "Tesseract not found in common locations." -ForegroundColor Yellow
    Write-Host "Please install Tesseract manually from:" -ForegroundColor Yellow
    Write-Host "  $tesseractUrl" -ForegroundColor Cyan
}

Write-Host ""

# Verify installation
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Verification" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# Check Poppler
Write-Host "Checking Poppler..." -ForegroundColor Cyan
try {
    $popplerVersion = & pdftoppm -h 2>&1 | Select-Object -First 1
    Write-Host "✓ Poppler installed successfully!" -ForegroundColor Green
    Write-Host "  $popplerVersion" -ForegroundColor Gray
} catch {
    Write-Host "✗ Poppler not found in PATH" -ForegroundColor Red
    Write-Host "  You may need to restart your terminal or add Poppler bin folder to PATH manually" -ForegroundColor Yellow
}

# Check Tesseract
Write-Host "Checking Tesseract..." -ForegroundColor Cyan
try {
    $tesseractVersion = & tesseract --version 2>&1 | Select-Object -First 1
    Write-Host "✓ Tesseract installed successfully!" -ForegroundColor Green
    Write-Host "  $tesseractVersion" -ForegroundColor Gray
} catch {
    Write-Host "✗ Tesseract not found in PATH" -ForegroundColor Red
    Write-Host "  Please install Tesseract from: $tesseractUrl" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: If tools were just installed, you may need to:" -ForegroundColor Yellow
Write-Host "1. Restart your terminal/PowerShell" -ForegroundColor Yellow
Write-Host "2. Restart the backend server" -ForegroundColor Yellow
Write-Host "3. Try uploading your PDF again" -ForegroundColor Yellow
Write-Host ""

