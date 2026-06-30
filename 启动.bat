@echo off
chcp 65001 >nul
title 考研英语真题词频统计 WebApp

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║     考研英语真题词频统计 WebApp — 一键启动器         ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: ── 1. 检查 Python ──
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    echo         下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [✓] Python 版本: %PYVER%

:: ── 2. 切换到项目目录 ──
cd /d "%~dp0"
set PROJECT_DIR=%~dp0
echo [✓] 项目目录: %PROJECT_DIR%

:: ── 3. 检查 / 安装依赖 ──
echo.
echo [*] 检查 Python 依赖...
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 正在安装依赖，请稍候...
    pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo [✓] 依赖安装完成
) else (
    echo [✓] 依赖已就绪
)

:: ── 4. 检查 NLTK 数据 ──
echo.
echo [*] 检查 NLTK 数据...
python -c "import nltk; nltk.data.find('corpora/wordnet')" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 正在下载 NLTK 数据（仅首次需要，约需 1-2 分钟）...
    python -c "import nltk; nltk.download('wordnet', quiet=True); nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); nltk.download('averaged_perceptron_tagger_eng', quiet=True); nltk.download('words', quiet=True); nltk.download('maxent_ne_chunker', quiet=True); nltk.download('maxent_ne_chunker_tab', quiet=True); print('OK')"
    if %errorlevel% neq 0 (
        echo [警告] NLTK 数据下载失败，WebApp 仍可启动但数据处理可能受影响
    ) else (
        echo [✓] NLTK 数据下载完成
    )
) else (
    echo [✓] NLTK 数据已就绪
)

:: ── 5. 检查数据库 ──
echo.
if exist "data\exam_words.db" (
    echo [✓] 数据库已存在，跳过数据处理
    set NEED_BUILD=0
) else (
    echo [!] 数据库不存在，需要先处理 PDF 数据
    echo.
    echo     完整数据处理需要 5-10 分钟，是否现在处理？
    echo     [Y] 是 — 运行完整数据处理流水线
    echo     [N] 否 — 退出（需要数据才能启动 WebApp）
    echo.
    choice /c YN /m "请选择"
    if errorlevel 2 goto :skip_build
    echo.
    echo [*] ====== Step 1/6: PDF 文本提取 ======
    pushd scripts
    python pdf_extractor.py "..\英语真题源文件PDF" "..\data\extracted"
    if %errorlevel% neq 0 (
        popd
        echo [错误] PDF 提取失败
        pause
        exit /b 1
    )
    popd
    echo [✓] Step 1/6 完成

    echo [*] ====== Step 2/6: 题型解析 ======
    pushd scripts
    python exam_parser.py
    if %errorlevel% neq 0 (
        popd
        echo [错误] 题型解析失败
        pause
        exit /b 1
    )
    popd
    echo [✓] Step 2/6 完成

    echo [*] ====== Step 3/6: 合并词修复 ======
    pushd scripts
    python word_splitter.py
    if %errorlevel% neq 0 (
        echo [警告] 合并词修复失败，继续执行...
    )
    popd

    echo [*] ====== Step 4/6: 手动修正 ======
    pushd scripts
    python manual_fix.py
    if %errorlevel% neq 0 (
        echo [警告] 手动修正失败，继续执行...
    )
    popd

    echo [*] ====== Step 5/6: 单词提取与词频统计 ======
    pushd scripts
    python word_processor.py
    if %errorlevel% neq 0 (
        popd
        echo [错误] 单词处理失败
        pause
        exit /b 1
    )
    popd
    echo [✓] Step 5/6 完成

    echo [*] ====== Step 6/6: 数据库构建 ======
    pushd scripts
    python freq_builder.py
    if %errorlevel% neq 0 (
        popd
        echo [错误] 数据库构建失败
        pause
        exit /b 1
    )
    popd
    echo [✓] Step 6/6 完成

    echo [✓] 数据处理完成！
    set NEED_BUILD=1
)

:skip_build
if not exist "data\exam_words.db" (
    echo [错误] 数据库文件不存在，无法启动 WebApp
    pause
    exit /b 1
)

:: ── 6. 启动 Flask WebApp ──
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║   🚀 正在启动 WebApp ...                                  ║
echo ║                                                          ║
echo ║   浏览器将自动打开:  http://127.0.0.1:5000                 ║
echo ║                                                          ║
echo ║   按 Ctrl+C 可停止服务器                                   ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

:: 启动 Flask（会自动打开浏览器）
python webapp\app.py

pause
