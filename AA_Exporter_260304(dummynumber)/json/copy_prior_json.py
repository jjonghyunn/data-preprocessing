import os
import shutil

# ──────────────────────────────────────────────────────────────
# ▶ prior json을 main(TY) + last_main(LY) 양쪽으로 복사
#   main_prior/X_prior.json       → main/X.json
#                                 → last_main/last_X.json
#   us_main_prior/us_X_prior.json → us_main/us_X.json
#                                 → last_us_main/last_us_X.json
# ──────────────────────────────────────────────────────────────

script_dir   = os.path.dirname(os.path.abspath(__file__))
main_prior   = os.path.join(script_dir, "main_prior")
main_dir     = os.path.join(script_dir, "main")
last_dir     = os.path.join(script_dir, "last_main")
us_prior     = os.path.join(script_dir, "us_main_prior")
us_dir       = os.path.join(script_dir, "us_main")
last_us_dir  = os.path.join(script_dir, "last_us_main")

cnt = 0

# ── 글로벌: main_prior/ → main/ + last_main/ ─────────────────
print("[글로벌]")
for filename in sorted(os.listdir(main_prior)):
    if not filename.endswith("_prior.json"):
        continue

    base_name = filename.replace("_prior.json", ".json")   # X_prior.json → X.json
    last_name = "last_" + base_name                          # → last_X.json

    src = os.path.join(main_prior, filename)

    dst1 = os.path.join(main_dir, base_name)
    shutil.copy2(src, dst1)
    print(f"  {filename} → main/{base_name}")

    dst2 = os.path.join(last_dir, last_name)
    shutil.copy2(src, dst2)
    print(f"  {filename} → last_main/{last_name}")

    cnt += 2

# ── US: us_main_prior/ → us_main/ + last_us_main/ ────────────
print("
[US]")
for filename in sorted(os.listdir(us_prior)):
    if not filename.endswith("_prior.json"):
        continue

    base_name = filename.replace("_prior.json", ".json")   # us_X_prior.json → us_X.json
    last_name = "last_" + base_name                          # → last_us_X.json

    src = os.path.join(us_prior, filename)

    dst1 = os.path.join(us_dir, base_name)
    shutil.copy2(src, dst1)
    print(f"  {filename} → us_main/{base_name}")

    dst2 = os.path.join(last_us_dir, last_name)
    shutil.copy2(src, dst2)
    print(f"  {filename} → last_us_main/{last_name}")

    cnt += 2

print(f"
완료: {cnt}개 복사됨")
