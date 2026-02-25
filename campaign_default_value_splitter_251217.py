import os
import re
import pandas as pd
from datetime import datetime

# =========================
# 📁 경로 설정
# =========================
base_dir = r'C:\Users\{username}\Downloads'

# 📄 원본 파일명
csv_filename = 'filename.csv'

# 📌 전체 경로
csv_path = os.path.join(base_dir, csv_filename)

# 입력 파일명에서 확장자 제거
base_name = os.path.splitext(csv_filename)[0]
# 맨 뒤의 6자리 날짜 제거 (예: _251217)
base_name_cleaned = re.sub(r'_\d{6}$', '', base_name)


# =========================
# 📥 CSV 불러오기
# =========================
df = pd.read_csv(csv_path)

# =========================
# 🔧 metric 분리 함수
# =========================
def custom_split(metric: str):
    parts = str(metric).split('_')
    result = []

    # 1️⃣ 맨 앞 1_1 묶기
    if len(parts) >= 2:
        result.append(f"{parts[0]}_{parts[1]}")
        idx = 2
    else:
        return [metric]

    # 2️⃣ 나머지 토큰 처리
    while idx < len(parts):
        part = parts[idx]

        # 🔎 20## 연도 감지 → 다음 토큰과 결합
        if re.fullmatch(r'20\d{2}', part) and idx + 1 < len(parts):
            result.append(f"{part}_{parts[idx + 1]}")
            idx += 2
        else:
            result.append(part)
            idx += 1

    return result

# =========================
# 🔁 metric 컬럼 전체 적용
# =========================
split_series = df['metric'].apply(custom_split)

# 최대 분리 개수
max_split_len = split_series.map(len).max()

# =========================
# ➕ split 컬럼 생성
# =========================
for i in range(max_split_len):
    df[f'split{i+1}'] = split_series.apply(
        lambda x: x[i] if i < len(x) else ''
    )

# =========================
# 🕒 저장 파일명 생성
# =========================
date_time_suffix = datetime.now().strftime('%y%m%d_%H%M%S')

output_filename = f"{base_name_cleaned}_{date_time_suffix}.csv"
output_path = os.path.join(base_dir, output_filename)

# =========================
# 💾 저장
# =========================
df.to_csv(output_path, index=False, encoding='utf-8-sig')

print('✅ 처리 완료')
print(f'📄 저장 파일: {output_path}')

