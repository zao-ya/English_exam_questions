"""
题型解析器 v2
- 识别试卷结构（三种结构：A/B/C）
- 区分题型、正文/选项/题目
- 提取和清理句子
- 输出结构化数据
"""
import re
import json
import os
import nltk

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt')
    nltk.download('punkt_tab')

# ============================================================
# 区域类型常量
# ============================================================
SEC_PASSAGE = '正文'
SEC_OPTION = '选项'
SEC_QUESTION = '题目'

# ============================================================
# 句子切分
# ============================================================
def split_sentences(text):
    if not text or not text.strip():
        return []
    try:
        sentences = nltk.sent_tokenize(text)
    except Exception:
        sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 2]

# ============================================================
# 文本清理函数
# ============================================================
def clean_options_labels(text):
    """去掉选项前的 A. B. C. D. 等标记"""
    return re.sub(r'\b[A-H][.)]\s*', '', text).strip()

def clean_question_number(text):
    """去掉行首题号"""
    return re.sub(r'^\s*\d{1,2}[.)]\s*', '', text).strip()

def clean_cloze_blanks(text):
    """把完形填空挖空数字替换为标记，不去掉"""
    text = re.sub(r'\s+(\d{1,2})\s+', r' [BLANK\1] ', text)
    return text

def clean_line_numbers(text):
    """去掉行首独立的数字"""
    text = re.sub(r'^\d{1,2}\s+', '', text)
    return text.strip()

def is_direction_line(line):
    """判断是否为考试提示信息行"""
    line = line.strip()
    if not line:
        return False
    patterns = [
        r'^Directions?\s*[:：]',
        r'^For each numbered blank',
        r'^Choose the best',
        r'^Mark your answer',
        r'^Each of the passages below',
        r'^In the following (text|article|passage)',
        r'^You are going to read',
        r'^Read the following',
        r'^Write (a|an|your|an essay|a letter|about)',
        r'^Your (translation|letter|essay|answer)',
        r'^You should write',
        r'^Do not sign',
        r'^Do not write',
        r'^Translate the',
        r'^The following paragraphs',
        r'^\d{1,2}[.)]\s*Directions',
        r'^among all the worthy',
        r'^\d{1,2}[.)]\s*Read the following',
    ]
    for p in patterns:
        if re.match(p, line, re.IGNORECASE):
            return True
    # 包含分数标记的行（如 "(10 points)"）
    if re.search(r'\(\d+\s*points?\)', line, re.IGNORECASE):
        return True
    # 续行：以大写字母开头 + "or D" / "C or D" 等（选项标记的延续）
    if re.match(r'^[A-H],?\s+[A-H]\s+or\s+[A-H]', line):
        return True
    if re.match(r'^and\s+[A-H][.,]', line):
        return True
    return False


# ============================================================
# 主解析逻辑
# ============================================================
def parse_exam(text, year):
    """解析整份试卷，返回句子块列表"""
    blocks = []

    # ---- 第一步：找到 Section 边界 ----
    # 行首可能有数字前缀，如 "1 Section II" 或 "1SectionII" (PDF空格丢失)
    sec_pattern = re.compile(r'(\d+\s*)?Section\s*(I+)\b', re.IGNORECASE)

    sec_positions = []
    for m in sec_pattern.finditer(text):
        roman = m.group(2).upper()
        sec_positions.append((m.start(), roman))

    if not sec_positions:
        print(f'    WARNING: {year} 未找到任何 Section 标记')
        return blocks

    # 按位置排序，截取各 Section 文本
    sections = {}
    for i, (pos, roman) in enumerate(sec_positions):
        next_pos = sec_positions[i + 1][0] if i + 1 < len(sec_positions) else len(text)
        sections[roman] = text[pos:next_pos]

    # ---- 第二步：解析每个 Section ----
    if 'I' in sections:
        blocks.extend(parse_section1_cloze(sections['I'], year))
    if 'II' in sections:
        blocks.extend(parse_section2_reading(sections['II'], year))
    if 'III' in sections:
        blocks.extend(parse_section3_writing(sections['III'], year))

    return blocks


def parse_section1_cloze(text, year):
    """Section I: 完形填空"""
    blocks = []

    # 去除标题行和 Directions
    content_text = text
    dir_match = re.search(r'Directions?\s*[:：]', text, re.IGNORECASE)
    if dir_match:
        post_dir = text[dir_match.end():]
        lines = post_dir.split('\n')
        # 跳过是 Directions 描述的行（以特征词开头），其余全部保留
        body_lines = []
        for line in lines:
            if not is_direction_line(line):
                body_lines.append(line)
        content_text = '\n'.join(body_lines)
    else:
        # 没找到 Directions，从 Section 标题后开始
        first_line_end = text.find('\n')
        content_text = text[first_line_end + 1:] if first_line_end > 0 else text

    # 分离正文和选项
    # 选项格式: "1. A. xxx B. xxx C. xxx D. xxx"
    option_start_match = re.search(r'\n\s*\d{1,2}[.)]\s*[A-H][.)]', content_text)
    if option_start_match:
        option_start = option_start_match.start() + 1  # 跳过换行符
        passage = content_text[:option_start]
        options = content_text[option_start:]
    else:
        passage = content_text
        options = ''

    # 处理正文
    for sent in split_sentences(passage):
        sent = clean_line_numbers(clean_question_number(sent))
        if sent and len(sent) > 5 and not is_direction_line(sent):
            blocks.append({
                'year': year,
                'exam_type': '完形填空',
                'section': SEC_PASSAGE,
                'sentence': sent
            })

    # 处理选项 — 按题目切分
    if options:
        option_blocks_raw = re.split(r'\n(?=\s*\d{1,2}[.)]\s*[A-H][.)])', options)
        for opt_block in option_blocks_raw:
            opt_block = clean_question_number(opt_block)
            opt_block = clean_options_labels(opt_block)
            for sent in split_sentences(opt_block):
                sent = clean_line_numbers(sent)
                if sent and len(sent) > 3:
                    blocks.append({
                        'year': year,
                        'exam_type': '完形填空',
                        'section': SEC_OPTION,
                        'sentence': sent
                    })

    return blocks


def parse_section2_reading(text, year):
    """Section II: 阅读理解（包括 Part A/B/C）"""
    blocks = []

    # 寻找 Part 边界 (空格可能丢失)
    part_pattern = re.compile(r'(?:\d+\s*)?Part\s*([A-C])\b', re.IGNORECASE)
    part_positions = [(m.start(), m.group(1).upper()) for m in part_pattern.finditer(text)]

    # 找 Text 边界
    text_pattern = re.compile(r'(?:\d+\s+)?Text\s*(\d+)', re.IGNORECASE)
    text_positions = [(m.start(), int(m.group(1))) for m in text_pattern.finditer(text)]

    # 确定各 Part 的文本范围
    if not part_positions:
        # 无 Part 标记，全量处理
        part_texts = {'A': text}
    else:
        part_texts = {}
        for i, (pos, label) in enumerate(part_positions):
            next_pos = part_positions[i + 1][0] if i + 1 < len(part_positions) else len(text)
            part_texts[label] = text[pos:next_pos]

    # ---- Part A: 阅读 ----
    if 'A' in part_texts:
        blocks.extend(parse_reading_part_a(part_texts['A'], year))

    # ---- Part B ----
    if 'B' in part_texts:
        part_b_text = part_texts['B']
        if year >= 2005:
            # 2005+ Part B 可能是 7选5/排序/选标题
            # 通过标题判断具体类型
            if re.search(r'七选五|7\s*选\s*5|seven.*choose.*five|7\s*choose\s*5', part_b_text, re.IGNORECASE):
                part_b_type = '7选5'
            elif re.search(r'排序|ordering|order|sequence', part_b_text, re.IGNORECASE):
                part_b_type = '排序'
            elif re.search(r'标题|title|heading|subheading', part_b_text, re.IGNORECASE):
                part_b_type = '选标题'
            else:
                part_b_type = '7选5'  # 默认
            blocks.extend(parse_reading_special(part_b_text, year, part_b_type))
        else:
            # 2000-2004: Part B 是翻译
            blocks.extend(parse_translation(part_b_text, year))

    # ---- Part C: 2005+ 翻译 ----
    if 'C' in part_texts and year >= 2005:
        blocks.extend(parse_translation(part_texts['C'], year))

    return blocks


def parse_reading_part_a(text, year):
    """解析阅读 Part A: Text 1-4/5 的文章和题目"""
    blocks = []

    text_positions = [(m.start(), int(m.group(1)))
                      for m in re.finditer(r'(?:\d+\s+)?Text\s*(\d+)', text, re.IGNORECASE)]

    if not text_positions:
        # 没有 Text 标记，整段当阅读正文处理
        for sent in split_sentences(text):
            sent = clean_question_number(clean_line_numbers(sent))
            if sent and len(sent) > 5 and not is_direction_line(sent):
                blocks.append({
                    'year': year, 'exam_type': '阅读',
                    'section': SEC_PASSAGE, 'sentence': sent
                })
        return blocks

    for i, (pos, tnum) in enumerate(text_positions):
        next_pos = text_positions[i + 1][0] if i + 1 < len(text_positions) else len(text)
        passage = text[pos:next_pos]

        # 跳过 "Text N" 标题行
        first_nl = passage.find('\n')
        if first_nl > 0:
            passage = passage[first_nl + 1:]

        # 分离正文和题目
        # 题目以数字开头：如 "11. The U.S. achieved..."
        q_match = re.search(r'\n\s*\d{1,2}[.)]\s+[A-Z]', passage[100:])
        if q_match:
            q_start = q_match.start() + 100
            body = passage[:q_start]
            questions = passage[q_start:]
        else:
            body = passage
            questions = ''

        # 正文
        for sent in split_sentences(body):
            sent = clean_line_numbers(clean_question_number(sent))
            if sent and len(sent) > 5 and not is_direction_line(sent):
                blocks.append({
                    'year': year, 'exam_type': '阅读',
                    'section': SEC_PASSAGE, 'sentence': sent
                })

        # 题目和选项
        if questions:
            q_blocks = re.split(r'\n(?=\s*\d{1,2}[.)]\s+[A-Z])', questions)
            for qb in q_blocks:
                qb = clean_question_number(clean_options_labels(qb))
                for sent in split_sentences(qb):
                    sent = clean_line_numbers(sent)
                    if sent and len(sent) > 3:
                        blocks.append({
                            'year': year, 'exam_type': '阅读',
                            'section': SEC_OPTION, 'sentence': sent
                        })

    return blocks


def parse_reading_special(text, year, exam_type):
    """解析 Part B 特殊题型：7选5/排序/选标题"""
    blocks = []

    # 找正文和选项的边界
    opt_match = re.search(r'\n\s*[A-H][.)]\s', text[200:])
    if opt_match:
        opt_start = opt_match.start() + 200
        body = text[:opt_start]
        opts = text[opt_start:]
    else:
        body = text
        opts = ''

    # 正文
    for sent in split_sentences(body):
        sent = clean_question_number(clean_line_numbers(sent))
        if sent and len(sent) > 5 and not is_direction_line(sent) \
           and not re.match(r'Part\s+[A-C]\b', sent, re.IGNORECASE):
            blocks.append({
                'year': year, 'exam_type': exam_type,
                'section': SEC_PASSAGE, 'sentence': sent
            })

    # 选项
    if opts:
        opt_items = re.split(r'\n(?=\s*[A-H][.)])', opts)
        for opt_item in opt_items:
            opt_item = clean_options_labels(opt_item)
            for sent in split_sentences(opt_item):
                sent = clean_line_numbers(sent)
                if sent and len(sent) > 3:
                    blocks.append({
                        'year': year, 'exam_type': exam_type,
                        'section': SEC_OPTION, 'sentence': sent
                    })

    return blocks


def parse_translation(text, year):
    """解析翻译部分"""
    blocks = []

    for sent in split_sentences(text):
        sent = clean_question_number(clean_line_numbers(sent))
        if sent and len(sent) > 5 and not is_direction_line(sent) \
           and not re.match(r'Part\s+[A-C]\b', sent, re.IGNORECASE):
            # 判断是题目还是正文
            # 翻译题目通常以数字开头（翻译题号）
            section_type = SEC_PASSAGE
            blocks.append({
                'year': year, 'exam_type': '翻译',
                'section': section_type, 'sentence': sent
            })

    return blocks


def parse_section3_writing(text, year):
    """Section III: 写作"""
    blocks = []

    # 找 Part A/B 边界（2005+）
    part_positions = [(m.start(), m.group(1).upper())
                      for m in re.finditer(r'Part\s+([AB])\b', text, re.IGNORECASE)]

    if part_positions:
        for i, (pos, label) in enumerate(part_positions):
            next_pos = part_positions[i + 1][0] if i + 1 < len(part_positions) else len(text)
            part_text = text[pos:next_pos]

            # 找 Directions 之后的内容
            dir_m = re.search(r'Directions?\s*[:：]', part_text, re.IGNORECASE)
            if dir_m:
                part_text = part_text[dir_m.end():]

            # 写作部分：Directions 之后的文本就是题目内容，不过滤 is_direction_line
            for sent in split_sentences(part_text):
                sent = clean_question_number(clean_line_numbers(sent))
                if sent and len(sent) > 5 \
                   and not re.match(r'Part\s+[AB]\b', sent, re.IGNORECASE) \
                   and not re.match(r'Section\s+III', sent, re.IGNORECASE):
                    blocks.append({
                        'year': year, 'exam_type': '写作',
                        'section': SEC_PASSAGE, 'sentence': sent
                    })
    else:
        # 2000-2004 写作：没有 Part A/B
        dir_m = re.search(r'Directions?\s*[:：]', text, re.IGNORECASE)
        if dir_m:
            content = text[dir_m.end():]
        else:
            content = text

        # 写作部分：Directions 之后的文本就是题目内容，不过滤 is_direction_line
        for sent in split_sentences(content):
            sent = clean_question_number(clean_line_numbers(sent))
            if sent and len(sent) > 5:
                blocks.append({
                    'year': year, 'exam_type': '写作',
                    'section': SEC_PASSAGE, 'sentence': sent
                })

    return blocks


# ============================================================
# 主入口
# ============================================================
def is_garbage_sentence(sent):
    """判断一个句子是否应该被丢弃"""
    s = sent.strip()
    if not s or len(s) < 3:
        return True
    # Part 标题行
    if re.match(r'^Part\s*[A-C]\b', s, re.IGNORECASE):
        return True
    # Directions 标题
    if re.match(r'^Directions?\s*[:：]', s, re.IGNORECASE):
        return True
    # "Read the following" 之类的 directions（考虑空格丢失）
    if re.match(r'^Read\s*the\s*follow(ing|wing)\b', s, re.IGNORECASE):
        return True
    # "Mark your answer" 之类的 directions
    if re.match(r'^Mark\s*your\s*answers?\b', s, re.IGNORECASE):
        return True
    # 水印 URL
    if re.search(r'burningvocabulary', s, re.IGNORECASE):
        return True
    # 仅剩标点符号或数字
    if re.match(r'^[\d\s.,;:!?\'\"\-—]+$', s):
        return True
    # "Your translation/letter/essay" (非写作部分的方向指示)
    if re.match(r'^Your\s+(translation|letter|essay)\b', s, re.IGNORECASE):
        return True
    return False


def parse_all_years(extracted_texts):
    """解析所有年份的试卷"""
    all_blocks = []
    for year in sorted(extracted_texts.keys()):
        text = extracted_texts[year]
        blocks = parse_exam(text, year)
        # 过滤垃圾句子 + 去重
        seen = set()
        unique = []
        for b in blocks:
            if is_garbage_sentence(b['sentence']):
                continue
            key = (b['year'], b['exam_type'], b['section'], b['sentence'][:100])
            if key not in seen:
                seen.add(key)
                unique.append(b)
        all_blocks.extend(unique)
        print(f'  {year}: {len(unique)} 个句子块')
    return all_blocks


if __name__ == '__main__':
    import sys, glob
    input_dir = sys.argv[1] if len(sys.argv) > 1 else '../data/extracted'
    output_file = sys.argv[2] if len(sys.argv) > 2 else '../data/parsed_blocks.json'

    extracted_texts = {}
    for f in sorted(glob.glob(f'{input_dir}/*_extracted.txt')):
        year = int(re.search(r'(\d{4})', f).group(1))
        with open(f, 'r', encoding='utf-8') as fh:
            extracted_texts[year] = fh.read()

    blocks = parse_all_years(extracted_texts)

    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(blocks, f, ensure_ascii=False, indent=2)
    print(f'\n总计 {len(blocks)} 个句子块 -> {output_file}')
