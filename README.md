# 考研英语真题词频统计 WebApp

一个本地运行的 Web 应用，对 **2000–2026 年考研英语真题** 进行词频统计，支持多维筛选、单词定位和 Excel 导出。

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

## 🖥️ 如何部署到本地

> 全程不需要编程知识，跟着步骤走即可。预计 5 分钟。

### 第一步：下载项目

点击本页面右上角绿色的 **`<> Code`** 按钮 → **Download ZIP**，解压到你想放的文件夹。

![download-zip](https://docs.github.com/assets/cb-20363/images/help/repository/code-button.png)

### 第二步：安装 Python

如果你的电脑还没有 Python：

1. 打开 [python.org](https://www.python.org/downloads/)
2. 点击黄色 **Download Python** 按钮
3. 运行下载的安装包
4. ⚠️ **重要**：安装界面**勾选 `Add Python to PATH`**（底部复选框），然后点 Install

### 第三步：安装依赖

打开解压后的项目文件夹，在地址栏输入 `cmd` 回车：

![地址栏输入cmd](https://www.top-password.com/blog/wp-content/uploads/2019/01/open-command-window-here.png)

在弹出的黑色窗口（命令提示符）中，输入以下命令并回车：

```bash
pip install pdfplumber nltk pandas flask openpyxl
```

等待出现 `Successfully installed` 字样。

### 第四步：下载 NLTK 数据（只需一次）

继续在黑色窗口中输入：

```bash
python -c "import nltk; nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger'); nltk.download('maxent_ne_chunker'); nltk.download('words'); nltk.download('punkt'); nltk.download('punkt_tab')"
```

等待出现 `Done` 字样。

### 第五步：启动应用

在黑色窗口中输入：

```bash
cd /d D:\你的项目文件夹\webapp
python app.py
```

看到 `Running on http://127.0.0.1:5000` 就表示启动成功了。

### 第六步：打开浏览器

打开浏览器（Chrome/Edge 等），在地址栏输入：

```
http://127.0.0.1:5000
```

🎉 搞定！现在就可以使用了。

---

## 🚀 快速上手

### 界面说明

```
┌──────────────────────────────────────────────────┐
│  考研英语真题词频统计               [📥 导出]    │
├────────────┬─────────────────────────────────────┤
│  统计概览   │                                     │
│  8265 单词  │   单词表格（点击可查看详情）          │
│  74989 次   │                                     │
│            │                                     │
│ 🔍 搜索…   │                                     │
│            │                                     │
│ 总词频      │                                     │
│ ☐ L1 仅1次  │                                     │
│ ☑ L2 2-5次  │                                     │
│ ☑ L3 6-20次 │                                     │
│ ...        │                                     │
│            │                                     │
│ 出现年份    │                                     │
│ 全选 00s…  │                                     │
│ ☐ 2000     │                                     │
│ ☑ 2001     │                                     │
│ ...        │                                     │
│            │                                     │
│ [重置]     │                                     │
└────────────┴─────────────────────────────────────┘
```

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

如果你修改了 PDF 源文件或脚本，可以重新跑数据处理流水线：

```bash
cd scripts

# Step 1: 从 PDF 提取文本
python pdf_extractor.py ../英语真题源文件PDF ../data/extracted

# Step 2: 解析题型和句子
python exam_parser.py ../data/extracted ../data/parsed_blocks.json

# Step 3: 拆分合并词
python word_splitter.py ../data/parsed_blocks.json ../data/parsed_blocks_fixed.json

# Step 4: 手动修正
python manual_fix.py

# Step 5: 单词提取与规范化
python word_processor.py --input ../data/parsed_blocks_final.json

# Step 6: 构建数据库
python freq_builder.py ../data/word_stats_final.json ../data/occurrences_final.json ../data/exam_words.db
```

---

## 📁 项目结构

```
├── 英语真题源文件PDF/      # 原始 PDF（2000-2026，27份）
├── scripts/                # 数据处理脚本
│   ├── pdf_extractor.py    # PDF 文本提取
│   ├── exam_parser.py      # 题型解析 + 句子提取
│   ├── word_splitter.py    # 合并词拆分
│   ├── manual_fix.py       # 手动修正规则
│   ├── word_processor.py   # 单词提取 + 规范化
│   ├── freq_builder.py     # 数据库构建
│   └── irregular_forms.json # 不规则形式词典
├── data/
│   ├── exam_words.db       # SQLite 数据库（生成物）
│   └── word_freq_export.txt # 分级词频导出
├── webapp/                 # Web 应用
│   ├── app.py              # Flask 后端（启动这个文件）
│   ├── templates/
│   │   └── index.html      # 前端页面
│   └── static/
│       ├── css/style.css   # 样式
│       └── js/app.js       # 前端逻辑
└── README.md               # 本教程
```

---

## ❓ 常见问题

**Q: 打开网页是空白的？**
A: 确认黑色窗口没关，且显示 `Running on http://127.0.0.1:5000`。

**Q: 提示 `pip 不是内部命令`？**
A: 安装 Python 时没有勾选 `Add Python to PATH`。重新安装并勾选即可。

**Q: 数据库在哪？**
A: `data/exam_words.db`，可以用任何 SQLite 工具打开查看。

**Q: 怎么关闭？**
A: 在黑色窗口按 `Ctrl+C`，然后关掉窗口。

---

*统计范围：2000–2026 年考研英语（一）真题 · 27 年 · 7 种题型 · 7750 规范单词*
