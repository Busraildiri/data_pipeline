@echo off
cd /d "%~dp0"
if not exist logs mkdir logs
call venv\Scripts\activate.bat
python src\load\run_etl_tayna.py >> logs\etl_tayna_log.txt 2>&1
