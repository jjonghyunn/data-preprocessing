import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
SUBDIRS = ["main", "main_prior", "us_main", "us_main_prior", "last_main", "last_us_main"]

cnt_empty = 0
cnt_nonempty = 0

for subdir in SUBDIRS:
    folder = os.path.join(script_dir, subdir)
    if not os.path.isdir(folder):
        continue

    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".json"):
            continue
        if "-EMPTY" in filename:
            continue

        filepath = os.path.join(folder, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            data = json.loads(content) if content else {}
            is_empty = (not content) or (data == {}) or (data == [])
        except Exception:
            is_empty = False

        if is_empty:
            new_name = filename[:-5] + "-EMPTY.json"
            new_path = os.path.join(folder, new_name)
            os.rename(filepath, new_path)
            print(f"  ○ EMPTY → 이름변경: {subdir}/{filename} → {new_name}")
            cnt_empty += 1
        else:
            print(f"  ✔ 내용있음 (유지): {subdir}/{filename}")
            cnt_nonempty += 1

print(f"
{'─'*40}")
print(f"내용 있음  : {cnt_nonempty}개")
print(f"빈 파일    : {cnt_empty}개  (파일명에 -EMPTY 추가됨)")
print(f"합계       : {cnt_nonempty + cnt_empty}개")
