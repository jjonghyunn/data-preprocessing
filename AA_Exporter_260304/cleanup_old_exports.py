# cleanup_old_exports.py
# 2026-04-24  Jonghyun Park w/ Claude
"""
aa_exports 폴더의 타임스탬프 붙은 CSV 중 base_key별 최신 1개만 남기고 나머지를 삭제.

[사용법]
    python cleanup_old_exports.py
    → 삭제 후보를 먼저 출력하고 y/N 확인 후 실제 삭제

[대상 폴더 탐색]
    1) 스크립트 옆 aa_exports/ 에 CSV가 있으면 그걸 대상으로
    2) 없거나 비어있으면 ../aa_exports/ 를 대상으로
    → 루트 또는 launch/ 어느 쪽에 두어도 동작

[파일 그룹핑 기준]
    파일명에 YYYYMMDD_HHMMSS 또는 YYYYMMDD_HHMM 패턴이 있어야 그룹 대상.
    base_key = 파일명에서 타임스탬프 부분 제거한 것.
    각 base_key 그룹의 최신 1개만 남기고 나머지는 삭제 후보.

[항상 보존]
    - 파일명에 타임스탬프 패턴이 없는 파일
    - 'union' 으로 시작하는 파일 (최종 병합 결과)
"""

import os
import re
from datetime import datetime


def _resolve_target():
    here = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(here, "aa_exports")
    if os.path.isdir(local) and any(f.lower().endswith(".csv") for f in os.listdir(local)):
        return local
    return os.path.join(here, "..", "aa_exports")


TARGET_DIR = _resolve_target()

DT_PATTERNS = [
    (r"(\d{8})_(\d{6})", "%Y%m%d%H%M%S"),
    (r"(\d{8})_(\d{4})",  "%Y%m%d%H%M"),
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


def cleanup():
    if not os.path.isdir(TARGET_DIR):
        print(f"폴더 없음: {TARGET_DIR}")
        return

    files = os.listdir(TARGET_DIR)
    groups = {}         # base_key -> list[(fname, dt)]
    no_dt_files = []    # datetime 패턴 없는 파일 (보존)

    for f in files:
        fpath = os.path.join(TARGET_DIR, f)
        if not os.path.isfile(fpath):
            continue
        if f.lower().startswith("union"):
            no_dt_files.append(f)
            continue
        dt = extract_dt(f)
        if dt is None:
            no_dt_files.append(f)
            continue
        groups.setdefault(base_key(f), []).append((f, dt))

    to_delete = []
    kept = []
    for k, lst in groups.items():
        lst.sort(key=lambda x: x[1], reverse=True)
        kept.append(lst[0][0])
        to_delete.extend(f for f, _ in lst[1:])

    print(f"대상 폴더: {TARGET_DIR}")
    print(f"타임스탬프 있는 파일 그룹: {len(groups)}개 (유지 {len(kept)})")
    print(f"타임스탬프 없는 파일 (보존): {len(no_dt_files)}개")
    print(f"삭제 후보: {len(to_delete)}개")
    print("=" * 60)

    if not to_delete:
        print("삭제할 파일 없음")
        return

    for f in to_delete:
        print(f"  - {f}")
    print("=" * 60)

    resp = input(f"위 {len(to_delete)}개 파일을 삭제할까요? (y/N): ").strip().lower()
    if resp != "y":
        print("취소됨")
        return

    deleted, failed = 0, []
    for f in to_delete:
        try:
            os.remove(os.path.join(TARGET_DIR, f))
            deleted += 1
        except Exception as e:
            failed.append((f, str(e)))

    print(f"\n삭제 완료: {deleted}/{len(to_delete)}개")
    if failed:
        print(f"실패 {len(failed)}개:")
        for f, reason in failed:
            print(f"  !  {f}: {reason}")


if __name__ == "__main__":
    cleanup()
