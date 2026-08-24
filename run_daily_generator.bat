@echo off
cd /d C:\Users\busra\cargo-data-pipeline
call venv\Scripts\activate.bat
python src\mock_generator\daily_runner.py >> logs\daily_run.log 2>&1
