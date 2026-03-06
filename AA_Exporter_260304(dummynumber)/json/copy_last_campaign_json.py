import os
import shutil

# ──────────────────────────────────────────────
# ▶ 연도 설정 (매년 여기만 수정)
#   FROM_YEAR : 현재 캠페인 연도 (복사 원본 기준)
#   TO_YEAR   : 자동 계산됨 (FROM_YEAR - 1)
# ──────────────────────────────────────────────
FROM_YEAR = 26   # 내년에 27_파일 생길 경우 → 27로 변경
TO_YEAR   = FROM_YEAR - 1

FROM_PREFIX    = f"{FROM_YEAR}_"
TO_PREFIX      = f"{TO_YEAR}_"
FROM_PREFIX_US = f"us_{FROM_YEAR}_"
TO_PREFIX_US   = f"us_{TO_YEAR}_"

# ──────────────────────────────────────────────

script_dir = os.path.dirname(os.path.abspath(__file__))

print(f"복사 방향: {FROM_PREFIX}* → {TO_PREFIX}*  /  {FROM_PREFIX_US}* → {TO_PREFIX_US}*")
print(f"{'─'*50}")

cnt = 0
for filename in sorted(os.listdir(script_dir)):
    if not filename.endswith(".json"):
        continue
    if "_prior" in filename:
        continue  # prior 파일은 copy_prior_json.py 에서 처리

    if filename.startswith(FROM_PREFIX_US):
        dst_name = TO_PREFIX_US + filename[len(FROM_PREFIX_US):]
    elif filename.startswith(FROM_PREFIX):
        dst_name = TO_PREFIX + filename[len(FROM_PREFIX):]
    else:
        continue  # 대상 연도 파일 아님 → 건드리지 않음

    src = os.path.join(script_dir, filename)
    dst = os.path.join(script_dir, dst_name)
    shutil.copy2(src, dst)
    print(f"  복사: {filename} → {dst_name}")
    cnt += 1

print(f"{'─'*50}")
print(f"완료: {cnt}개 복사됨")
