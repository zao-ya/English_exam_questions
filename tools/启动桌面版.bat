@echo off
setlocal
chcp 65001 >nul
title 考研英语真题词频统计

:: 切换到项目根目录
cd /d "%~dp0\.."

:: 优先使用打包好的 exe
if exist "%~dp0\..\考研英语词频统计.exe" (
    start "" "%~dp0\..\考研英语词频统计.exe"
    exit /b 0
)

:: 回退：用 Python 开发模式启动（无命令行窗口）
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0\..\src\desktop_app.py"
    exit /b 0
)

:: 最后兜底：普通 Python 启动
where python >nul 2>&1
if %errorlevel% equ 0 (
    start "" python "%~dp0\..\src\desktop_app.py"
    exit /b 0
)

echo [错误] 未找到 考研英语词频统计.exe 或 Python
pause
