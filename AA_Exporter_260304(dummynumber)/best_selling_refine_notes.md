# best selling product 정제 스크립트 노트

## 파일 목록

| 파일 | 역할 |
|---|---|
| `best_selling_refine_260413.py` | AA Exporter raw CSV → stacked_separate CSV 정제 |

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
