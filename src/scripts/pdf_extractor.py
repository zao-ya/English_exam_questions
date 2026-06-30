"""
PDF 文本提取器
- 从 PDF 中提取原始文本
- 过滤水印、页码等全局忽略项
- 输出清洗后的文本供 exam_parser 使用
"""

import pdfplumber
import re
import json
import os
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    """逐页提取 PDF 文本"""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text)
    return '\n'.join(pages_text)


def clean_text(text):
    """
    全局清理：
    - 去掉水印
    - 去掉独立页码行
    - 修复常见编码问题
    """
    # 去水印 (.com 和 .cn 两种)
    text = re.sub(r'https?://zhenti\.burningvocabulary\.(?:com|cn)\s*', '', text)
    # 去掉单独的页码行（纯数字，前后有空行或位于行首/行尾附近）
    text = re.sub(r'\n\s*\d{1,3}\s*\n', '\n', text)
    # 修复单引号编码问题
    text = text.replace('’', "'")  # right single quote
    text = text.replace('‘', "'")  # left single quote
    text = text.replace('“', '"')  # left double quote
    text = text.replace('”', '"')  # right double quote
    text = text.replace('–', '-')  # en dash
    text = text.replace('—', '--') # em dash
    # 修复空格问题
    text = re.sub(r' {2,}', ' ', text)
    # 去掉多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_all_pdfs(pdf_dir, output_dir=None):
    """
    处理所有 PDF 文件
    返回 dict: {year: cleaned_text}
    """
    pdf_dir = Path(pdf_dir)
    results = {}

    pdf_files = sorted(pdf_dir.glob('*.pdf'))
    print(f'找到 {len(pdf_files)} 个 PDF 文件')

    for pdf_path in pdf_files:
        year_match = re.match(r'(\d{4})', pdf_path.stem)
        if not year_match:
            print(f'  跳过无法识别年份的文件: {pdf_path.name}')
            continue
        year = int(year_match.group(1))
        print(f'处理 {year} 年: {pdf_path.name} ...', end=' ')

        raw_text = extract_text_from_pdf(str(pdf_path))
        cleaned_text = clean_text(raw_text)
        results[year] = cleaned_text

        print(f'({len(cleaned_text)} 字符)')

        # 保存中间结果
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f'{year}_extracted.txt')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)

    return results


if __name__ == '__main__':
    import sys
    pdf_dir = sys.argv[1] if len(sys.argv) > 1 else '../英语真题源文件PDF'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '../data/extracted'
    results = extract_all_pdfs(pdf_dir, output_dir)
    print(f'\n处理完成，共 {len(results)} 个年份')
