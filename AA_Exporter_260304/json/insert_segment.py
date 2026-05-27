# insert_segment.py
# 2026-04-24  Jonghyun Park w/ Claude
"""
json/ 하위 모든 서브폴더의 JSON에서
    "type": "dateRange",
를
    "type": "segment","segmentId": "{SEGMENT_ID}" }, {             "type": "dateRange",
로 치환한다. dateRange 엔트리 앞에 segment 엔트리를 삽입하는 효과.

[전제]
    이미 파일 본문에 SEGMENT_ID 문자열이 포함되어 있으면 중복 처리 방지를 위해 해당 파일은 건너뜀.

[사용법]
    python insert_segment.py                  # test 포함 파일 제외 (기본)
    python insert_segment.py --include-test   # test 포함 파일도 처리
    python insert_segment.py --dry-run        # 대상 목록만 보고 실제 수정 안 함
    (여러 옵션 조합 가능)

[설정]
    JSON_ROOT  : 스캔 시작 폴더 (기본: 스크립트 옆 json/)
    SEGMENT_ID : 삽입할 세그먼트 ID — 실제 값으로 갈아끼운 뒤 실행
"""

import os
import sys
from pathlib import Path

JSON_ROOT  = Path(os.path.dirname(os.path.abspath(__file__))) / "json"
SEGMENT_ID = "세그먼트_아이디_넘버"  # 실제 값(s\d{9}_[0-9a-f]{24})으로 교체 후 실행

SEARCH  = '"type": "dateRange",'
REPLACE = '"type": "segment","segmentId": "' + SEGMENT_ID + '" }, {             "type": "dateRange",'


def collect_targets(include_test: bool):
    if not JSON_ROOT.is_dir():
        print(f"폴더 없음: {JSON_ROOT}")
        return []
    files = list(JSON_ROOT.rglob("*.json"))
    if not include_test:
        files = [p for p in files if "test" not in p.name.lower()]
    return files


def classify(files):
    to_modify, already_done, no_match, read_fail = [], [], [], []
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:
            read_fail.append((p, str(e)))
            continue
        if SEGMENT_ID in text:
            already_done.append(p)
        elif SEARCH not in text:
            no_match.append(p)
        else:
            to_modify.append((p, text))
    return to_modify, already_done, no_match, read_fail


def summarize(to_modify, already_done, no_match, read_fail):
    print(f"수정 대상            : {len(to_modify)}개")
    print(f"이미 SEGMENT_ID 포함 : {len(already_done)}개 (스킵)")
    print(f"dateRange 패턴 없음  : {len(no_match)}개 (스킵)")
    print(f"읽기 실패            : {len(read_fail)}개")
    print("=" * 60)
    if to_modify:
        print("[수정 예정]")
        for p, _ in to_modify:
            print(f"  + {p.relative_to(JSON_ROOT)}")
    if already_done:
        print("[스킵 - 이미 처리됨]")
        for p in already_done:
            print(f"  = {p.relative_to(JSON_ROOT)}")
    if read_fail:
        print("[읽기 실패]")
        for p, err in read_fail:
            print(f"  !  {p.relative_to(JSON_ROOT)}: {err}")


def apply(to_modify):
    written, failed = [], []
    for p, text in to_modify:
        try:
            p.write_text(text.replace(SEARCH, REPLACE), encoding="utf-8")
            written.append(p)
        except Exception as e:
            failed.append((p, str(e)))
    print(f"\n수정 완료: {len(written)}/{len(to_modify)}개")
    if failed:
        print(f"실패 {len(failed)}개:")
        for p, err in failed:
            print(f"  !  {p.relative_to(JSON_ROOT)}: {err}")


def main():
    include_test = "--include-test" in sys.argv
    dry_run      = "--dry-run" in sys.argv

    print(f"JSON_ROOT : {JSON_ROOT}")
    print(f"SEGMENT_ID: {SEGMENT_ID}")
    print(f"옵션       : include_test={include_test}, dry_run={dry_run}")
    print("=" * 60)

    files = collect_targets(include_test)
    if not files:
        print("대상 파일 없음")
        return

    to_modify, already_done, no_match, read_fail = classify(files)
    summarize(to_modify, already_done, no_match, read_fail)

    if dry_run:
        print("\n[dry-run] 실제 수정 없이 종료")
        return

    if not to_modify:
        print("\n수정할 파일 없음")
        return

    resp = input(f"\n위 {len(to_modify)}개 파일을 수정할까요? (y/N): ").strip().lower()
    if resp != "y":
        print("취소됨")
        return

    apply(to_modify)


if __name__ == "__main__":
    main()
