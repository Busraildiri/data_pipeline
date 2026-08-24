@echo off
cd /d C:\Projects\cargo-pipeline
call venv\Scripts\activate.bat
python src\load\run_etl_misa_only.py >> logs\etl_misa_log.txt 2>&1