"""
词频统计与数据库构建
- 从 word_stats.json 和 occurrences.json 导入 SQLite
- 创建索引
"""

import json
import sqlite3
import os
import sys


DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    total_freq INTEGER DEFAULT 0,
    year_count INTEGER DEFAULT 0,
    first_year INTEGER,
    last_year INTEGER,
    freq_by_year TEXT,
    freq_by_type TEXT
);

CREATE TABLE IF NOT EXISTS occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    surface TEXT,
    year INTEGER NOT NULL,
    exam_type TEXT NOT NULL,
    section TEXT NOT NULL,
    sentence TEXT NOT NULL,
    word_offset INTEGER,
    word_length INTEGER,
    FOREIGN KEY (word_id) REFERENCES words(id)
);

CREATE INDEX IF NOT EXISTS idx_words_word ON words(word);
CREATE INDEX IF NOT EXISTS idx_words_freq ON words(total_freq DESC);
CREATE INDEX IF NOT EXISTS idx_words_yearcount ON words(year_count DESC);
CREATE INDEX IF NOT EXISTS idx_words_firstyear ON words(first_year);
CREATE INDEX IF NOT EXISTS idx_occ_word ON occurrences(word_id);
CREATE INDEX IF NOT EXISTS idx_occ_year ON occurrences(year);
CREATE INDEX IF NOT EXISTS idx_occ_type ON occurrences(exam_type);
CREATE INDEX IF NOT EXISTS idx_occ_section ON occurrences(section);
CREATE INDEX IF NOT EXISTS idx_occ_word_year ON occurrences(word_id, year);
CREATE INDEX IF NOT EXISTS idx_occ_word_type ON occurrences(word_id, exam_type);
"""


def build_database(stats_file, occ_file, db_path):
    """从 JSON 构建 SQLite 数据库"""

    print('加载词频统计...')
    with open(stats_file, 'r', encoding='utf-8') as f:
        word_stats = json.load(f)
    print(f'  规范单词: {len(word_stats)}')

    print('加载出现位置...')
    with open(occ_file, 'r', encoding='utf-8') as f:
        occurrences = json.load(f)
    print(f'  出现记录: {len(occurrences)}')

    # 创建数据库
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    conn.executescript(DB_SCHEMA)

    # 插入单词数据
    print('\n插入单词数据...')
    word_id_map = {}
    cursor = conn.cursor()

    word_rows = []
    for word, stats in word_stats.items():
        word_rows.append((
            word,
            stats['total_freq'],
            stats['year_count'],
            stats['first_year'],
            stats['last_year'],
            json.dumps({str(y): 0 for y in stats['years']}, ensure_ascii=False),
            json.dumps(stats['types'], ensure_ascii=False)
        ))
        # 先不计算分年词频，等插入 occurrences 后统一更新

    cursor.executemany(
        "INSERT INTO words (word, total_freq, year_count, first_year, last_year, freq_by_year, freq_by_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
        word_rows
    )
    conn.commit()

    # 建立 word -> id 映射
    for row in cursor.execute("SELECT id, word FROM words"):
        word_id_map[row[1]] = row[0]
    print(f'  插入 {len(word_id_map)} 条单词记录')

    # 批量插入出现位置
    print('\n插入出现位置...')
    occ_rows = []
    batch_size = 5000
    count = 0

    for occ in occurrences:
        canonical = occ['canonical']
        word_id = word_id_map.get(canonical)
        if word_id is None:
            continue

        occ_rows.append((
            word_id,
            occ['surface'],
            occ['year'],
            occ['exam_type'],
            occ['section'],
            occ['sentence'],
            occ['offset'],
            occ['length']
        ))

        if len(occ_rows) >= batch_size:
            cursor.executemany(
                "INSERT INTO occurrences (word_id, surface, year, exam_type, section, sentence, word_offset, word_length) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                occ_rows
            )
            count += len(occ_rows)
            occ_rows = []
            print(f'  已插入 {count} / {len(occurrences)}')

    # 剩余数据
    if occ_rows:
        cursor.executemany(
            "INSERT INTO occurrences (word_id, surface, year, exam_type, section, sentence, word_offset, word_length) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            occ_rows
        )
        count += len(occ_rows)

    conn.commit()
    print(f'  插入 {count} 条出现位置记录')

    # 更新分年词频
    print('\n更新分年词频...')
    cursor.execute("""
        UPDATE words SET freq_by_year = (
            SELECT json_group_object(year, cnt) FROM (
                SELECT year, COUNT(*) as cnt
                FROM occurrences
                WHERE occurrences.word_id = words.id
                GROUP BY year
                ORDER BY year
            )
        )
    """)
    conn.commit()
    print('  分年词频已更新')

    # 统计信息
    cursor.execute("SELECT COUNT(*) FROM words")
    word_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM occurrences")
    occ_count = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(total_freq) FROM words")
    total_freq = cursor.fetchone()[0]

    print(f'\n=== 数据库统计 ===')
    print(f'  单词数: {word_count}')
    print(f'  出现记录: {occ_count}')
    print(f'  总词频: {total_freq}')
    print(f'  数据库路径: {db_path}')

    # 验证
    print(f'\n=== Top 10 验证 ===')
    for row in cursor.execute(
        "SELECT word, total_freq, year_count, first_year FROM words ORDER BY total_freq DESC LIMIT 10"
    ):
        print(f'  {row[0]:<15} 词频:{row[1]:<5} 年份:{row[2]:<3} 首次:{row[3]}')

    conn.close()
    return db_path


if __name__ == '__main__':
    stats_file = sys.argv[1] if len(sys.argv) > 1 else '../data/word_stats.json'
    occ_file = sys.argv[2] if len(sys.argv) > 2 else '../data/occurrences.json'
    db_path = sys.argv[3] if len(sys.argv) > 3 else '../data/exam_words.db'

    build_database(stats_file, occ_file, db_path)
