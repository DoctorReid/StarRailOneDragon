@echo off
setlocal enabledelayedexpansion
chcp 65001
cd /D %~dp0

echo 正在更新文件
timeout /t 1 >nul

xcopy ".temp\StarRailOneDragon" "..\" /E /I /Y
copy ".temp\version.yml" ".\version.yml" /Y

echo 更新成功 即将启动脚本

start "StarRailOneDragon" "../StarRailOneDragon.exe"
exit