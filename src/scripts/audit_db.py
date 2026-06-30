#!/usr/bin/env python3
"""Audit exam_words.db for data accuracy."""

import sqlite3, json, sys, os

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'exam_words.db')
DB = os.path.abspath(DB)

def run():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    findings = []

    # ---------------------------------------------------------------
    # Schema discovery
    # ---------------------------------------------------------------
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("Tables:", tables)

    cols = {}
    for t in tables:
        cs = [r for r in cur.execute(f"PRAGMA table_info({t})")]
        cols[t] = [(c[1], c[2]) for c in cs]
        print(f"  {t}: {cols[t]}")

    # ---------------------------------------------------------------
    # 1. Sample 10 words: freq_by_type sums to total_freq ?
    # ---------------------------------------------------------------
    sample_words = ["people", "world", "system", "government", "research",
                    "science", "education", "economic", "political", "culture"]
    cursor = conn.execute("PRAGMA table_info(words)")
    word_cols = [c[1] for c in cursor.fetchall()]

    for w in sample_words:
        row = cur.execute(
            "SELECT * FROM words WHERE LOWER(word) = ?", (w,)
        ).fetchone()
        if row is None:
            findings.append({
                "issue": f"Sample word '{w}' not found in words table",
                "severity": "medium",
                "detail": f"Word '{w}' missing from words table."
            })
            continue
        rd = dict(row)

        # Check if freq_by_type column exists and parse it
        if "freq_by_type" not in rd:
            findings.append({
                "issue": f"Column freq_by_type missing from words table",
                "severity": "high",
                "detail": "Schema missing freq_by_type column."
            })
            break

        total = rd.get("total_freq", 0)
        fbt_raw = rd.get("freq_by_type")
        if fbt_raw is None:
            fbt = {}
        elif isinstance(fbt_raw, str):
            try:
                fbt = json.loads(fbt_raw)
            except json.JSONDecodeError:
                findings.append({
                    "issue": f"Invalid JSON in freq_by_type for '{w}'",
                    "severity": "high",
                    "detail": f"Raw: {fbt_raw[:200]}"
                })
                continue
        else:
            fbt = fbt_raw if isinstance(fbt_raw, dict) else {}

        fbt_sum = sum(v for v in fbt.values() if isinstance(v, (int, float)))
        if fbt_sum != total:
            findings.append({
                "issue": f"Mismatch: freq_by_type sum ({fbt_sum}) != total_freq ({total}) for '{w}'",
                "severity": "high",
                "detail": f"freq_by_type={json.dumps(fbt)}"
            })
        else:
            print(f"  OK: '{w}' freq_by_type sum={fbt_sum} == total_freq={total}")

    # ---------------------------------------------------------------
    # 2. Any duplicate word entries?
    # ---------------------------------------------------------------
    dupes = cur.execute("""
        SELECT word, COUNT(*) as cnt
        FROM words
        GROUP BY LOWER(word)
        HAVING cnt > 1
    """).fetchall()
    if dupes:
        for d in dupes:
            findings.append({
                "issue": f"Duplicate word: '{d['word']}' appears {d['cnt']} times",
                "severity": "high",
                "detail": f"Word '{d['word']}' has {d['cnt']} entries in words table."
            })
    else:
        print("  OK: No duplicate word entries.")

    # Also check for exact word duplicates (case-sensitive)
    exact_dupes = cur.execute("""
        SELECT word, COUNT(*) as cnt
        FROM words
        GROUP BY word
        HAVING cnt > 1
    """).fetchall()
    if exact_dupes:
        for d in exact_dupes:
            findings.append({
                "issue": f"Exact duplicate word: '{d['word']}' appears {d['cnt']} times",
                "severity": "high",
                "detail": f"Word '{d['word']}' has {d['cnt']} entries (case-sensitive)."
            })
    else:
        print("  OK: No exact duplicate word entries.")

    # ---------------------------------------------------------------
    # 3. Any orphan occurrences (word_id not in words table)?
    # ---------------------------------------------------------------
    for t in tables:
        if t not in ("words", "sqlite_sequence"):
            # Check if this table has a word_id column
            tcols = [c[0] for c in cols[t]]
            if "word_id" in tcols:
                orphans = cur.execute(f"""
                    SELECT DISTINCT {t}.word_id
                    FROM {t}
                    LEFT JOIN words ON {t}.word_id = words.id
                    WHERE words.id IS NULL
                """).fetchall()
                if orphans:
                    orphan_ids = [str(o[0]) for o in orphans]
                    findings.append({
                        "issue": f"Orphan word_ids in {t}: {orphan_ids[:20]}",
                        "severity": "high",
                        "detail": f"Table '{t}' has {len(orphans)} word_ids not in words table: {', '.join(orphan_ids[:20])}"
                    })
                else:
                    print(f"  OK: No orphan word_ids in '{t}'.")
    print("  Orphan check complete.")

    # ---------------------------------------------------------------
    # 4. first_year <= last_year for all words?
    # ---------------------------------------------------------------
    has_first = "first_year" in [c[0] for c in cols.get("words", [])]
    has_last  = "last_year" in [c[0] for c in cols.get("words", [])]
    if has_first and has_last:
        bad_years = cur.execute("""
            SELECT word, first_year, last_year
            FROM words
            WHERE first_year IS NOT NULL AND last_year IS NOT NULL
              AND first_year > last_year
        """).fetchall()
        if bad_years:
            for r in bad_years:
                findings.append({
                    "issue": f"Year order mismatch: '{r['word']}' first_year={r['first_year']} > last_year={r['last_year']}",
                    "severity": "high",
                    "detail": f"Word '{r['word']}': first_year={r['first_year']}, last_year={r['last_year']}"
                })
        else:
            print("  OK: All words have first_year <= last_year.")
    else:
        print(f"  INFO: first_year/last_year columns not both present. Has first={has_first}, last={has_last}")

    # ---------------------------------------------------------------
    # 5. Any words with total_freq > 0 but year_count = 0 (or similar)?
    # ---------------------------------------------------------------
    # Detect the right columns: could be year_count, years_active, num_years, etc.
    year_col = None
    for c in word_cols:
        if c in ("year_count", "years_active", "num_years", "year_span"):
            year_col = c
            break
    if year_col:
        bad_freq = cur.execute(f"""
            SELECT word, total_freq, {year_col}
            FROM words
            WHERE total_freq > 0 AND ({year_col} IS NULL OR {year_col} = 0)
        """).fetchall()
        if bad_freq:
            for r in bad_freq:
                findings.append({
                    "issue": f"Positive total_freq but zero/Null {year_col}: '{r['word']}' total_freq={r['total_freq']}, {year_col}={r[year_col]}",
                    "severity": "high",
                    "detail": f"Word '{r['word']}': total_freq={r['total_freq']}, {year_col}={r[year_col]}"
                })
            print(f"  Found {len(bad_freq)} words with total_freq>0 but {year_col}=0/null.")
        else:
            print(f"  OK: No words with total_freq>0 and {year_col}=0/null.")
    else:
        # Check for freq_by_year JSON length vs total_freq
        has_fby = "freq_by_year" in word_cols
        if has_fby:
            rows = cur.execute("""
                SELECT word, total_freq, freq_by_year
                FROM words
                WHERE total_freq > 0 AND freq_by_year IS NOT NULL
                LIMIT 500
            """).fetchall()
            bad_count = 0
            for r in rows:
                try:
                    fby = json.loads(r["freq_by_year"])
                except Exception:
                    continue
                if isinstance(fby, dict) and len(fby) == 0:
                    findings.append({
                        "issue": f"Positive total_freq but empty freq_by_year: '{r['word']}' total_freq={r['total_freq']}",
                        "severity": "medium",
                        "detail": f"Word '{r['word']}': total_freq={r['total_freq']}, freq_by_year is empty dict"
                    })
                    bad_count += 1
            if bad_count == 0:
                print("  OK: Sampled 500 words; no empty freq_by_year with total_freq>0 found.")
            else:
                print(f"  Found {bad_count} words with total_freq>0 but empty freq_by_year.")
        else:
            print("  INFO: No year_count-like column; skipping check 5.")

    # ---------------------------------------------------------------
    # 6. freq_by_year JSON valid for a sample of words?
    # ---------------------------------------------------------------
    if "freq_by_year" in word_cols:
        rows = cur.execute("""
            SELECT word, freq_by_year
            FROM words
            WHERE freq_by_year IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 50
        """).fetchall()
        bad_json = 0
        for r in rows:
            raw = r["freq_by_year"]
            if raw is None:
                continue
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    findings.append({
                        "issue": f"freq_by_year not a dict for '{r['word']}'",
                        "severity": "medium",
                        "detail": f"Type: {type(parsed).__name__}, word='{r['word']}'"
                    })
                    bad_json += 1
                else:
                    # Validate keys look like years and values are numbers
                    for k, v in parsed.items():
                        if not isinstance(k, (str, int)):
                            findings.append({
                                "issue": f"freq_by_year key not int/str for '{r['word']}': {k}",
                                "severity": "low",
                                "detail": f"Key type: {type(k).__name__}"
                            })
                        if not isinstance(v, (int, float)):
                            findings.append({
                                "issue": f"freq_by_year value not numeric for '{r['word']}': {k}={v}",
                                "severity": "low",
                                "detail": f"Value type: {type(v).__name__}"
                            })
            except json.JSONDecodeError as e:
                findings.append({
                    "issue": f"Invalid freq_by_year JSON for '{r['word']}'",
                    "severity": "high",
                    "detail": f"Error: {str(e)}, raw: {str(raw)[:200]}"
                })
                bad_json += 1
        if bad_json == 0:
            print(f"  OK: Sampled {len(rows)} words; all freq_by_year JSON valid.")
        else:
            print(f"  Found {bad_json} words with invalid freq_by_year JSON.")
    else:
        print("  INFO: No freq_by_year column; skipping check 6.")

    # ---------------------------------------------------------------
    # Extra: general stats
    # ---------------------------------------------------------------
    word_count = cur.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    print(f"\n=== General Stats ===")
    print(f"  Total words: {word_count}")

    # Look at occurrence tables
    for t in tables:
        if t != "words" and t != "sqlite_sequence":
            cnt = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t} rows: {cnt}")

    conn.close()

    # Print final JSON
    print(f"\n=== FINAL FINDINGS JSON ===")
    print(json.dumps(findings, indent=2, ensure_ascii=False))
    return findings

if __name__ == "__main__":
    run()
