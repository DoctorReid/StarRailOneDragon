@echo off
setlocal enabledelayedexpansion
chcp 65001
cd /D %~dp0

pause
echo 准备关闭现有程序
taskkill /IM "StarRailOneDragon.exe" /F
taskkill /IM "flet.exe" /F

echo 准备更新文件
timeout /t 5 >nul

echo 更新中
xcopy ".temp\StarRailOneDragon" "..\" /E /I /Y
copy ".temp\version.yml" ".\version.yml" /Y

echo 更新成功 即将启动脚本

start "StarRailOneDragon" "../StarRailOneDragon.exe"

echo 启动完成后 可关闭本窗口
pause