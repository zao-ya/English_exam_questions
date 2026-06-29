"""手动修正：用户提供的拆分方案"""
import json, re, os

# 合并词 → 正确拆分 映射表
FIX_MAP = {
    'areinfluencedandtheninfluenceothers': 'are influenced and then influence others',
    'andfranceexamplesareusedto': 'and France examples are used to',
    'theglamourofcelebritymoms': 'the glamour of celebrity moms',
    'returnforsimilarfavours': 'return for similar favours',
    'ofthemexicocitysubway': 'of the Mexico City subway',
    'structureofalanguage': 'structure of a language',
    'asksmartinbercovici': 'asks Martin Bercovici',
    'afewcelebritieslike': 'a few celebrities like',
    'consultanciestendto': 'consultancies tend to',
    'inspirespopularsci': 'inspires popular sci',
    'abetterlifeforall': 'a better life for all',
    'asupportiveadult': 'a supportive adult',
    'helpingraisegpas': 'helping raise GPAs',
    'tradecoordination': 'trade coordination',
    # 同一句子中附带修正的其他合并词
    'wouldbe': 'would be',
    'it werenot': 'it were not',
    'associatesto doso forthemin': 'associates to do so for them in',
    'whichiswhy': 'which is why',
    'lear nit': 'learn it',
    'TheUS': 'The US',
    'tosay': 'to say',
    'cameto': 'came to',
    'dee pin': 'deep in',
    'istrueofthebilskicase': 'is true of the Bilski case',
    'onthe': 'on the',
    'th every': 'the very',
    'wha tit': 'what it',
    'anargument': 'an argument',
    'withintheir': 'within their',
    'andtheir': 'and their',
}

def fix_sentences(blocks):
    import re
    count = 0
    for block in blocks:
        original = block['sentence']
        fixed = original
        for bad, good in FIX_MAP.items():
            # 大小写不敏感替换
            pattern = re.compile(re.escape(bad), re.IGNORECASE)
            if pattern.search(fixed):
                fixed = pattern.sub(good, fixed)
        if fixed != original:
            block['sentence'] = fixed
            count += 1
    print(f'  修复句子数: {count}')
    return blocks

def main():
    input_file = '../data/parsed_blocks_fixed.json'
    output_file = '../data/parsed_blocks_final.json'

    print('加载句子块...')
    with open(input_file, encoding='utf-8') as f:
        blocks = json.load(f)

    print(f'  共 {len(blocks)} 块')
    blocks = fix_sentences(blocks)

    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(blocks, f, ensure_ascii=False, indent=2)
    print(f'保存 -> {output_file}')

if __name__ == '__main__':
    main()
