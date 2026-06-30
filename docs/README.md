# 考研英语真题词频统计 WebApp

一个本地运行的 Web 应用，对 **2000–2026 年考研英语真题** 进行词频统计，支持多维筛选、单词定位和 Excel 导出。

---

## ⚡ 一键启动

> 项目已包含完整数据库和自动安装脚本，**双击 `启动.bat` 即可使用**，无需任何手动配置。

### Windows 用户

1. 下载并解压项目
2. 双击 **`启动.bat`**
3. 脚本会自动完成以下工作：
   - ✅ 检查 Python 环境
   - ✅ 自动安装依赖库（`pip install`）
   - ✅ 自动下载 NLTK 数据（首次约 1-2 分钟）
   - ✅ 验证数据库完整性（异常数据库自动提示重建）
   - ✅ 启动 WebApp 并打开浏览器
4. 🎉 开始使用！

> **注意**：首次运行会自动安装依赖和下载 NLTK 数据，需要联网，请耐心等待 2-3 分钟。之后每次启动只需几秒。

### Mac / Linux 用户

```bash
chmod +x start.sh
./start.sh
```

---

## 📸 功能概览

| 功能 | 说明 |
|------|------|
| 📊 **词频表格** | 7750 个单词，按总词频排序，分页浏览 |
| 🔍 **多维筛选** | 五级词频分级、年份、年份数、首次年份、题型 — 全部可组合 |
| 🃏 **单词详情** | 点击单词 → 卡片展示在所有真题中的出现位置，单词高亮 |
| 📥 **Excel 导出** | 当前筛选结果一键导出，带 AutoFilter |
| 🎯 **7 种题型** | 完形填空 / 阅读 / 翻译 / 七选五 / 排序 / 选标题 / 写作 |

---

## 🖥️ 手动部署（如果一键启动失败）

### 第一步：安装 Python

1. 打开 [python.org](https://www.python.org/downloads/)
2. 点击黄色 **Download Python** 按钮，运行安装包
3. ⚠️ **重要**：安装界面**勾选 `Add Python to PATH`**

### 第二步：安装依赖

打开项目文件夹，在地址栏输入 `cmd` 回车，执行：

```bash
pip install -r requirements.txt
```

### 第三步：下载 NLTK 数据

```bash
python -c "import nltk; nltk.download('wordnet'); nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger'); nltk.download('averaged_perceptron_tagger_eng'); nltk.download('words'); nltk.download('maxent_ne_chunker'); nltk.download('maxent_ne_chunker_tab')"
```

### 第四步：启动应用

```bash
python webapp\app.py
```

浏览器打开 `http://127.0.0.1:5000` 即可使用。

---

## 🚀 快速上手

### 常用操作

| 你想做的事 | 操作方法 |
|-----------|---------|
| 看高频词 | 勾选 L5（100次以上） |
| 找某年专属词 | 勾选"出现年份"中该年 + "出现年份数"选 L1 |
| 查某个单词 | 在搜索框输入单词，回车 |
| 看单词在哪出现过 | 点击表格中的蓝色单词 |
| 导出当前结果 | 点右上角 📥 导出 Excel |
| 清除所有筛选 | 点"重置"按钮 |

---

## 🔄 重新生成数据

如果你修改了 PDF 源文件或脚本，可以重新跑数据处理流水线。

**方法一**：删除 `data\exam_words.db`，然后重新运行 `启动.bat`，脚本会自动检测并引导你重建数据。

**方法二**：手动执行各步骤：

```bash
cd scripts

# Step 1: 从 PDF 提取文本
python pdf_extractor.py "..\英语真题源文件PDF" "..\data\extracted"

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

---

## 📁 项目结构

```
├── 英语真题源文件PDF/       # 原始 PDF（2000-2026，27份）
├── scripts/                # 数据处理脚本
│   ├── pdf_extractor.py    # PDF 文本提取
│   ├── exam_parser.py      # 题型解析 + 句子提取
│   ├── word_splitter.py    # 合并词拆分
│   ├── manual_fix.py       # 手动修正规则
│   ├── word_processor.py   # 单词提取 + 规范化
│   ├── freq_builder.py     # 数据库构建
│   └── irregular_forms.json # 不规则形式词典
├── data/
│   ├── exam_words.db       # SQLite 数据库（已包含完整数据）
│   └── word_freq_export.txt # 分级词频导出
├── webapp/                 # Web 应用
│   ├── app.py              # Flask 后端
│   ├── templates/
│   │   └── index.html      # 前端页面
│   └── static/
├── 启动.bat                # Windows 一键启动脚本
├── start.sh                # Mac/Linux 启动脚本
├── requirements.txt        # Python 依赖列表
└── README.md
```

---

## ❓ 常见问题

**Q: 启动后网页是空白的？**
A: 这说明数据库无效。`启动.bat` 会自动检测并提示重建，选择 Y 等待 5-10 分钟即可。

**Q: 提示 `pip 不是内部命令`？**
A: 安装 Python 时没有勾选 `Add Python to PATH`。重新安装 Python 并勾选即可。

**Q: NLTK 数据下载失败？**
A: 网络问题，可以稍后重试。`启动.bat` 每次都会检查并自动补下。

**Q: 数据库在哪？**
A: `data/exam_words.db`，可以用任何 SQLite 工具打开查看。

**Q: 怎么关闭？**
A: 在黑色窗口按 `Ctrl+C`，然后关掉窗口。

---

*统计范围：2000–2026 年考研英语（一）真题 · 27 年 · 7 种题型 · 7750 规范单词*
