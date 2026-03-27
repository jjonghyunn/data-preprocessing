"""
update_schedule.py

1. 1.고객 법인 일정 파일/ 폴더에서 최신 파일 자동 선택
   - 정렬 기준: 파일명 내 날짜(YYMMDD) → 버전(_vX.XX) → 끝 번호(_2 등)
2. 소스 파일 첫 번째 시트 B3:J(마지막 데이터 행) 값 읽기
   - datetime → yyyy-mm-dd 문자열 변환
   - WEEKNUM 수식 셀 → W01 형식 변환
3. Auto 파일의 '고객법인일정파일' 시트 B2:K999 클리어 후 B2부터 값 붙여넣기 (서식 제외)
"""

import re
import datetime as dt
from pathlib import Path
import openpyxl
from openpyxl.styles import PatternFill
import win32com.client

CHANGED_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
NO_FILL      = PatternFill(fill_type=None)


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
    r"\Project_team_name - 1 company_name - 02 part_name"
    r"\part_name\2026\# CAMPAIGN_PROJECTS\02. CAMPAIGN NAME\02. SCHEDULE"
)

SOURCE_FOLDER = BASE / "1.고객 법인 일정 파일"
TARGET_SHEET  = "고객법인일정파일"
LAST_SOURCE_FILE = Path(r"C:\Users\user_name\Documents\schedule_last_source.txt")

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

# 소스 파일이 이전과 동일하면 업데이트 불필요 → 스킵 (로컬 마커 파일 기준)
if LAST_SOURCE_FILE.exists() and LAST_SOURCE_FILE.read_text(encoding="utf-8").strip() == source_file.name:
    print(f"[SKIP] 소스 파일 변경 없음 ({source_file.name}), 업데이트 생략")
    exit(0)

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

# ── 이전 파일 읽기 (전후 비교용) ──────────────────────────────
prev_data = {}
if len(xlsx_files) >= 2:
    prev_file = xlsx_files[-2]
    prev_wb_raw = openpyxl.load_workbook(prev_file, data_only=False)
    prev_ws_raw = prev_wb_raw.worksheets[0]
    prev_weeknum_cells = set()
    for row in prev_ws_raw.iter_rows(min_row=3, min_col=2, max_col=10):
        for cell in row:
            if cell.value and isinstance(cell.value, str) and "WEEKNUM" in cell.value.upper():
                prev_weeknum_cells.add((cell.row, cell.column))
    prev_wb_raw.close()

    prev_wb = openpyxl.load_workbook(prev_file, data_only=True)
    prev_ws = prev_wb.worksheets[0]
    for row in prev_ws.iter_rows(min_row=3, min_col=2, max_col=10):
        if all(cell.value is None for cell in row):
            continue
        row_data = []
        for cell in row:
            v = cell.value
            if (cell.row, cell.column) in prev_weeknum_cells and v and isinstance(v, (int, float)):
                v = f"W{int(v):02d}"
            elif isinstance(v, dt.datetime):
                v = v.date()
            row_data.append(v)
        subs_key = row_data[1]  # C열
        if subs_key:
            prev_data[subs_key] = row_data
    prev_wb.close()
    print(f"[이전 파일] {prev_file.name} ({len(prev_data)}행 로드)")

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

# B2:K999 값·음영 클리어 (서식 유지)
for row in tgt_ws.iter_rows(min_row=2, max_row=999, min_col=2, max_col=11):
    for cell in row:
        cell.value = None
        cell.fill  = NO_FILL

# B2부터 값 붙여넣기
for r_idx, row_data in enumerate(src_data, start=2):
    for c_idx, value in enumerate(row_data, start=2):  # B열=2
        cell = tgt_ws.cell(row=r_idx, column=c_idx, value=value)
        if isinstance(value, dt.date):
            cell.number_format = "YYYY-MM-DD"

# 변경 셀 음영 표시 (E=Participation, F=Start at, H=End at)
# src_data index: 3=E, 4=F, 6=H  /  target column: 5=E, 6=F, 8=H
COMPARE = {3: 5, 4: 6, 6: 8}
if prev_data:
    changed_count = 0
    for r_idx, row_data in enumerate(src_data, start=2):
        subs_key = row_data[1]  # C열
        if not subs_key or subs_key not in prev_data:
            continue
        prev_row = prev_data[subs_key]
        for src_idx, tgt_col in COMPARE.items():
            cur_val  = row_data[src_idx] if src_idx < len(row_data) else None
            prv_val  = prev_row[src_idx] if src_idx < len(prev_row) else None
            if cur_val != prv_val:
                tgt_ws.cell(row=r_idx, column=tgt_col).fill = CHANGED_FILL
                changed_count += 1
    print(f"[변경 셀] {changed_count}개 음영 표시")

try:
    tgt_wb.save(output_file)
    tgt_wb.close()
except PermissionError:
    tgt_wb.close()
    print(f"[SKIP] 저장 중 파일이 잠겼습니다. 다음 실행 시 재시도합니다: {output_file.name}")
    exit(0)

# Excel로 열어서 전체 재계산 후 저장 (FILTER/SORT 등 동적 배열 함수 반영)
excel = win32com.client.Dispatch("Excel.Application")
excel.Visible = False
try:
    wb_com = excel.Workbooks.Open(str(output_file.resolve()))
    excel.CalculateFull()
    wb_com.Save()
    wb_com.Close()
    LAST_SOURCE_FILE.write_text(source_file.name, encoding="utf-8")
    print(f"[완료] {output_file.name} 저장 완료")
finally:
    excel.Quit()
