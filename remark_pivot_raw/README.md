# remark_pivot_raw  
<sub>2026-07-29  Jonghyun Park w/ Claude</sub>  

분석 결과 xlsx / CSV 를 외부 공유용 리마킹 파일로 변환하는 스크립트 모음.  
피봇 종류(Classic / OLAP)에 따라 도구가 나뉜다.

---

## 피봇 종류별 도구

| 피봇 종류 | 도구 | 방식 |
|---|---|---|
| **Classic** (워크시트 소스) | `remark_classic.py` | xlsx raw 시트 셀 값 직접 치환 (openpyxl 안전) |
| **OLAP** (파워피봇 데이터 모델) | `remark_olap.py` | 데이터 모델 소스인 data/ CSV 를 치환 → data_fx/ 출력 |

> **OLAP 피봇 xlsx 는 openpyxl 저장 시 파일이 깨진다** → xlsx 를 직접 못 건드림.  
> 그래서 소스 CSV(`data/`)를 리마킹해 `data_fx/` 로 떨군 뒤, Excel 에서 데이터 모델 소스 경로를 `data_fx/` 로 다시 로드한다.

---

## 스크립트 목록

| 파일 | 용도 |
|---|---|
| `remark_classic.py` | **Classic 피봇** xlsx 리마킹 — raw 시트 셀 치환 + 불필요 시트 삭제 + `_remarkprefix_classic.csv` 레전드 |
| `remark_olap.py` | **OLAP 피봇** 소스 리마킹 — data/ CSV → data_fx/ + `_remarkprefix_olap.csv` 레전드 |
| `check_pivot_cache.py` | 피봇 캐시 **진단**(읽기 전용) — CLASSIC/OLAP 엔진 판별 + 차원값 추출 (마스킹 전 확인용) |

---

## 실행 순서

```
# 1a. Classic 피봇 xlsx 리마킹
python remark_classic.py   →  OUT_DIR/_remark_원본파일명.xlsx

# 1b. OLAP 피봇 소스 CSV 리마킹 (data 폴더가 있을 때)
python remark_olap.py      →  OUTPUT_DIR/data_fx/ 폴더

# ※ 출력은 입력 파일 옆이 아니라 스크립트 상단 OUT_DIR / OUTPUT_DIR 로 나간다 (레전드 csv 도 동일).

# ※ 1a/1b 실행 시 칼럼별 레전드 csv 가 자동 생성됨:
#    remark_classic.py → _remarkprefix_classic.csv
#    remark_olap.py    → _remarkprefix_olap.csv
#    (상단 PREFIX_ONLY=True 면 결과물 xlsx/data_fx 저장 생략, 레전드 csv 만 빠르게 생성)

# 2. (선택) 마스킹 전 피봇 캐시 엔진 진단 (CLASSIC/OLAP 확인)
python check_pivot_cache.py     →  remark_olap.csv / remark_classic.csv / remark_prefix.csv
```

---

## remark_classic.py

### 동작 방식
- `openpyxl.load_workbook()` 으로 **기존 xlsx 그대로 열기** (새 workbook 미생성)
- 불필요 시트 삭제 → raw 시트 셀 값 치환 → 저장
- 피봇 캐시 XML 유지 → **Excel 새로고침으로 피봇 복원 가능**

### 치환 범위
- **차원 컬럼**: sitecode / country / subs / region / channel 계열 헤더를 가진 컬럼 — xlsx 내부 값 직접 치환 (외부 CSV 조회 불필요)
- **ITEM 컬럼**: 왼쪽 열 값이 `Paid` 또는 `Non-Paid` 일 때만 조건부 치환
- **치환 안 하는 것**: 시트명, 컬럼 헤더, 숫자값, 날짜, Current/Prior/YoY 등 일반 레이블

### 새 캠페인 파일 적용 시 수정 항목

```python
# 1. 입력 파일 경로 + 출력 폴더 (둘 다 하드코딩이라 반드시 교체)
CLASSIC_XLSX = r"...새 파일.xlsx"
OUT_DIR      = r"...출력 경로"     # 결과 xlsx·레전드 csv 가 여기로 나감 (입력 폴더 아님)

# 2. 유지할 시트 목록 (새 파일 구조에 맞게 — 아래는 예시)
CLASSIC_KEEP = ["SHEET_A TRAFFIC ANALYSIS", "SHEET_A_PIVOT_1", ...]

# 3. raw 시트 + 헤더 행 번호
#    헤더가 1행이 아닌 경우가 많음 — 아래 빠른 확인법 참고
CLASSIC_RAW_HEADER_ROW = {
    "SHEET_A_RAW": 2,
    "SHEET_B":     8,
    "SHEET_C_RAW": 2,
    "SHEET_D_RAW": 1,
}
```

> **헤더 행 빠른 확인**:
> ```python
> import openpyxl
> wb = openpyxl.load_workbook("파일.xlsx", read_only=True, data_only=True)
> ws = wb["SHEET_A_RAW"]
> for i, row in enumerate(ws.iter_rows(min_row=1, max_row=5, values_only=True), 1):
>     print(i, [v for v in row if v])
> ```

---

## remark_olap.py

### 동작 방식
- OLAP(파워피봇 데이터 모델) 피봇용 — 데이터 모델 소스인 `data/dim/*.csv` + `data/fact/*.csv` 의 지정 컬럼 값을 치환
- 원본 유지, `data_fx/` 에 별도 출력 → Excel 에서 데이터 모델 소스를 `data_fx/` 로 다시 로드

### 리마킹 대상 컬럼
- 민감 식별자(`sitecode` / `region` / `subs` / `country` / `division` / `channel` 계열)만 치환. `external` fact 는 채널 컬럼명이 `variables/marketingchannel` 이라 그 이름으로 등록돼 있음
- `SegmentName` / `SegmentId` / `category` / `variables/product` / `prop6` / `evar41` / `div_1~3` 등은 기본 주석처리(미치환) — 필요 시 주석 해제

### 새 파일 적용 시 수정 항목

```python
INPUT_DIR  = r"...새 data 폴더"
OUTPUT_DIR = r"...출력 경로"

# dim: 민감 컬럼만 (region/subs/country 는 dim 에서 치환)
DIM_REMARK  = { "d_country.csv": ["sitecode", "region", "subs", "country"], ... }
# fact: sitecode/division/channel 계열만 활성, 나머지(SegmentName·category·product 등)는 주석처리
FACT_REMARK = {
    "basic_traffic": ["sitecode"],
    "external":      ["sitecode", "variables/marketingchannel"],
    "internal":      ["sitecode", "channel"],
    ...
}
```

---

## 레전드(legend) — 어떤 값이 뭐로 바뀌었나

| 파일 | 생성 도구 | 형태 |
|---|---|---|
| `_remarkprefix_classic.csv` | `remark_classic.py` (실행 시 자동) | `Column \| Value_Original \| Value_fx` — 그 실행에서 **실제 바뀐** 값 |
| `_remarkprefix_olap.csv` | `remark_olap.py` (실행 시 자동) | 〃 |
| `remark_olap.csv` / `remark_classic.csv` | `check_pivot_cache.py` (선택) | 캐시에 실제 있던 차원값 기준 (원본칼럼 \| 칼럼_fx 쌍) |
| `remark_prefix.csv` | `check_pivot_cache.py` (선택) | 토큰 레전드 (Token_Original \| Token_fx) |

- 세 경로 모두 **같은 SEED=<REMARK_SEED> cipher** → `ca_fr` 은 어디서 나오든 항상 같은 `_fx` 값. 서로 모순 없이 맞물린다.
- ⚠️ 레전드는 **역추적 키** — 외부 공유 파일과 같이 보내지 말 것 (내부 검증용).

---

## 치환 규칙

- **토큰 단위**: 알파벳 연속 덩어리만 치환, 숫자/언더바/구분자는 원형 유지
  - 예) `ca_fr` → `vp_ez` (`ca`→`vp`, `_` 유지, `fr`→`ez`)
- **대소문자 유지**: `France` → `Ezpdvc`, `FRANCE` → `EZPDVC`
- **일관성**: 같은 토큰은 파일 전체에서 항상 같은 결과
- **시드 고정**: `SEED = <REMARK_SEED>` — 동일 입력이면 언제나 동일 출력 (재현 가능)
