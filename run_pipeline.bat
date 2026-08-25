@echo off
cd /d "%~dp0"

rem Windows a??ld?ktan sonra internet ba?lant?s?n? bekle
timeout /t 30 /nobreak >nul

call run_daily_generator.bat
if errorlevel 1 exit /b %errorlevel%

call run_etl_tayna.bat
if errorlevel 1 exit /b %errorlevel%

call run_etl_misa.bat
if errorlevel 1 exit /b %errorlevel%
