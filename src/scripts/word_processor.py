"""
单词提取与规范化处理器
- 从句子中提取英文单词
- 过滤短词、缩写、专有名词
- 词形还原（常规变化→原型，不规则变化→独立条目）
- 记录每个单词的出现位置
"""

import re
import json
import os
import sys
from collections import Counter

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import words as nltk_words
from nltk import pos_tag, word_tokenize

# ============================================================
# 1. 加载资源
# ============================================================

def load_irregular_forms(path):
    """加载不规则形式词典"""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 合并所有类别
    all_irregular = set()
    for category in ['irregular_verbs_past', 'irregular_verbs_past_participle',
                     'irregular_nouns', 'irregular_comparative', 'irregular_superlative']:
        all_irregular.update(w.lower() for w in data.get(category, []))
    return all_irregular


def load_proper_noun_dict():
    """加载常见专有名词列表"""
    # 常见人名、地名、机构名等
    proper_nouns = {
        # 常见人名
        'john', 'mary', 'james', 'robert', 'smith', 'william', 'david', 'michael',
        'thomas', 'richard', 'charles', 'paul', 'mark', 'george', 'steven', 'joseph',
        'linda', 'susan', 'sandra', 'helen', 'barbara', 'karen', 'lisa', 'nancy',
        'betty', 'margaret', 'dorothy', 'patricia', 'elizabeth', 'jennifer',
        'peter', 'henry', 'andrew', 'stephen', 'martin', 'kevin', 'brian',
        'edward', 'donald', 'ronald', 'anthony', 'frank', 'patrick', 'raymond',
        'jack', 'dennis', 'jerry', 'larry', 'gary', 'timothy', 'jose', 'douglas',
        'simon', 'daniel', 'matthew', 'jason', 'steve', 'jim', 'bob', 'tom',
        'scott', 'eric', 'alan', 'philip', 'chris', 'mike', 'jeff', 'ryan',
        'nicholas', 'jonathan', 'bruce', 'russell', 'lawrence', 'carl', 'walter',
        'alex', 'ted', 'jane', 'sarah', 'laura', 'anna', 'emma', 'alice',
        'catherine', 'rebecca', 'rachel', 'kate', 'judy', 'lucy', 'anne',
        # 常见姓氏
        'washington', 'lincoln', 'kennedy', 'roosevelt', 'churchill', 'thatcher',
        'reagan', 'clinton', 'obama', 'trump', 'biden', 'bush', 'nixon',
        'einstein', 'darwin', 'newton', 'shakespeare', 'dickens', 'hemingway',
        'napoleon', 'hitler', 'mandela', 'gandhi', 'lenin', 'stalin',
        'socrates', 'plato', 'aristotle', 'aristotles', 'beethoven', 'mozart',
        'picasso', 'van', 'gogh', 'dyson', 'hawking', 'feynman', 'tesla',
        'edison', 'ford', 'gates', 'jobs', 'musk', 'bezos', 'zuckerberg',
        # 地名
        'america', 'american', 'britain', 'british', 'england', 'london',
        'france', 'paris', 'germany', 'berlin', 'japan', 'tokyo', 'china',
        'beijing', 'shanghai', 'india', 'canada', 'australia', 'europe',
        'european', 'asia', 'africa', 'york', 'yorkshire', 'california',
        'texas', 'florida', 'chicago', 'boston', 'wales', 'scotland',
        'ireland', 'irish', 'dutch', 'sweden', 'norway', 'denmark', 'russia',
        'ukraine', 'poland', 'italy', 'spain', 'greece', 'rome', 'venice',
        'moscow', 'kremlin', 'pentagon', 'hollywood', 'broadway', 'manhattan',
        'brooklyn', 'harvard', 'yale', 'stanford', 'princeton', 'oxford',
        'cambridge', 'mit', 'cornell', 'berkeley',
        # 机构/品牌
        'microsoft', 'google', 'apple', 'facebook', 'amazon', 'twitter',
        'intel', 'ibm', 'nasa', 'fbi', 'cia', 'un', 'unesco', 'nato',
        'wto', 'who', 'imf', 'coca', 'cola', 'nike', 'adidas', 'sony',
        'samsung', 'toyota', 'honda', 'boeing', 'airbus', 'mcdonald',
        'starbucks', 'walmart', 'exxon', 'shell', 'chevron', 'ford',
        'general', 'electric', 'volkswagen', 'siemens', 'dell', 'hp',
        'nokia', 'motorola', 'verizon', 'at&t', 't-mobile', 'vodafone',
        # 月份（通常首字母大写）
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        # 星期
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
        'saturday', 'sunday',
        # 其他专有名词
        'god', 'bible', 'christmas', 'easter', 'thanksgiving',
        'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'sir', 'madam',
        'zenith', 'lg', 'microsoft', 'netscape', 'yahoo',
        # 常见国家/人
        'english', 'french', 'german', 'spanish', 'italian', 'russian',
        'japanese', 'chinese', 'korean', 'indian', 'canadian', 'australian',
        'african', 'asian', 'latin', 'arab', 'jewish', 'christian',
        'muslim', 'catholic', 'protestant', 'buddhist', 'hindu'
    }
    return proper_nouns


# ============================================================
# 2. 单词提取和过滤
# ============================================================

# 匹配纯英文单词（至少2个字母，不含数字和特殊符号）
WORD_RE = re.compile(r'\b[a-zA-Z]+\b')
# 匹配缩写形式：don't, can't, it's, they're 等
CONTRACTION_RE = re.compile(r"\b[a-zA-Z]+'[a-zA-Z]+\b", re.IGNORECASE)


def remove_contractions(text):
    """从文本中移除所有缩写形式"""
    return CONTRACTION_RE.sub('', text)


def extract_words_from_sentence(sentence):
    """从句子中提取英文单词及其位置（已预先移除缩写）"""
    words = []
    for m in WORD_RE.finditer(sentence):
        word = m.group()
        words.append({
            'surface': word,
            'lower': word.lower(),
            'start': m.start(),
            'length': len(word)
        })
    return words


def is_contraction(word):
    """判断是否为缩写形式（如 don't, can't）"""
    # 含撇号
    if "'" in word.lower():
        return True
    # 常见缩写词（不含撇号的特殊情况）
    # 如 gonna, wanna, gotta — 按用户要求，这些正常拼写的算作单词
    return False


def is_too_short(word_lower):
    """长度小于3的单词"""
    return len(word_lower) < 3


# ============================================================
# 3. 词形还原
# ============================================================

def normalize_word(word_lower, lemmatizer, irregular_set):
    """
    词形规范化：
    - 常规变化 → 还原到词元（通过 WordNet Lemmatizer）
    - 不规则变化 → 保留原形
    """
    # 如果不规则形式集合中包含此词 → 保留原形
    if word_lower in irregular_set:
        return word_lower

    # 尝试名词还原
    lemma_n = lemmatizer.lemmatize(word_lower, 'n')
    # 尝试动词还原
    lemma_v = lemmatizer.lemmatize(word_lower, 'v')
    # 尝试形容词还原
    lemma_a = lemmatizer.lemmatize(word_lower, 'a')

    # 优先选择与原词不同的最短还原结果（说明是变形）
    candidates = []
    if lemma_n != word_lower:
        candidates.append(lemma_n)
    if lemma_v != word_lower:
        candidates.append(lemma_v)
    if lemma_a != word_lower:
        candidates.append(lemma_a)

    if candidates:
        # 取最短的还原结果
        return min(candidates, key=len)

    # 如果所有还原都等于原词，返回原词
    return word_lower


# ============================================================
# 4. 专有名词过滤
# ============================================================

def is_proper_noun(word_info, sentence, proper_dict, nltk_word_set):
    """
    判断一个单词是否为专有名词
    多层过滤策略：
    1. 查专有名词词典
    2. 首字母大写启发式
    3. 是否在 NLTK 英文词表中
    """
    word_lower = word_info['lower']
    word_surface = word_info['surface']

    # (a) 在专有名词黑名单中 → 过滤
    if word_lower in proper_dict:
        return True

    # (b) 首字母大写但不在句首 → 可能是专有名词
    # 但还需要更多证据
    if word_surface[0].isupper() and not word_lower.isupper():
        # 检查是否在常见英文词表中
        if word_lower not in nltk_word_set:
            # 不在普通词表中 → 很可能是专有名词
            return True
        # 在词表中但从上下文看是专有名词的情况
        # 可以用 NER 进一步判断，但代价较高
        # 暂时信任词表

    # (c) 全大写缩写词（如 NASA, FBI）→ 过滤（这些是机构名/缩写）
    if len(word_surface) >= 3 and word_surface.isupper():
        if word_lower not in nltk_word_set:
            return True

    return False


# ============================================================
# 5. 主处理流程
# ============================================================

def process_blocks(blocks, irregular_set, proper_dict, nltk_word_set):
    """
    处理所有句子块，返回：
    - word_stats: {canonical_word: {total_freq, years: set, types: Counter, first_year}}
    - occurrences: [{canonical, surface, year, exam_type, section, sentence, offset, length}]
    """
    lemmatizer = WordNetLemmatizer()
    word_stats = {}
    occurrences = []

    for block in blocks:
        year = block['year']
        exam_type = block['exam_type']
        section = block['section']
        sentence = block['sentence']

        # 先移除缩写形式（don't, can't 等整词移除）
        clean_sentence = remove_contractions(sentence)

        # 提取单词
        words = extract_words_from_sentence(clean_sentence)

        for w in words:
            wl = w['lower']

            # 过滤：太短（表面形式 < 3）
            if is_too_short(wl):
                continue

            # 过滤：专有名词
            if is_proper_noun(w, sentence, proper_dict, nltk_word_set):
                continue

            # 词形规范化
            canonical = normalize_word(wl, lemmatizer, irregular_set)

            # 过滤：规范形式太短（如 are→be，does→do 等）
            if is_too_short(canonical):
                continue

            # 更新统计
            if canonical not in word_stats:
                word_stats[canonical] = {
                    'total_freq': 0,
                    'years': set(),
                    'types': Counter(),
                    'first_year': year,
                    'last_year': year
                }
            ws = word_stats[canonical]
            ws['total_freq'] += 1
            ws['years'].add(year)
            ws['types'][exam_type] += 1
            ws['first_year'] = min(ws['first_year'], year)
            ws['last_year'] = max(ws['last_year'], year)

            # 记录出现位置（使用清理后的句子）
            occurrences.append({
                'canonical': canonical,
                'surface': w['surface'],
                'year': year,
                'exam_type': exam_type,
                'section': section,
                'sentence': clean_sentence,
                'offset': w['start'],
                'length': w['length']
            })

    # 转换 years 从 set 到 count
    for ws in word_stats.values():
        ws['year_count'] = len(ws['years'])
        ws['years'] = sorted(ws['years'])
        ws['types'] = dict(ws['types'])

    return word_stats, occurrences


# ============================================================
# 6. 主入口
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='单词提取与规范化')
    parser.add_argument('--input', default='../data/parsed_blocks.json',
                        help='解析后的句子块 JSON')
    parser.add_argument('--irregular', default='irregular_forms.json',
                        help='不规则形式词典')
    parser.add_argument('--output-stats', default='../data/word_stats.json',
                        help='词频统计输出')
    parser.add_argument('--output-occ', default='../data/occurrences.json',
                        help='单词出现位置输出')
    args = parser.parse_args()

    # 加载资源
    print('加载不规则形式词典...')
    irregular_set = load_irregular_forms(args.irregular)
    print(f'  不规则形式: {len(irregular_set)} 个')

    print('加载专有名词词典...')
    proper_dict = load_proper_noun_dict()
    print(f'  专有名词: {len(proper_dict)} 个')

    print('加载 NLTK 英文词表...')
    try:
        nltk_word_set = set(w.lower() for w in nltk_words.words())
    except Exception:
        print('  警告: 无法加载 NLTK words，使用空集')
        nltk_word_set = set()
    print(f'  词表大小: {len(nltk_word_set)}')

    # 加载句子块
    print(f'\n加载句子块: {args.input}')
    with open(args.input, 'r', encoding='utf-8') as f:
        blocks = json.load(f)
    print(f'  句子块数: {len(blocks)}')

    # 处理
    print('\n处理单词...')
    word_stats, occurrences = process_blocks(blocks, irregular_set, proper_dict, nltk_word_set)
    print(f'  规范单词数: {len(word_stats)}')
    print(f'  总出现次数: {len(occurrences)}')

    # 保存
    os.makedirs(os.path.dirname(args.output_stats), exist_ok=True)
    with open(args.output_stats, 'w', encoding='utf-8') as f:
        json.dump(word_stats, f, ensure_ascii=False, indent=2)
    print(f'\n词频统计已保存: {args.output_stats}')

    with open(args.output_occ, 'w', encoding='utf-8') as f:
        json.dump(occurrences, f, ensure_ascii=False, indent=2)
    print(f'出现位置已保存: {args.output_occ} ({len(occurrences)} 条)')

    # 统计
    print(f'\n=== Top 20 高频词 ===')
    sorted_words = sorted(word_stats.items(), key=lambda x: x[1]['total_freq'], reverse=True)
    for i, (word, stats) in enumerate(sorted_words[:20]):
        print(f'  {i+1}. {word:<15} 词频: {stats["total_freq"]:<6} '
              f'年份: {stats["year_count"]:<3} 首次: {stats["first_year"]}')


if __name__ == '__main__':
    main()
