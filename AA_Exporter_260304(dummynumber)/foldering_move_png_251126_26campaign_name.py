# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★★★★★ MO 파일 먼저 옮기고 실행하기!! ★★★★★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

import os
import shutil
import re

# 원본 폴더 경로
folder_path = r"C:\Users\user_name\OneDrive - company_name\Project_team_name - 1 company_name - 02 part_name\part_name\2026\CAMPAIGN_ADHOC\01.CAMPAIGN NAME (260331~)\03.MONITORING"

# 파일 리스트 가져오기
file_list = [f for f in os.listdir(folder_path) if f.endswith(".png") or f.endswith(".mhtml")]

# 정리 시작
for file_name in file_list:
    # PC 또는 MO 앞까지 추출 (공백이나 언더바 포함)
    match = re.match(r"(.+?)[ _](PC|MO)", file_name)
    if match:
        folder_name = match.group(1).replace(" ", "_")  # 공백 → 언더바 처리
        dest_folder = os.path.join(folder_path, folder_name)

        # 폴더 없으면 생성
        os.makedirs(dest_folder, exist_ok=True)

        # 파일 이동
        src_path = os.path.join(folder_path, file_name)
        dest_path = os.path.join(dest_folder, file_name)
        shutil.move(src_path, dest_path)
        print(f"Moved: {file_name} -> {folder_name}/")
    else:
        print(f"Skipped: {file_name}")
