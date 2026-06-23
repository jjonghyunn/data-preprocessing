# 260622_remark_pivot  
<sub>2026-06-23  Jonghyun Park w/ Claude</sub>

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
| `remark_classic.py` | **Classic 피봇** xlsx 리마킹 — raw 시트 셀 치환 + 불필요 시트 삭제 |
| `remark_olap.py` | **OLAP 피봇** 소스 리마킹 — data/ CSV → data_fx/ 출력 |
| `remark_prefix_v2.py` | 컬럼쌍 구조 레전드 xlsx 생성 (샘플 포맷) |
| `remark_pivot.py` | 피봇 캐시 차원값 추출 (분석용 보조 도구) |

---

## 실행 순서

```
# 1a. Classic 피봇 xlsx 리마킹
python remark_classic.py   →  _remark_원본파일명.xlsx

# 1b. OLAP 피봇 소스 CSV 리마킹 (data 폴더가 있을 때)
python remark_olap.py      →  data_fx/ 폴더

# 2. 레전드 뷰 생성
python remark_prefix_v2.py      →  remark_prefix_v2.xlsx
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
# 1. 파일 경로
CLASSIC_XLSX = r"...새 파일.xlsx"

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
- 민감 식별자(`sitecode` / `region` / `subs` / `country` / `division` / `channel` 계열)만 치환
- `SegmentName` / `SegmentId` / `category` / `variables/product` / `prop6` / `evar41` / `div_1~3` 등은 기본 주석처리(미치환) — 필요 시 주석 해제

### 새 파일 적용 시 수정 항목

```python
INPUT_DIR  = r"...새 data 폴더"
OUTPUT_DIR = r"...출력 경로"

# dim: 민감 컬럼만 (region/subs/country 는 dim 에서 치환)
DIM_REMARK  = { "d_country.csv": ["sitecode", "region", "subs", "country"], ... }
# fact: sitecode/division/channel 만 활성, 나머지는 주석처리
FACT_REMARK = { "basic_traffic": ["sitecode"], "internal": ["sitecode", "channel"], ... }
```

---

## remark_prefix_v2.py

### 출력 형식
샘플(`remark_sample_fx.xlsx`)과 동일한 컬럼쌍 레이아웃:

| Sheet | 컬럼 |
|---|---|
| **Site** | Region \| Region_fx \| Subs \| Subs_fx \| Country \| Country_fx \| Site Code \| Site Code_fx |
| **Channel** | channel_source \| channel_source_fx \| channel_unified \| channel_unified_fx \| paid_type |

---

## 치환 규칙

- **토큰 단위**: 알파벳 연속 덩어리만 치환, 숫자/언더바/구분자는 원형 유지
  - 예) `ca_fr` → `fr_tc` (`ca`→`fr`, `_` 유지, `fr`→`tc`)
- **대소문자 유지**: `France` → `Bqozxi`, `FRANCE` → `BQOZXI`
- **일관성**: 같은 토큰은 파일 전체에서 항상 같은 결과
- **시드 고정**: `SEED = <REMARK_SEED>` — 동일 입력이면 언제나 동일 출력 (재현 가능)
