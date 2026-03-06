import os
import shutil

script_dir = os.path.dirname(os.path.abspath(__file__))

for filename in os.listdir(script_dir):
    if filename.endswith("_prior.json"):
        src = os.path.join(script_dir, filename)
        dst_name = filename.replace("_prior.json", ".json")

        if dst_name.startswith("us_26_"):
            dst_name = "us_25_" + dst_name[6:]
        elif dst_name.startswith("26_"):
            dst_name = "25_" + dst_name[3:]

        dst = os.path.join(script_dir, dst_name)
        shutil.copy2(src, dst)
        print(f"복사 완료: {filename} → {dst_name}")
