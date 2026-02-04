@echo off
echo ==========================================
echo OCR Tools Installation Script
echo ==========================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator - Good!
) else (
    echo WARNING: Not running as Administrator
    echo PATH modifications will be for current user only
)
echo.

REM Create tools directory
set TOOLS_DIR=%USERPROFILE%\ocr_tools
if not exist "%TOOLS_DIR%" mkdir "%TOOLS_DIR%"
echo Created tools directory: %TOOLS_DIR%
echo.

REM Download Poppler
echo ==========================================
echo Step 1: Installing Poppler
echo ==========================================
echo.

set POPPLER_URL=https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip
set POPPLER_ZIP=%TEMP%\poppler.zip
set POPPLER_DIR=%TOOLS_DIR%\poppler

echo Downloading Poppler...
echo This may take a few minutes...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%POPPLER_URL%' -OutFile '%POPPLER_ZIP%' -UseBasicParsing}"

if exist "%POPPLER_ZIP%" (
    echo Download complete!
    echo.
    echo Extracting Poppler...
    powershell -Command "Expand-Archive -Path '%POPPLER_ZIP%' -DestinationPath '%POPPLER_DIR%' -Force"
    del "%POPPLER_ZIP%"
    echo Extraction complete!
    echo.
    
    REM Find bin directory
    for /r "%POPPLER_DIR%" %%d in (.) do (
        if exist "%%d\pdftoppm.exe" (
            set POPPLER_BIN=%%d
            goto :found_poppler
        )
    )
    
    :found_poppler
    if defined POPPLER_BIN (
        echo Found Poppler bin directory: %POPPLER_BIN%
        echo.
        
        REM Add to PATH
        for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CURRENT_PATH=%%B"
        echo %CURRENT_PATH% | findstr /C:"%POPPLER_BIN%" >nul
        if %errorLevel% neq 0 (
            setx PATH "%CURRENT_PATH%;%POPPLER_BIN%"
            set PATH=%PATH%;%POPPLER_BIN%
            echo Added Poppler to PATH!
        ) else (
            echo Poppler already in PATH
        )
    ) else (
        echo ERROR: Could not find Poppler bin directory
        echo Please extract manually and add bin folder to PATH
    )
) else (
    echo ERROR: Failed to download Poppler
    echo Please download manually from:
    echo %POPPLER_URL%
)

echo.
echo ==========================================
echo Step 2: Tesseract OCR
echo ==========================================
echo.
echo Tesseract requires manual installation:
echo.
echo 1. Download installer from:
echo    https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo 2. Run the installer
echo.
echo 3. IMPORTANT: Check "Add to PATH" during installation
echo.

REM Check if Tesseract is already installed
where tesseract >nul 2>&1
if %errorLevel% == 0 (
    echo Tesseract found in PATH!
    tesseract --version
) else (
    echo Tesseract not found in PATH
    echo Please install Tesseract manually
)

echo.
echo ==========================================
echo Installation Summary
echo ==========================================
echo.
echo IMPORTANT: After installation, you MUST:
echo 1. Close and reopen this terminal
echo 2. Restart the backend server
echo 3. Try uploading your PDF again
echo.
echo Verification:
echo.

REM Refresh PATH
set PATH=%PATH%;%POPPLER_BIN%

where pdftoppm >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Poppler is installed
    pdftoppm -h | findstr /C:"pdftoppm" | findstr /V "Copyright"
) else (
    echo [FAIL] Poppler not found - may need to restart terminal
)

where tesseract >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Tesseract is installed
    tesseract --version | findstr /C:"tesseract"
) else (
    echo [FAIL] Tesseract not found - please install manually
)

echo.
echo ==========================================
echo Done!
echo ==========================================
pause

