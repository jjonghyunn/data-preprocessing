import os
import shutil
import re

script_dir = os.path.dirname(os.path.abspath(__file__))

for filename in os.listdir(script_dir):
    if filename.endswith(".json") and "_prior" not in filename:
        match = re.match(r'^(\d{2})(.+\.json)$', filename)
        if match:
            prefix = int(match.group(1))
            rest = match.group(2)
            new_name = f"{prefix - 1:02d}{rest}"
            src = os.path.join(script_dir, filename)
            dst = os.path.join(script_dir, new_name)
            shutil.copy2(src, dst)