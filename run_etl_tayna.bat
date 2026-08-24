@echo off
cd /d "C:\Users\busra\cargo-data-pipeline"
call venv\Scripts\activate.bat
python src\load\run_etl_tayna.py >> logs\etl_tayna_log.txt 2>&1