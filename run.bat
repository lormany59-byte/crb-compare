@echo off
REM ============================================================
REM  ດັບເບິລຄິກໄຟລ໌ນີ້ ເພື່ອເປີດລະບົບ CRB Deposit Comparison
REM  Double-click this file to start the CRB comparison app.
REM ============================================================
cd /d "%~dp0"

REM --- ຫາໂປຣແກຣມ Python (try py launcher, then known install path, then python) ---
set "PYEXE="
where py >nul 2>nul && set "PYEXE=py"
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYEXE set "PYEXE=python"

echo Using Python: %PYEXE%
echo.

REM --- ຕິດຕັ້ງ dependencies (ຄັ້ງທຳອິດຈະຊ້າໜ້ອຍ, ເທື່ອຫຼັງໄວ) ---
"%PYEXE%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [ERROR] ຕິດຕັ້ງ dependencies ບໍ່ສຳເລັດ. ກວດວ່າຕິດຕັ້ງ Python ແລ້ວບໍ.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  ເປີດ browser ໄປທີ່:  http://127.0.0.1:5000
echo  ປິດ server: ກົດ Ctrl+C ຫຼື ປິດໜ້າຕ່າງນີ້
echo ============================================================
echo.

REM --- ເປີດ browser ໃຫ້ອັດຕະໂນມັດ ແລ້ວ start server ---
start "" http://127.0.0.1:5000
"%PYEXE%" app.py

pause
