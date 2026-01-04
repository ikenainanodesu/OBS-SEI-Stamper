@echo off
REM OBS SEI Stamper Plugin - Automated Build and Install Script
REM This script automates the CMake build process and installs the plugin to the output directory

echo ================================================
echo OBS SEI Stamper Plugin - Build and Install
echo ================================================
echo.

REM Check if build directory exists
if not exist "build" (
    echo Creating build directory...
    mkdir build
) else (
    echo Build directory exists, cleaning...
    rmdir /S /Q build
    mkdir build
)

REM Navigate to build directory
cd build

echo.
echo ================================================
echo Step 1: Configuring CMake...
echo ================================================
cmake .. -G "Visual Studio 17 2022" -A x64
if %ERRORLEVEL% neq 0 (
    echo ERROR: CMake configuration failed!
    cd ..
    pause
    exit /b 1
)

echo.
echo ================================================
echo Step 2: Building project (Release)...
echo ================================================
cmake --build . --config Release
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed!
    cd ..
    pause
    exit /b 1
)

echo.
echo ================================================
echo Step 3: Installing to output directory...
echo ================================================
cmake --install . --config Release --prefix ../out/obs-studio
if %ERRORLEVEL% neq 0 (
    echo ERROR: Install failed!
    cd ..
    pause
    exit /b 1
)

REM Copy SRT library to output directory (if exists)
echo.
echo ================================================
echo Step 4: Copying dependencies...
echo ================================================

set SRT_DLL_PATHS=^
..\srt\_build\Release\srt.dll ^
..\obs-studio-master\build\rundir\Release\bin\64bit\srt.dll

for %%P in (%SRT_DLL_PATHS%) do (
    if exist "%%P" (
        echo Found SRT library: %%P
        if not exist "..\out\obs-studio\obs-plugins\64bit" mkdir "..\out\obs-studio\obs-plugins\64bit"
        copy /Y "%%P" "..\out\obs-studio\obs-plugins\64bit\" >nul
        echo SRT library copied successfully
        goto :srt_done
    )
)
echo WARNING: SRT library not found, receiver may not work
:srt_done

REM Copy locale files
echo.
echo Copying locale files...
xcopy /E /I /Y ..\data\locale ..\out\obs-studio\data\obs-plugins\obs-sei-stamper\locale >nul
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to copy locale files
) else (
    echo Locale files copied successfully
)

REM Return to project root
cd ..

echo.
echo ================================================
echo Build Complete!
echo ================================================
echo.
echo Output directory: %CD%\out\obs-studio
echo Plugin DLL: %CD%\out\obs-studio\obs-plugins\64bit\obs-sei-stamper.dll
echo.
echo To install to OBS Studio:
echo   1. Copy contents of out\obs-studio\ to C:\Program Files\obs-studio
echo   2. Administrator privileges required
echo   3. Restart OBS Studio
echo.
echo ================================================
pause
