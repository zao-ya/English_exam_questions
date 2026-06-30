# 考研英语真题词频统计

对 **2000–2026 年考研英语真题** 进行词频统计，支持多维筛选、单词定位和 Excel 导出。

---

## 🚀 普通用户（直接下载 EXE，无需安装任何东西）

<div align="center">

### 👉 **[⬇ 点击下载桌面版](https://github.com/zao-ya/English_exam_questions/releases/latest)**

</div>

1. 下载 `考研英语词频统计.exe`
2. 双击运行，**无需安装 Python 或任何依赖**
3. 应用窗口自动打开，即可使用

> 仅支持 Windows 10/11。首次启动可能稍慢几秒（解压资源），后续秒开。

---

## 👨‍💻 开发者（从源码启动）

### 前置条件

- Python 3.9+（安装时勾选 `Add Python to PATH`）
- Git（用于下载项目）

### 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/zao-ya/English_exam_questions.git
cd English_exam_questions

# 2. Windows 用户 — 双击运行
tools\启动.bat

# 3. Mac / Linux 用户
chmod +x tools/start.sh
./tools/start.sh
```

脚本会自动完成：检查 Python → 安装依赖 → 下载 NLTK 数据 → 验证数据库 → 打开浏览器。

> 首次运行需联网（下载依赖和 NLTK 数据），约 2-3 分钟。之后每次启动仅几秒。

### 手动启动

如果一键脚本失败，可以手动操作：

```bash
# 安装依赖
pip install -r tools\requirements.txt

# 下载 NLTK 数据（仅首次）
python -c "import nltk; nltk.download('wordnet'); nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger'); nltk.download('averaged_perceptron_tagger_eng'); nltk.download('words'); nltk.download('maxent_ne_chunker'); nltk.download('maxent_ne_chunker_tab')"

# 启动 Web 版
python src\webapp\app.py
```

浏览器打开 `http://127.0.0.1:5000`。

### 启动桌面版（开发模式）

```bash
python src\desktop_app.py
```

或双击 `tools\启动桌面版.bat`（无命令行窗口）。

---

## 📸 功能概览

| 功能 | 说明 |
|------|------|
| 📊 **词频表格** | 7750 个单词，按总词频排序，分页浏览 |
| 🔍 **多维筛选** | 五级词频分级、年份、年份数、首次年份、题型 — 全部可组合 |
| 🃏 **单词详情** | 点击单词 → 卡片展示在所有真题中的出现位置，目标单词高亮 |
| 📥 **Excel 导出** | 当前筛选结果一键导出，带 AutoFilter |
| 🎯 **7 种题型** | 完形填空 / 阅读 / 翻译 / 七选五 / 排序 / 选标题 / 写作 |

### 常用操作

| 你想做的事 | 操作方法 |
|-----------|---------|
| 看高频词 | 勾选「总词频」→ L5（100次以上） |
| 找某年专属词 | 勾选「出现年份」中该年 + 「出现年份数」选 L1 |
| 查某个单词 | 在搜索框输入单词 |
| 看单词在哪出现过 | 点击表格中的单词（蓝色文字） |
| 导出当前筛选结果 | 点右上角 📥 导出 Excel |
| 清除所有筛选 | 点左下角「重置」或顶部的「✕ 清除全部」 |

---

## 📦 打包为独立 EXE

如果修改了代码想重新打包：

```bash
# Windows — 双击运行
tools\build_exe.bat

# 或手动
python -m PyInstaller --onefile --noconsole --name "考研英语词频统计" ^
  --add-data "src\webapp\templates;webapp\templates" ^
  --add-data "src\webapp\static;webapp\static" ^
  --add-data "src\data\exam_words.db;data" ^
  --collect-submodules flask ^
  --collect-submodules webview ^
  --hidden-import openpyxl ^
  --hidden-import clr ^
  src\desktop_app.py
```

打包后 `考研英语词频统计.exe` 生成在项目根目录，约 47 MB。

---

## 🔄 重新生成数据

如果你修改了 PDF 源文件或处理脚本，可以重建数据库。

**方法一（推荐）**：删除 `src\data\exam_words.db`，运行 `tools\启动.bat`，脚本会自动检测并引导重建。

**方法二（手动）**：

```bash
cd src\scripts

# Step 1: PDF 文本提取
python pdf_extractor.py "..\..\英语真题源文件PDF" "..\data\extracted"

# Step 2: 题型解析
python exam_parser.py

# Step 3: 合并词拆分
python word_splitter.py

# Step 4: 手动修正
python manual_fix.py

# Step 5: 单词提取与规范化
python word_processor.py

# Step 6: 构建数据库
python freq_builder.py
```

> 完整流水线约 5-10 分钟。

---

## 📁 项目结构

```
├── 考研英语词频统计.exe       # ★ 桌面版，双击即用
├── 英语真题源文件PDF/           # 原始 PDF（2000–2026，27 份）
│
├── src/                       # 源码和数据
│   ├── desktop_app.py         # 桌面版入口
│   ├── webapp/                # Flask 后端 + 前端
│   │   ├── app.py
│   │   ├── templates/index.html
│   │   └── static/
│   ├── scripts/               # 数据处理流水线
│   │   ├── pdf_extractor.py   # Step 1: PDF 文本提取
│   │   ├── exam_parser.py     # Step 2: 题型解析
│   │   ├── word_splitter.py   # Step 3: 合并词拆分
│   │   ├── manual_fix.py      # Step 4: 手动修正
│   │   ├── word_processor.py  # Step 5: 单词提取
│   │   ├── freq_builder.py    # Step 6: 数据库构建
│   │   └── audit_db.py        # 数据库校验
│   └── data/
│       └── exam_words.db      # SQLite 数据库（已包含完整数据）
│
├── tools/                     # 工具脚本
│   ├── 启动.bat               # Windows Web 版一键启动
│   ├── 启动桌面版.bat         # 桌面版快捷启动
│   ├── build_exe.bat          # PyInstaller 打包脚本
│   ├── start.sh               # Mac/Linux 一键启动
│   └── requirements.txt       # Python 依赖
│
└── docs/                      # 文档
    └── README.md
```

---

## ❓ 常见问题

**Q: 桌面版支持 Mac 吗？**
A: 目前 EXE 仅支持 Windows。Mac 用户请用 `tools/start.sh` 启动 Web 版。

**Q: 启动后网页空白？**
A: 数据库无效。删除 `src\data\exam_words.db` 后重新运行 `tools\启动.bat`，选择 Y 重建（5-10 分钟）。

**Q: 提示 `pip 不是内部命令`？**
A: 安装 Python 时没勾选 `Add Python to PATH`，重新安装并勾选即可。

**Q: NLTK 数据下载失败？**
A: 网络问题，脚本每次启动会自动重试。也可以手动挂代理后执行 NLTK 下载命令。

**Q: 数据库在哪，能自己查吗？**
A: `src\data\exam_words.db`，SQLite 格式，可用 [DB Browser for SQLite](https://sqlitebrowser.org/) 打开。

**Q: 怎么关闭应用？**
A: 桌面版直接关窗口。Web 版在命令行窗口按 `Ctrl+C`。

---

*统计范围：2000–2026 年考研英语（一）真题 · 27 年 · 7 种题型 · 7750 规范单词*
