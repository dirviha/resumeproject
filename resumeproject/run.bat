@echo off
cd /d D:\project89\resumeproject
call ..\venv\Scripts\activate
python manage.py runserver 127.0.0.1:8000
pause