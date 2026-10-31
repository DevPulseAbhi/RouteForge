@echo off
cd /d "%~dp0"
if not exist ".venv313\Scripts\python.exe" (
    echo Python 3.13 environment not found.
    echo Create it with: py -3.13 -m venv .venv313
    exit /b 1
)
".venv313\Scripts\python.exe" -m streamlit run app.py
