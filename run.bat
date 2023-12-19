@echo off
setlocal enabledelayedexpansion
chcp 65001
cd /D %~dp0

echo 如无反应 可切换使用管理员权限运行脚本

REM set local_python=%~dp0.env\venv\Scripts\python.exe
set PYTHONPATH=%~dp0/src
set DEBUG=1

REM !local_python! src/gui/app.py
python src/gui/app.py
pause
