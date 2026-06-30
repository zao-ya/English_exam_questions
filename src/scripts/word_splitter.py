"""
长单词拆分修复器 v2
- 检测因 PDF 空格丢失导致的长"单词"（多词合并）
- 使用英文基础词典 + 词形还原动态规划拆分
- 修复句子后重新输出 parsed_blocks
"""

import re
import json
import sys
import os


# ============================================================
# 1. 词典构建（仅原型）
# ============================================================

def build_word_dict():
    """构建英文基础单词词典"""
    from nltk.corpus import words as nltk_words
    word_set = set(w.lower() for w in nltk_words.words() if len(w) > 1)
    extra = {'a','an','the','is','am','are','was','were','be','been',
             'has','had','have','do','does','did','can','could','will',
             'would','shall','should','may','might','must','not','no',
             'yes','in','on','at','to','for','of','with','by','from',
             'up','down','out','off','over','under','into','onto',
             'and','or','but','if','so','as','than','that','this',
             'these','those','it','its','he','she','they','we','you',
             'me','him','her','us','them','my','his','our','your','their',
             'more','most','some','any','all','each','every','both','few',
             'many','much','such','very','too','also','just','now','then',
             'here','there','when','where','why','how','what','which',
             'who','whom','whose','one','two'}
    word_set.update(extra)
    return word_set


def get_lemmatizer():
    """延迟加载 lemmatizer（只初始化一次）"""
    if not hasattr(get_lemmatizer, '_instance'):
        from nltk.stem import WordNetLemmatizer
        get_lemmatizer._instance = WordNetLemmatizer()
    return get_lemmatizer._instance


def is_valid_word(candidate, base_dict):
    """
    检查 candidate 是否为合法英文单词：
    1. 直接在词典中
    2. 词形还原后在词典中（处理 prevented→prevent 等变形）
    """
    c = candidate.lower()
    if c in base_dict:
        return True
    lemmatizer = get_lemmatizer()
    for pos in ['v', 'n', 'a', 'r']:
        lemma = lemmatizer.lemmatize(c, pos)
        if lemma != c and lemma in base_dict:
            return True
    return False


# ============================================================
# 2. 单词拆分（动态规划）
# ============================================================

def split_merged_word(merged, base_dict, min_len=2):
    """
    使用动态规划将合并词拆分为已知英文单词序列
    返回拆分后的字符串（单词间空格分隔），或 None（无法拆分）
    """
    merged = merged.lower()
    n = len(merged)
    if n < min_len:
        return None

    # dp[i] = (word_list, score)  从位置 i 开始的拆分方案
    # score: 越小越好 = 单词数 - sum(单词长度)*0.001
    dp = [None] * (n + 1)
    dp[n] = ([], 0.0)

    for i in range(n - 1, -1, -1):
        best = None
        max_j = min(n, i + 22)  # 最大单词长度 21
        for j in range(i + min_len, max_j + 1):
            word = merged[i:j]
            if is_valid_word(word, base_dict):
                if dp[j] is not None:
                    rest_words, rest_score = dp[j]
                    score = rest_score + 1.0 - len(word) * 0.001
                    if best is None or score < best[1]:
                        best = ([word] + rest_words, score)
        dp[i] = best

    if dp[0] is None:
        return None

    words, _ = dp[0]
    return ' '.join(words)


def find_and_fix_merged_words(sentence, base_dict, threshold=12):
    """在句子中查找长度超过 threshold 的连续字母序列并尝试拆分"""
    pattern = re.compile(r'\b[a-zA-Z]{%d,}\b' % (threshold + 1))

    def replacer(m):
        merged = m.group()
        fixed = split_merged_word(merged, base_dict)
        if fixed is not None and fixed != merged:
            return fixed
        return merged

    return pattern.sub(replacer, sentence)


def fix_blocks(blocks, base_dict, threshold=12):
    """修复所有句子块中的合并词"""
    fixed_count = 0
    total_checked = 0

    for block in blocks:
        original = block['sentence']
        long_words = re.findall(r'\b[a-zA-Z]{%d,}\b' % (threshold + 1), original)
        if long_words:
            total_checked += 1
            fixed = find_and_fix_merged_words(original, base_dict, threshold)
            if fixed != original:
                block['sentence'] = fixed
                fixed_count += 1

    print(f'  检查句子: {total_checked}, 修复句子: {fixed_count}')
    return blocks


# ============================================================
# 3. 主入口
# ============================================================
def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else '../data/parsed_blocks.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else '../data/parsed_blocks_fixed.json'

    print('构建英文基础词典...')
    base_dict = build_word_dict()
    print(f'  词典大小: {len(base_dict)}')

    print(f'\n加载句子块: {input_file}')
    with open(input_file, 'r', encoding='utf-8') as f:
        blocks = json.load(f)
    print(f'  句子块数: {len(blocks)}')

    # 测试
    test_words = [
        'preventedmarketparticipantsfromcompetingonanevenplaying',
        'showthetriumphoftheanimalrightsmovement',
        'spokespersonforwaterstonesseemtoconvey',
        'areinfluencedandtheninfluenceothers',
        'describethedrawingbriefly',
        'whichofthefollowing',
        'canbeinferredfrom',
        'wouldbethebesttitleforthetext',
    ]
    print('\n拆分测试:')
    for tw in test_words:
        result = split_merged_word(tw, base_dict)
        print(f'  {tw[:70]}')
        print(f'    -> {result}')
        print()

    # 修复
    print('修复句子块...')
    blocks = fix_blocks(blocks, base_dict, threshold=12)

    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(blocks, f, ensure_ascii=False, indent=2)
    print(f'\n修复完成 -> {output_file}')


if __name__ == '__main__':
    main()
