@echo off
setlocal enabledelayedexpansion
chcp 65001

echo 如无反应 可切换使用管理员权限运行脚本

set local_python=%~dp0.env\venv\Scripts\python.exe
set PYTHONPATH=%~dp0/src

!local_python! src/gui/single_page.py
pause
