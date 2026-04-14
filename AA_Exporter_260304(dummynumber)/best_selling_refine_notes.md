# best selling product 정제 스크립트 노트

## 파일 목록

| 파일 | 역할 |
|---|---|
| `best_selling_refine_260413.py` | AA Exporter raw CSV → stacked_separate CSV 정제 |
| `foldering_move_png_251126_26campaign_name.py` | 모니터링 캡처 파일(PNG/MHTML)을 날짜·디바이스 기준 폴더로 이동 |

---

## best_selling_refine_260413.py

### 개요
AA Exporter에서 추출한 `best_selling_product` raw CSV를 읽어
노트북 컨벤션(`{tb_key}_stacked_separate.csv`)에 맞게 정제하는 스크립트.

### 처리 흐름

```
aa_exports/{tb_key}_{YYYYMMDD}_{HHMM}.csv  (타임스탬프 최신 파일 자동 선택)
  ↓ status=OK 필터
  ↓ DIVISION / CATEGORY 분류
  ↓ Brand_Site 행 (value1=ORDER, value2×환율=REVENUE)
  ↓ Campaign 행 (value3=ORDER, value4×환율=REVENUE)
  → aa_exports/{tb_key}_stacked_separate.csv
```

### TB_KEYS 설정

| tb_key | PERIOD | 환율 연도 |
|---|---|---|
| `best_selling_product` | 2026 Campaign Period | 2026 |
| `best_selling_product_prior` | 2026 Prior Period | 2026 |
| `last_best_selling_product` | 2025 Campaign Period | 2025 |

- 환율 컬럼은 `ref/currency.csv`에서 해당 연도로 시작하는 컬럼 자동 선택
- 파일명 날짜가 바뀌어도 TB_KEYS 수정 불필요

### ref/currency.csv 구조

`SITE CODE` 컬럼 + 연도별 환율 컬럼으로 구성.

| 컬럼 | 예시 | 설명 |
|---|---|---|
| `SITE CODE` | `us`, `de`, `kr` | 소문자 사이트 코드 |
| `2025_...` | `2025_KRW` 등 | 2025년 기준 환율 |
| `2026_...` | `2026_KRW` 등 | 2026년 기준 환율 |

스크립트는 TB_KEYS의 세 번째 값(연도 문자열)으로 시작하는 컬럼명을 자동 탐색.  
연도가 바뀌면 TB_KEYS의 환율 연도만 수정하면 됨 (컬럼명 직접 지정 불필요).

### 출력 컬럼 (A~K)

`PERIOD` / `STANDARD` / `TIER` / `SUBS` / `COUNTRY` / `SITE CODE` / `DIVISION` / `PRODUCT` / `CATEGORY` / `ORDER` / `REVENUE`

### 분류 체계

**DIVISION** (대분류, `cmp_n_scom` CTE 기준)

| 값 | 대상 |
|---|---|
| MX | 스마트폰·웨어러블·태블릿·PC |
| VD | TV·모니터·사운드바 |
| DA | 생활가전 |
| ETC | 그 외 |

**CATEGORY** (세분류, `plus_category` CTE 기준)

`SMP` / `Tablet` / `NPC` / `Wearable` / `ACC` / `TV` / `Monitor` / `Sound Bar` / `AC` / `Air Purifier` / `Washer` / `Dryer` / `Air Dresser` / `Shoe Dresser` / `REF` / `VC` / `Cooking` / `DW` / `AUDIO` / `BUNDLE` / `X`(제외) / `ETC`

스페인어 display name 예외 처리 포함 (FUNDA→ACC, SMART TV→TV, REFRIGERADOR→REF 등)

### 예외 상황

| 상황 | 동작 |
|---|---|
| `aa_exports/`에 해당 `tb_key` 파일 없음 | 해당 tb_key 스킵, 나머지 계속 처리 |
| `status≠OK` 행만 존재 | 빈 CSV 출력 (헤더만) |
| `ref/currency.csv`에 해당 연도 컬럼 없음 | `KeyError` 발생 → TB_KEYS 환율 연도 또는 currency.csv 컬럼명 확인 필요 |
| SITE CODE가 currency.csv에 없음 | REVENUE가 `NaN`으로 출력 → currency.csv에 해당 사이트 코드 추가 필요 |

---

## foldering_move_png_251126_26campaign_name.py

### 개요
캠페인 모니터링 캡처 폴더의 PNG·MHTML 파일을 파일명 앞부분(PC/MO 이전)을 폴더명으로 삼아 자동 분류 이동.

### 실행 전 주의
- **MO 파일 먼저 수동 이동 후 실행**
- 스크립트 상단 `folder_path` 변수를 실제 경로로 수정 필요

```python
# 예시
folder_path = r"C:\Users\user_name\OneDrive\campaign_name\monitoring"
```

### 동작 예시

```
입력: 20260407_homepage_PC_AE.png
출력: 20260407_homepage/20260407_homepage_PC_AE.png

입력: 20260407_homepage_MO_AE.mhtml
출력: 20260407_homepage/20260407_homepage_MO_AE.mhtml
```
