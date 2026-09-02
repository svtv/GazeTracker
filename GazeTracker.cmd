@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"
if not exist "venv\Scripts\python.exe" exit /b 1
"venv\Scripts\python.exe" "main.pyw"
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
