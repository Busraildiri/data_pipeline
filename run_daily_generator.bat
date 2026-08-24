@echo off
cd /d "%~dp0"
if not exist logs mkdir logs
call venv\Scripts\activate.bat
python src\mock_generator\daily_runner.py >> logs\daily_run.log 2>&1
