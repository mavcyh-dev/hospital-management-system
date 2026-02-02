@echo off
call .venv\Scripts\activate
python launch_app.py --mysql --reset --seed-random-users
pause