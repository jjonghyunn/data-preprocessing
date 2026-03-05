"""
make_dummy.py
─────────────────────────────────────────────────────────
raw CSV 파일의 value1~valueN 숫자 컬럼을 더미 값으로 교체.
(GitHub/블로그 공유용 가짜 데이터 생성)

대상  : aa_exports/ 내 CSV 중 _separate 미포함 & union 미시작
제외  : Subsidiary, Country, Site_Code, RSID,
        Start_Date, End_Date, itemId, value(문자), status, error
출력  : aa_exports_dummy/ 폴더에 동일 파일명으로 저장
"""

import os
import csv
import random
import re

# ── 경로 설정 ──────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SRC_DIR    = os.path.join(BASE_DIR, "aa_exports")
DST_DIR    = os.path.join(BASE_DIR, "aa_exports_dummy")
os.makedirs(DST_DIR, exist_ok=True)

# 더미 값 생성 범위 (원본 숫자와 자릿수가 비슷하게 보이도록)
DUMMY_MIN = 100
DUMMY_MAX = 999_999

# value1, value2 ... valueN 패턴 (숫자가 붙은 것만, value 단독 제외)
VALUE_COL_PATTERN = re.compile(r"^value\d+$")

# ── 대상 파일 필터 ─────────────────────────────────────────────────────────
def is_target(filename: str) -> bool:
    if not filename.endswith(".csv"):
        return False
    if "separate" in filename.lower():
        return False
    if filename.lower().startswith("union"):
        return False
    return True


# ── 더미 숫자 생성 ─────────────────────────────────────────────────────────
def dummy_number(original: str) -> str:
    """원본이 숫자면 더미 숫자로, 빈값/None/문자면 그대로."""
    stripped = original.strip().replace("'", "")
    if stripped in ("", "None", "null", "NULL"):
        return original
    try:
        float(stripped)
        # 소수점 유무 보존
        if "." in stripped:
            return str(round(random.uniform(DUMMY_MIN, DUMMY_MAX), 1))
        else:
            return str(random.randint(DUMMY_MIN, DUMMY_MAX))
    except ValueError:
        return original   # 숫자가 아니면 그대로


# ── 메인 처리 ──────────────────────────────────────────────────────────────
def process_file(src_path: str, dst_path: str):
    with open(src_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        value_cols = [c for c in fieldnames if VALUE_COL_PATTERN.match(c)]

        rows = []
        for row in reader:
            for col in value_cols:
                row[col] = dummy_number(row[col])
            rows.append(row)

    with open(dst_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(value_cols), len(rows)


def main():
    files = [f for f in os.listdir(SRC_DIR) if is_target(f)]
    files.sort()

    print(f"대상 파일: {len(files)}개  →  저장 위치: {DST_DIR}\n")

    for fname in files:
        src = os.path.join(SRC_DIR, fname)
        dst = os.path.join(DST_DIR, fname)
        try:
            n_cols, n_rows = process_file(src, dst)
            print(f"  OK  {fname}  (value cols {n_cols} x {n_rows} rows)")
        except Exception as e:
            print(f"  FAIL  {fname}  : {e}")

    print(f"\n완료. {DST_DIR} 확인하세요.")


if __name__ == "__main__":
    main()
