import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))

cnt_empty = 0
cnt_nonempty = 0

for filename in sorted(os.listdir(script_dir)):
    if not filename.endswith(".json"):
        continue
    if "-EMPTY" in filename:
        continue

    filepath = os.path.join(script_dir, filename)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        data = json.loads(content) if content else {}
        is_empty = (not content) or (data == {}) or (data == [])
    except Exception:
        is_empty = False

    if is_empty:
        new_name = filename[:-5] + "-EMPTY.json"
        new_path = os.path.join(script_dir, new_name)
        os.rename(filepath, new_path)
        print(f"  ○ EMPTY → 이름변경: {filename} → {new_name}")
        cnt_empty += 1
    else:
        print(f"  ✔ 내용있음 (유지): {filename}")
        cnt_nonempty += 1

print(f"\n{'─'*40}")
print(f"내용 있음  : {cnt_nonempty}개")
print(f"빈 파일    : {cnt_empty}개  (파일명에 -EMPTY 추가됨)")
print(f"합계       : {cnt_nonempty + cnt_empty}개")
