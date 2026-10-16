@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Once KURULUM.bat ile kurulum yapin.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" test_jeodezi.py
pause
