@echo off
REM ============================================================
REM  ສ້າງໄຟລ໌ .exe ດຽວ (standalone) ສຳລັບແຈກໃຫ້ພະນັກງານ
REM  Build a single standalone .exe with PyInstaller.
REM  ຜົນລັບ: dist\CRB-Compare.exe
REM ============================================================
cd /d "%~dp0"

set "PYEXE="
where py >nul 2>nul && set "PYEXE=py"
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYEXE set "PYEXE=python"

echo Using Python: %PYEXE%
echo Installing dependencies + PyInstaller...
"%PYEXE%" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 ( echo [ERROR] pip install failed & pause & exit /b 1 )

echo.
echo Building CRB-Compare.exe ...
"%PYEXE%" -m PyInstaller --noconfirm --onefile --name CRB-Compare ^
  --paths crb_compare ^
  --add-data "crb_compare/templates/index.html;templates" ^
  --add-data "crb_compare/config.yaml;." ^
  --hidden-import app ^
  --hidden-import compare ^
  --hidden-import reader ^
  --hidden-import excel_writer ^
  crb_compare\crb_desktop.py
if errorlevel 1 ( echo [ERROR] build failed & pause & exit /b 1 )

echo.
echo ============================================================
echo  ສຳເລັດ!  ໄຟລ໌ຢູ່ທີ່:  dist\CRB-Compare.exe
echo  ກ໊ອບປີ້ໄຟລ໌ນັ້ນໄຟລ໌ດຽວໄປໃຫ້ພະນັກງານ ດັບເບິລຄິກໃຊ້ໄດ້ເລີຍ.
echo ============================================================
pause
