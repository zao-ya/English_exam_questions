#!/bin/bash
# 考研英语真题词频统计 WebApp — 一键启动器 (Git Bash / Linux / macOS)

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     考研英语真题词频统计 WebApp — 一键启动器         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. 检查 Python ──
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "[错误] 未找到 Python，请先安装 Python 3.9+"
    echo "       下载地址: https://www.python.org/downloads/"
    exit 1
fi
echo "[✓] Python: $($PYTHON --version 2>&1)"

# ── 2. 切换到项目根目录 ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
echo "[✓] 项目目录: $(pwd)"

# ── 3. 安装依赖 ──
echo ""
echo "[*] 检查 Python 依赖..."
if ! $PYTHON -c "import flask" 2>/dev/null; then
    echo "[!] 正在安装依赖..."
    $PYTHON -m pip install -r tools/requirements.txt -q
    echo "[✓] 依赖安装完成"
else
    echo "[✓] 依赖已就绪"
fi

# ── 4. 检查 NLTK 数据 ──
echo ""
echo "[*] 检查 NLTK 数据..."
if ! $PYTHON -c "import nltk; nltk.data.find('corpora/wordnet')" 2>/dev/null; then
    echo "[!] 正在下载 NLTK 数据（仅首次需要）..."
    $PYTHON -c "
import nltk
for pkg in ['wordnet','punkt','punkt_tab','averaged_perceptron_tagger','averaged_perceptron_tagger_eng','words','maxent_ne_chunker','maxent_ne_chunker_tab']:
    try:
        nltk.download(pkg, quiet=True)
        print(f'  OK: {pkg}')
    except Exception as e:
        print(f'  WARN: {pkg} - {e}')
"
    echo "[✓] NLTK 数据下载完成"
else
    echo "[✓] NLTK 数据已就绪"
fi

# ── 5. 检查数据库 ──
echo ""
if [ -f "src/data/exam_words.db" ]; then
    echo "[✓] 数据库已存在，跳过数据处理"
else
    echo "[!] 数据库不存在，需要先处理 PDF 数据"
    echo ""
    echo "    完整数据处理需要 5-10 分钟，是否现在处理？ [Y/n]"
    read -r answer
    if [ "$answer" != "n" ] && [ "$answer" != "N" ]; then
        echo ""
        echo "[*] ====== Step 1/6: PDF 文本提取 ======"
        (cd src/scripts && $PYTHON pdf_extractor.py "../../英语真题源文件PDF" "../data/extracted")
        echo "[✓] Step 1/6 完成"

        echo "[*] ====== Step 2/6: 题型解析 ======"
        (cd src/scripts && $PYTHON exam_parser.py)
        echo "[✓] Step 2/6 完成"

        echo "[*] ====== Step 3/6: 合并词修复 ======"
        (cd src/scripts && $PYTHON word_splitter.py) || echo "[警告] 合并词修复失败，继续..."

        echo "[*] ====== Step 4/6: 手动修正 ======"
        (cd src/scripts && $PYTHON manual_fix.py) || echo "[警告] 手动修正失败，继续..."

        echo "[*] ====== Step 5/6: 单词提取与词频统计 ======"
        (cd src/scripts && $PYTHON word_processor.py)
        echo "[✓] Step 5/6 完成"

        echo "[*] ====== Step 6/6: 数据库构建 ======"
        (cd src/scripts && $PYTHON freq_builder.py)
        echo "[✓] Step 6/6 完成"

        echo "[✓] 数据处理完成！"
    fi
fi

if [ ! -f "src/data/exam_words.db" ]; then
    echo "[错误] 数据库文件不存在，无法启动 WebApp"
    exit 1
fi

# ── 6. 启动 Flask WebApp ──
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║   🚀 正在启动 WebApp ...                                  ║"
echo "║                                                          ║"
echo "║   浏览器打开:  http://127.0.0.1:5000                       ║"
echo "║                                                          ║"
echo "║   按 Ctrl+C 可停止服务器                                   ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 启动 Flask（会自动打开浏览器）
$PYTHON src/webapp/app.py
