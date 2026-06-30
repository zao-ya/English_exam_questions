@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title 考研英语词频统计 — 打包工具

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║       考研英语真题词频统计 — PyInstaller 打包器          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo   即将使用 PyInstaller 打包为单个 .exe 桌面应用。
echo   最终文件: 考研英语词频统计.exe（约 50 MB，项目根目录）
echo   无命令行窗口，双击即可运行。
echo.

:: ── 1. 检查 Python ──
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)
echo [✓] Python 已就绪

:: ── 2. 切换到项目根目录 ──
cd /d "%~dp0\.."

:: ── 3. 安装 PyInstaller ──
echo [*] 安装/更新 PyInstaller...
pip install pyinstaller>=6.0 -q
if %errorlevel% neq 0 (
    echo [错误] PyInstaller 安装失败
    pause
    exit /b 1
)
echo [✓] PyInstaller 已就绪

:: ── 4. 清理旧构建 ──
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "考研英语词频统计.exe" del /q "考研英语词频统计.exe"
if exist "考研英语词频统计.spec" del /q "考研英语词频统计.spec"
echo [✓] 旧构建已清理

:: ── 5. PyInstaller 打包 ──
echo.
echo ════════════════════════════════════════════════════════════
echo   正在打包，请耐心等待（约 2-5 分钟）...
echo ════════════════════════════════════════════════════════════
echo.

python -m PyInstaller ^
  --onefile ^
  --noconsole ^
  --name "考研英语词频统计" ^
  --add-data "src\webapp\templates;webapp\templates" ^
  --add-data "src\webapp\static;webapp\static" ^
  --add-data "src\data\exam_words.db;data" ^
  --collect-submodules flask ^
  --collect-submodules webview ^
  --hidden-import openpyxl ^
  --hidden-import clr ^
  src\desktop_app.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 打包失败，请检查上方输出信息
    pause
    exit /b 1
)

:: ── 6. 复制到根目录 ──
copy /y "dist\考研英语词频统计.exe" "考研英语词频统计.exe" >nul
echo [✓] 已复制到根目录

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║   ✅ 打包完成！                                           ║
echo ║                                                          ║
echo ║   文件位置: 考研英语词频统计.exe  （项目根目录，双击运行）  ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo   按任意键关闭...
pause >nul
