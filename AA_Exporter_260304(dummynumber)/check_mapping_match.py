"""
check_mapping_match.py
─────────────────────────────────────────────────────────────────────
aa_exports/ 의 CSV 파일들이 tb_column_name_mapping.csv 와
정상적으로 매핑되는지 검수합니다.

[검사 항목]
  1. 매핑 테이블에 tb 자체가 없는 파일 (skip 대상)
  2. 매핑은 있지만 value_n 컬럼명이 CSV와 하나도 안 맞는 파일
     → value_vars=[] → melt 0행 → metric_name KeyError 원인
  3. 일부만 매칭되는 파일 (부분 누락)
"""

import re
from pathlib import Path
import pandas as pd

BASE_DIR     = Path(__file__).parent
EXPORTS_DIR  = BASE_DIR / "aa_exports"
MAPPING_CSV  = BASE_DIR / "tb_column_name_mapping.csv"

print(f"EXPORTS_DIR : {EXPORTS_DIR}")
print(f"MAPPING_CSV : {MAPPING_CSV}\n")

mapping_df = pd.read_csv(MAPPING_CSV)

csv_files = [
    f for f in EXPORTS_DIR.glob("*.csv")
    if "_long" not in f.name and "_stacked" not in f.name and not f.stem.startswith("union")
]
print(f"검사 대상 파일: {len(csv_files)}개\n")
print("=" * 70)

no_mapping   = []   # 매핑 테이블에 tb 없음
empty_match  = []   # 매핑 있으나 컬럼 하나도 안 맞음
partial      = []   # 일부 컬럼만 매칭
ok_list      = []   # 정상

for src_path in sorted(csv_files):
    stem   = src_path.stem
    tb_key = re.sub(r"_\d{8}_\d{6}$", "", stem)

    tb_mapping = mapping_df[mapping_df["tb"] == tb_key]
    if tb_mapping.empty:
        tb_mapping = mapping_df[mapping_df["tb"] == re.sub(r"_prior$", "", tb_key)]

    if tb_mapping.empty:
        no_mapping.append(tb_key)
        continue

    rename_dict = dict(zip(tb_mapping["value_n"], tb_mapping["column"]))

    try:
        df = pd.read_csv(src_path, encoding="utf-8-sig", nrows=1)
    except Exception as e:
        print(f"  [읽기오류] {tb_key}: {e}")
        continue

    mapped_cols   = [c for c in rename_dict.keys() if c in df.columns]
    unmapped_cols = [c for c in rename_dict.keys() if c not in df.columns]
    value_vars    = [rename_dict[c] for c in mapped_cols]

    if not value_vars:
        empty_match.append({
            "tb_key": tb_key,
            "mapping_expects": list(rename_dict.keys()),
            "csv_columns": list(df.columns),
        })
    elif unmapped_cols:
        partial.append({
            "tb_key": tb_key,
            "matched": mapped_cols,
            "unmatched": unmapped_cols,
        })
    else:
        ok_list.append(tb_key)

# ── 결과 출력 ──────────────────────────────────────────────────────
print(f"\n✅ 정상 ({len(ok_list)}개)")
for t in ok_list:
    print(f"  - {t}")

print(f"\n⚠️  일부 컬럼 누락 ({len(partial)}개)")
for item in partial:
    print(f"  - {item['tb_key']}")
    print(f"      매칭됨  : {item['matched']}")
    print(f"      누락됨  : {item['unmatched']}")

print(f"\n🔴 매핑 컬럼 전혀 안 맞음 → metric_name KeyError 원인 ({len(empty_match)}개)")
for item in empty_match:
    print(f"  - {item['tb_key']}")
    print(f"      매핑이 기대하는 컬럼 : {item['mapping_expects']}")
    print(f"      CSV 실제 컬럼       : {item['csv_columns']}")

print(f"\n❌ 매핑 테이블에 tb 없음 → skip 대상 ({len(no_mapping)}개)")
for t in no_mapping:
    print(f"  - {t}")

print("\n" + "=" * 70)
print(f"합계: 정상 {len(ok_list)} / 부분누락 {len(partial)} / 전혀불일치 {len(empty_match)} / 매핑없음 {len(no_mapping)}")
