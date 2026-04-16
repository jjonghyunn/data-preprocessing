import os
import csv

TARGET_DIR = os.path.join(os.path.dirname(__file__), "aa_exports")

def check_failed():
    failed_report = []  # (파일명, FAILED 행 수)
    skipped = []
    no_status = []

    files = [
        f for f in os.listdir(TARGET_DIR)
        if f.endswith(".csv")
        and f != "separate.csv"
        and not f.lower().startswith("union")
        and "separate" not in f.lower()  # *_separate.csv 제외
    ]

    print(f"검사 대상 파일 수: {len(files)}\n")

    for fname in sorted(files):
        fpath = os.path.join(TARGET_DIR, fname)
        try:
            with open(fpath, encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                if headers is None:
                    skipped.append((fname, "헤더 없음"))
                    continue

                # 대소문자 무관하게 status 컬럼 찾기
                status_col = next((h for h in headers if h.strip().lower() == "status"), None)
                if status_col is None:
                    no_status.append(fname)
                    continue

                failed_count = sum(
                    1 for row in reader
                    if row.get(status_col, "").strip().upper() == "FAILED"
                )

                if failed_count > 0:
                    failed_report.append((fname, failed_count))

        except Exception as e:
            skipped.append((fname, str(e)))

    # 결과 출력
    print("=" * 60)
    if failed_report:
        print(f"[FAILED 발견] {len(failed_report)}개 파일:")
        for fname, cnt in failed_report:
            print(f"  ❌  {fname}  ({cnt}건)")
    else:
        print("[OK] FAILED 상태인 파일 없음")

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
