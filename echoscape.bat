@echo off
setlocal
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Setting up virtual environment...
    python -m venv .venv || (popd & exit /b 1)
    ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt || (popd & exit /b 1)
)
".venv\Scripts\python.exe" -m echoscape %*
set EXITCODE=%ERRORLEVEL%
popd
exit /b %EXITCODE%
