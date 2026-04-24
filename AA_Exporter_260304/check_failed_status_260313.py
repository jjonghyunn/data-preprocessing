# check_failed_status_260313.py
# 2026-04-24  Jonghyun Park w/ Claude

import os
import csv
import re
from datetime import datetime

TARGET_DIR = os.path.join(os.path.dirname(__file__), "aa_exports")

DT_PATTERNS = [
    (r"(\d{8})_(\d{6})", "%Y%m%d%H%M%S"),  # YYYYMMDD_HHMMSS
    (r"(\d{8})_(\d{4})",  "%Y%m%d%H%M"),    # YYYYMMDD_HHMM
]

def extract_dt(fname):
    for pattern, fmt in DT_PATTERNS:
        m = re.search(pattern, fname)
        if m:
            try:
                return datetime.strptime(m.group(1) + m.group(2), fmt)
            except ValueError:
                pass
    return None

def base_key(fname):
    key = re.sub(r"_\d{8}_\d{6}", "", fname)
    key = re.sub(r"_\d{8}_\d{4}", "", key)
    return key

def pick_latest(files):
    """datetime 패턴 있는 파일은 base_key 별 최신 1개만, 없는 파일은 그대로."""
    dated, undated = [], []
    for f in files:
        if extract_dt(f) is not None:
            dated.append(f)
        else:
            undated.append(f)

    groups = {}
    for f in dated:
        k = base_key(f)
        dt = extract_dt(f)
        if k not in groups or dt > groups[k][1]:
            groups[k] = (f, dt)

    return undated + [v[0] for v in groups.values()]

def check_failed():
    failed_report = []
    us_empty_report = []
    skipped = []
    no_status = []

    all_files = [
        f for f in os.listdir(TARGET_DIR)
        if f.endswith(".csv")
        and f != "separate.csv"
        and not f.lower().startswith("union")
        and "separate" not in f.lower()
        and not f.lower().startswith("_stacked")
    ]

    files = sorted(pick_latest(all_files))
    print(f"검사 대상 파일 수: {len(files)}  (전체 {len(all_files)}개 중 최신만)\n")

    for fname in files:
        fpath = os.path.join(TARGET_DIR, fname)
        is_us = fname.lower().startswith("us_") or fname.lower().startswith("last_us_")

        try:
            with open(fpath, encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                if headers is None:
                    skipped.append((fname, "헤더 없음"))
                    continue

                status_col = next((h for h in headers if h.strip().lower() == "status"), None)
                if status_col is None:
                    no_status.append(fname)
                    continue

                failed_count = 0
                ok_count = 0
                for row in reader:
                    s = row.get(status_col, "").strip().upper()
                    if s == "FAILED":
                        failed_count += 1
                    elif s == "OK":
                        ok_count += 1

                if failed_count > 0:
                    failed_report.append((fname, failed_count))

                if is_us and ok_count == 0:
                    us_empty_report.append((fname, failed_count))

        except Exception as e:
            skipped.append((fname, str(e)))

    print("=" * 60)

    if failed_report:
        print(f"[FAILED 발견] {len(failed_report)}개 파일:")
        for fname, cnt in failed_report:
            print(f"  ❌  {fname}  ({cnt}건)")
    else:
        print("[OK] FAILED 상태인 파일 없음")

    if us_empty_report:
        print(f"\n[US 데이터 없음] {len(us_empty_report)}개 파일 (OK 행 0개):")
        for fname, failed_cnt in us_empty_report:
            note = f"FAILED {failed_cnt}건" if failed_cnt > 0 else "추출 값 없음"
            print(f"  ⚠️  {fname}  ({note})")
    else:
        us_files = [f for f in files if f.lower().startswith("us_") or f.lower().startswith("last_us_")]
        if us_files:
            print(f"\n[US OK] US 파일 {len(us_files)}개 모두 데이터 있음")

    if no_status:
        print(f"\n[참고] status 컬럼 없는 파일 ({len(no_status)}개):")
        for fname in no_status:
            print(f"  -  {fname}")

    if skipped:
        print(f"\n[오류] 읽기 실패 파일 ({len(skipped)}개):")
        for fname, reason in skipped:
            print(f"  !  {fname}: {reason}")

    print("=" * 60)

if __name__ == "__main__":
    check_failed()
