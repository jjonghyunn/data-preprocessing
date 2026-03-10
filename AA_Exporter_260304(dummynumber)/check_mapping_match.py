"""
check_mapping_match.py
─────────────────────────────────────────────────────────────────────
aa_exports/ 의 CSV 파일들이 tb_column_name_mapping.csv 와
컬럼 레벨로 정상 매핑되는지 검수합니다.

[검사 항목]
  1. 매핑 테이블에 tb 자체가 없는 파일          → ❌ 매핑없음
  2. 매핑 value_n 이 CSV value 컬럼과 전혀 안 맞음 → 🔴 전혀불일치
  3. 매핑에만 있고 CSV에는 없는 컬럼 존재
     (tb_column_name_mapping의 value_n > CSV 실제 컬럼) → ⚠️ 매핑초과(CSV부족)
  4. CSV에만 있고 매핑에 없는 value 컬럼 존재
     (CSV value19~20+ 등 > tb_column_name_mapping) → ⚠️ CSV초과(매핑누락)
  5. 3+4 동시                                    → ⚠️ 양쪽불일치
  6. 완전 일치                                    → ✅ 정상

[결과 저장]
  mapping_match_report/_all_check.csv
"""

import re
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR     = Path(__file__).parent
EXPORTS_DIR  = BASE_DIR / "aa_exports"
MAPPING_CSV  = BASE_DIR / "tb_column_name_mapping.csv"
OUT_DIR      = BASE_DIR / "mapping_match_report"

# aa_exports 하위 날짜폴더(260224 등)까지 포함해서 검색
SEARCH_SUBDIRS = False

VALUE_COL_PAT = re.compile(r"^value\d+$", re.IGNORECASE)

print(f"EXPORTS_DIR : {EXPORTS_DIR}")
print(f"MAPPING_CSV : {MAPPING_CSV}\n")

mapping_df = pd.read_csv(MAPPING_CSV)
OUT_DIR.mkdir(exist_ok=True)

# ── 대상 파일 수집 ────────────────────────────────────────────────
glob_fn = EXPORTS_DIR.rglob if SEARCH_SUBDIRS else EXPORTS_DIR.glob
csv_files = [
    f for f in glob_fn("*.csv")
    if "_long"    not in f.name
    and "_stacked" not in f.name
    and not f.stem.startswith("union")
    and not f.stem.startswith("_")
]
print(f"검사 대상 파일: {len(csv_files)}개\n")


# ── 상태 결정 ─────────────────────────────────────────────────────
def get_status(matched, mapping_only, csv_only):
    if not matched:
        return "🔴 전혀불일치"
    if mapping_only and csv_only:
        return "⚠️ 양쪽불일치"
    if mapping_only:
        return "⚠️ 매핑초과(CSV부족)"
    if csv_only:
        return "⚠️ CSV초과(매핑누락)"
    return "✅ 정상"


# ── 파일별 검사 ───────────────────────────────────────────────────
rows = []

no_mapping_list    = []
empty_match_list   = []
ok_list            = []
mapping_over_list  = []   # 매핑 > CSV
csv_over_list      = []   # CSV > 매핑
both_mismatch_list = []   # 양쪽

for src_path in sorted(csv_files):
    stem   = src_path.stem
    tb_key = re.sub(r"_\d{8}_\d{6}$", "", stem)

    tb_mapping = mapping_df[mapping_df["tb"] == tb_key]
    if tb_mapping.empty:
        tb_mapping = mapping_df[mapping_df["tb"] == re.sub(r"_prior$", "", tb_key)]

    if tb_mapping.empty:
        no_mapping_list.append(tb_key)
        rows.append({
            "tb_key"          : tb_key,
            "file"            : src_path.name,
            "status"          : "❌ 매핑없음",
            "matched_cnt"     : "",
            "mapping_only_cnt": "",
            "csv_only_cnt"    : "",
            "matched"         : "",
            "mapping_only"    : "",
            "csv_only"        : "",
        })
        continue

    # 매핑에서 기대하는 value_n 컬럼셋
    mapping_value_ns = set(
        tb_mapping["value_n"].dropna().astype(str).str.strip()
    )

    try:
        df = pd.read_csv(src_path, encoding="utf-8-sig", nrows=1)
    except Exception as e:
        print(f"  [읽기오류] {tb_key}: {e}")
        continue

    # CSV 실제 value\d+ 컬럼셋
    csv_value_cols = {c for c in df.columns if VALUE_COL_PAT.match(str(c))}

    def _sort_key(x):
        m = re.search(r"\d+", x)
        return (int(m.group()), x) if m else (9999, x)

    matched      = sorted(mapping_value_ns & csv_value_cols, key=_sort_key)
    mapping_only = sorted(mapping_value_ns - csv_value_cols, key=_sort_key)
    csv_only     = sorted(csv_value_cols   - mapping_value_ns, key=_sort_key)

    status = get_status(matched, mapping_only, csv_only)

    rows.append({
        "tb_key"          : tb_key,
        "file"            : src_path.name,
        "status"          : status,
        "matched_cnt"     : len(matched),
        "mapping_only_cnt": len(mapping_only),
        "csv_only_cnt"    : len(csv_only),
        "matched"         : " / ".join(matched),
        "mapping_only"    : " / ".join(mapping_only),
        "csv_only"        : " / ".join(csv_only),
    })

    if not matched:
        empty_match_list.append(tb_key)
    elif mapping_only and csv_only:
        both_mismatch_list.append(tb_key)
    elif mapping_only:
        mapping_over_list.append(tb_key)
    elif csv_only:
        csv_over_list.append(tb_key)
    else:
        ok_list.append(tb_key)


# ── CSV 저장 ──────────────────────────────────────────────────────
all_check_path = OUT_DIR / "_all_check.csv"
result_df = pd.DataFrame(rows, columns=[
    "tb_key", "file", "status",
    "matched_cnt", "mapping_only_cnt", "csv_only_cnt",
    "matched", "mapping_only", "csv_only",
])
result_df.to_csv(all_check_path, index=False, encoding="utf-8-sig")
print(f"▶ 결과 저장: {all_check_path}\n")
print("=" * 70)


# ── 콘솔 출력 ────────────────────────────────────────────────────
print(f"\n✅ 정상 ({len(ok_list)}개)")
for t in ok_list:
    print(f"  - {t}")

print(f"\n⚠️  매핑초과·CSV부족 ({len(mapping_over_list)}개)"
      f"  ← 매핑 value_n이 CSV에 없음 (tb mapping이 CSV보다 많음)")
for t in mapping_over_list:
    r = next(x for x in rows if x["tb_key"] == t and x["status"] == "⚠️ 매핑초과(CSV부족)")
    print(f"  - {t}")
    print(f"      매칭됨       ({r['matched_cnt']}): {r['matched']}")
    print(f"      매핑에만 있음({r['mapping_only_cnt']}): {r['mapping_only']}")

print(f"\n⚠️  CSV초과·매핑누락 ({len(csv_over_list)}개)"
      f"  ← CSV에 value19~20+ 등 있는데 tb mapping에 없음")
for t in csv_over_list:
    r = next(x for x in rows if x["tb_key"] == t and x["status"] == "⚠️ CSV초과(매핑누락)")
    print(f"  - {t}")
    print(f"      매칭됨      ({r['matched_cnt']}): {r['matched']}")
    print(f"      CSV에만 있음({r['csv_only_cnt']}): {r['csv_only']}")

print(f"\n⚠️  양쪽 불일치 ({len(both_mismatch_list)}개)"
      f"  ← 매핑 초과 + CSV 초과 동시 발생")
for t in both_mismatch_list:
    r = next(x for x in rows if x["tb_key"] == t and x["status"] == "⚠️ 양쪽불일치")
    print(f"  - {t}")
    print(f"      매칭됨       ({r['matched_cnt']}): {r['matched']}")
    print(f"      매핑에만 있음({r['mapping_only_cnt']}): {r['mapping_only']}")
    print(f"      CSV에만 있음 ({r['csv_only_cnt']}): {r['csv_only']}")

print(f"\n🔴 매핑 컬럼 전혀 안 맞음 ({len(empty_match_list)}개)"
      f"  ← value_vars=[] → metric_name KeyError 원인")
for t in empty_match_list:
    r = next(x for x in rows if x["tb_key"] == t)
    print(f"  - {t}")
    print(f"      매핑 기대: {r['mapping_only']}")
    print(f"      CSV 실제:  {r['csv_only']}")

print(f"\n❌ 매핑 테이블에 tb 없음 ({len(no_mapping_list)}개)  ← skip 대상")
for t in no_mapping_list:
    print(f"  - {t}")

print("\n" + "=" * 70)
total = len(ok_list) + len(mapping_over_list) + len(csv_over_list) + len(both_mismatch_list) + len(empty_match_list) + len(no_mapping_list)
print(
    f"합계 {total}개: "
    f"정상 {len(ok_list)} / "
    f"매핑초과 {len(mapping_over_list)} / "
    f"CSV초과 {len(csv_over_list)} / "
    f"양쪽불일치 {len(both_mismatch_list)} / "
    f"전혀불일치 {len(empty_match_list)} / "
    f"매핑없음 {len(no_mapping_list)}"
)
print(f"\n출력 폴더: {OUT_DIR}")
print(f"  - 통합 검수 CSV: _all_check.csv")
print(f"    컬럼: tb_key / file / status / matched_cnt / mapping_only_cnt / csv_only_cnt / matched / mapping_only / csv_only")
