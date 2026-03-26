"""
update_schedule.py

1. 26_md_schedule_260323(자동정제).xlsx 를 오늘 날짜 사본으로 복사
2. 1.고객 법인 일정 파일/ 폴더에서 최신 파일 자동 선택
   - 정렬 기준: 파일명 내 날짜(YYMMDD) → 버전(_vX.XX) → 끝 번호(_2 등)
3. 소스 파일 첫 번째 시트 B3:J(마지막 데이터 행) 값 읽기
   - datetime → yyyy-mm-dd 문자열 변환
   - WEEKNUM 수식 셀 → W01 형식 변환
4. 사본의 '고객법인일정파일' 시트 B2:K999 클리어 후 B2부터 값 붙여넣기 (서식 제외)
"""

import re
import datetime as dt
from pathlib import Path
import openpyxl


# ── 최신 파일 정렬 키 ────────────────────────────────────────
def latest_file_key(f: Path):
    """파일명에서 (날짜, 버전, 끝번호) 추출해 정렬 키로 반환.
    예) _v0.441_260325_2.xlsx → (260325, 0.441, 2)
    """
    name = f.stem
    date    = int(m.group()) if (m := re.search(r'(?<!\d)\d{6}(?!\d)', name)) else 0
    version = float(m.group(1)) if (m := re.search(r'_v(\d+\.\d+)', name)) else 0.0
    suffix  = int(m.group(1)) if (m := re.search(r'_(\d{1,5})$', name)) else 0
    return (date, version, suffix)


# ── 경로 설정 ────────────────────────────────────────────────
BASE = Path(
    r"C:\Users\user_name\OneDrive - company_name"
    r"\Project_KR_Digital Intelligence - 1 삼성 - 02 GMO Demand Generation"
    r"\part_name\2026\# CAMPAIGN_PROJECTS\02. CAMPAIGN NAME\02. SCHEDULE"
)

SOURCE_FOLDER = BASE / "1.고객 법인 일정 파일"
TARGET_SHEET  = "고객법인일정파일"

# ── Auto 파일 자동 탐색 ──────────────────────────────────────
auto_files = list(BASE.glob("*Auto*.xlsx"))
if not auto_files:
    raise FileNotFoundError(f"Auto 파일을 찾을 수 없습니다: {BASE}")
output_file = auto_files[0]
print(f"[업데이트 대상] {output_file.name}")

# ── 소스 폴더에서 최신 파일 선택 ────────────────────────────
xlsx_files = sorted(SOURCE_FOLDER.glob("*.xlsx"), key=latest_file_key)
if not xlsx_files:
    raise FileNotFoundError(f"소스 폴더에 xlsx 파일이 없습니다: {SOURCE_FOLDER}")

source_file = xlsx_files[-1]
print(f"[소스 파일] {source_file.name}")

# ── Pass 1: WEEKNUM 수식이 있는 셀 위치 파악 ─────────────────
src_wb_raw = openpyxl.load_workbook(source_file, data_only=False)
src_ws_raw = src_wb_raw.worksheets[0]

weeknum_cells = set()
for row in src_ws_raw.iter_rows(min_row=3, min_col=2, max_col=10):
    for cell in row:
        if (
            cell.value
            and isinstance(cell.value, str)
            and "WEEKNUM" in cell.value.upper()
        ):
            weeknum_cells.add((cell.row, cell.column))

src_wb_raw.close()
print(f"[WEEKNUM 셀] {len(weeknum_cells)}개 감지")

# ── Pass 2: 실제 값 읽기 ─────────────────────────────────────
src_wb = openpyxl.load_workbook(source_file, data_only=True)
src_ws = src_wb.worksheets[0]
print(f"[소스 시트] {src_ws.title}")

src_data = []
for row in src_ws.iter_rows(min_row=3, min_col=2, max_col=10):  # B3:J
    if all(cell.value is None for cell in row):
        continue  # 완전 빈 행 스킵
    row_data = []
    for cell in row:
        v = cell.value
        # WEEKNUM 수식 셀 → W01 형식
        if (cell.row, cell.column) in weeknum_cells and v and isinstance(v, (int, float)):
            v = f"W{int(v):02d}"
        # datetime → date로 변환 (시간 정보 제거, Excel 날짜값 유지)
        elif isinstance(v, dt.datetime):
            v = v.date()
        row_data.append(v)
    src_data.append(row_data)

src_wb.close()
print(f"[읽은 행 수] {len(src_data)}행")

# ── 타겟 파일 업데이트 ───────────────────────────────────────
try:
    tgt_wb = openpyxl.load_workbook(output_file)
except PermissionError:
    print(f"[SKIP] 파일이 사용 중입니다. 다음 실행 시 재시도합니다: {output_file.name}")
    exit(0)

if TARGET_SHEET not in tgt_wb.sheetnames:
    raise ValueError(f"'{TARGET_SHEET}' 시트를 찾을 수 없습니다. 시트 목록: {tgt_wb.sheetnames}")

tgt_ws = tgt_wb[TARGET_SHEET]

# D1에 소스 파일명 기록
tgt_ws.cell(row=1, column=4, value=source_file.name)

# B2:K999 값 클리어 (서식 유지)
for row in tgt_ws.iter_rows(min_row=2, max_row=999, min_col=2, max_col=11):
    for cell in row:
        cell.value = None

# B2부터 값 붙여넣기
for r_idx, row_data in enumerate(src_data, start=2):
    for c_idx, value in enumerate(row_data, start=2):  # B열=2
        tgt_ws.cell(row=r_idx, column=c_idx, value=value)

try:
    tgt_wb.save(output_file)
    tgt_wb.close()
    print(f"[완료] {output_file.name} 저장 완료")
except PermissionError:
    tgt_wb.close()
    print(f"[SKIP] 저장 중 파일이 잠겼습니다. 다음 실행 시 재시도합니다: {output_file.name}")
