@echo off
call .venv\Scripts\activate
python launch_app.py --mysql --no-reset --no-seed
pause