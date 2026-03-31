import os
import shutil

# ──────────────────────────────────────────────────────────────
# ▶ 현재 캠페인 json을 last year용으로 복사
#   main/X.json        → last_main/last_X.json
#   us_main/us_X.json  → last_us_main/last_us_X.json
#
# ※ prior 파일은 copy_prior_json.py 에서 처리
# ──────────────────────────────────────────────────────────────

script_dir  = os.path.dirname(os.path.abspath(__file__))
main_dir    = os.path.join(script_dir, "main")
last_dir    = os.path.join(script_dir, "last_main")
us_dir      = os.path.join(script_dir, "us_main")
last_us_dir = os.path.join(script_dir, "last_us_main")

print("복사 방향: main/* → last_main/last_*  /  us_main/* → last_us_main/last_us_*")
print("─" * 60)

cnt = 0

# ── 글로벌: main/ → last_main/ ───────────────────────────────
for filename in sorted(os.listdir(main_dir)):
    if not filename.endswith(".json"):
        continue
    if "_prior" in filename:
        continue  # prior 파일은 copy_prior_json.py 에서 처리

    dst_name = "last_" + filename
    src = os.path.join(main_dir, filename)
    dst = os.path.join(last_dir, dst_name)
    shutil.copy2(src, dst)
    print(f"  복사: main/{filename} → last_main/{dst_name}")
    cnt += 1

# ── US: us_main/ → last_us_main/ ────────────────────────────
for filename in sorted(os.listdir(us_dir)):
    if not filename.endswith(".json"):
        continue
    if "_prior" in filename:
        continue

    dst_name = "last_" + filename   # us_X.json → last_us_X.json
    src = os.path.join(us_dir, filename)
    dst = os.path.join(last_us_dir, dst_name)
    shutil.copy2(src, dst)
    print(f"  복사: us_main/{filename} → last_us_main/{dst_name}")
    cnt += 1

print("─" * 60)
print(f"완료: {cnt}개 복사됨")
