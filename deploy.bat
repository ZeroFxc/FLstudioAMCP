@echo off
echo ========================================
echo FL Studio MCP - Deploy
echo ========================================
echo.

set "SRC=%~dp0"
set "DST=%USERPROFILE%\Documents\Image-Line\FL Studio\Settings"
set "HW=%DST%\Hardware\NirithyCore"
set "PR=%DST%\Piano roll scripts"

if not exist "%DST%" mkdir "%DST%"
if not exist "%HW%" mkdir "%HW%"
if not exist "%PR%" mkdir "%PR%"

copy /Y "%SRC%device_NirithyCore.py" "%HW%\device_NirithyCore.py"
if errorlevel 1 goto :err

copy /Y "%SRC%NirithyCore.pyscript" "%PR%\NirithyCore.pyscript"
if errorlevel 1 goto :err

if not exist "%HW%\device_NirithyCore.py" goto :err
if not exist "%PR%\NirithyCore.pyscript" goto :err

echo.
echo ========================================
echo Done!
echo 1. Restart MCP server
echo 2. Reload FL Studio controller (Options - MIDI Settings)
echo ========================================
pause
exit /b 0

:err
echo Deploy failed!
pause
exit /b 1