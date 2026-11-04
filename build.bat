@echo off
chcp 65001 >nul
echo ========================================
echo ساخت EXE با pyinstaller
echo ========================================

echo.
echo پاکسازی...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del ElectroCalc.spec 2>nul

echo.
echo ساخت EXE...
pyinstaller --onefile --windowed ^
  --icon=assets\icon.ico ^
  --name=ElectroCalc ^
  --add-data "assets;assets" ^
  --collect-submodules electrocalc ^
  --collect-data electrocalc ^
  main.py

echo.
echo کپی فایل‌های لازم...
copy electrocalc.db dist\electrocalc.db
xcopy assets dist\assets\ /E /Y
mkdir dist\exports 2>nul

echo.
echo ========================================
echo تمام! EXE تو پوشه dist
echo ========================================
pause