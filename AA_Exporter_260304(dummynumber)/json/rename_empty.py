import os

script_dir = os.path.dirname(os.path.abspath(__file__))
SUBDIRS = ["main", "main_prior", "us_main", "us_main_prior", "last_main", "last_us_main"]

cnt = 0
for subdir in SUBDIRS:
    folder = os.path.join(script_dir, subdir)
    if not os.path.isdir(folder):
        continue

    for filename in os.listdir(folder):
        if filename.endswith("-EMPTY.json"):
            new_name = filename.replace("-EMPTY.json", ".json")
            src = os.path.join(folder, filename)
            dst = os.path.join(folder, new_name)
            os.rename(src, dst)
            print(f"{subdir}/{filename} → {new_name}")
            cnt += 1

print(f"완료: {cnt}개")
