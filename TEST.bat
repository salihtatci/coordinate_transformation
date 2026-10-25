@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
if not exist ".venv\Scripts\python.exe" (
  echo Once KURULUM.bat ile kurulum yapin.
  pause
  exit /b 1
)
echo ===== Hesap cekirdegi testleri (test_jeodezi.py) =====
".venv\Scripts\python.exe" test_jeodezi.py
set "HATA1=%errorlevel%"
echo.
echo ===== Arayuz testleri (test_arayuz.py) =====
".venv\Scripts\python.exe" test_arayuz.py
set "HATA2=%errorlevel%"
echo.
if "%HATA1%%HATA2%"=="00" (
  echo Tum testler gecti.
) else (
  echo En az bir test BASARISIZ. Yukaridaki ciktiyi inceleyin.
)
pause
