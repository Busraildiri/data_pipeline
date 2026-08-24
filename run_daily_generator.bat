@echo off
cd /d C:\Projects\cargo-pipeline
.\venv\Scripts\python.exe src\mock_generator\daily_runner.py >> logs\daily_run.log 2>&1
