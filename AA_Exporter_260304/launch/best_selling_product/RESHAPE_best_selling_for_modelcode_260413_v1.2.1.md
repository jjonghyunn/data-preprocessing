# RESHAPE_best_selling_for_modelcode_260413_v1.2.1.py 가이드
<!-- 2026-04-30  Jonghyun Park w/ Claude -->

`best_selling_modelcode` raw CSV → 정제 CSV (`_stacked_separate`) 생성 스크립트.

베이스: `RESHAPE_best_selling_260413_v1.2.1.py` (v1.2.1)  
카테고리 집계 패턴: `RESHAPE_multipurchase_260428_v1.1.py` 의 `aggregate_categories`

> **언제 사용?** raw `value` 컬럼이 단일 모델이 아니라 **다중 모델 코드 쉼표 구분** 형태 (예: `SM-S910,SM-A155,QN65...`)일 때.

---

## v1.2.1 best_selling 대비 차이

### 1) value(PRODUCT) 다중 모델 처리

raw `value` 컬럼을 **쉼표 분리**해서 모델별 DIVISION/CATEGORY를 추출한 뒤 집계.

```
"SM-S910,SM-A155,QN65,SM-S210"
    ↓ split ","
["SM-S910", "SM-A155", "QN65", "SM-S210"]
    ↓ get_division 각각
["MX", "MX", "VD", "MX"]
    ↓ 순서보존 dedup
"MX, VD"
```

### 2) DIVISION — 두 컬럼 분리 + 고정 순서

- **이전 (best_selling v1.2.1)**: 단일 모델 → 단일 division ("MX" / "VD" / "DA" / "ETC")
- **변경 (modelcode v1.2.1)**: 다중 모델 → 두 컬럼:
  - **DIVISION**: ETC 제외, 고정 순서 `MX→VD→DA`, dedup
  - **DIVISION ORIGIN** (신규): ETC 포함, 고정 순서 `MX→VD→DA→ETC`, dedup

> **출력 순서는 등장 순서가 아니라 항상 `MX, VD, DA(, ETC)` 고정**. 즉 `DA, MX`는 잘못된 출력 — 항상 `MX, DA`로 정렬됨.

| 입력 (모델별 division 집합) | DIVISION ORIGIN | DIVISION |
|---|---|---|
| `{MX}` | `MX` | `MX` |
| `{MX, VD, DA}` | `MX, VD, DA` | `MX, VD, DA` |
| `{DA, MX}` | `MX, DA` | `MX, DA` |
| `{MX, ETC}` | `MX, ETC` | `MX` |
| `{ETC}` | `ETC` | (빈) |

```python
DIVISION_ORDER = ["MX", "VD", "DA", "ETC"]

def aggregate_divisions(value) -> tuple[str, str]:
    if pd.isna(value):
        return ("", "")
    parts = [p.strip() for p in str(value).split(",")]
    parts = [p for p in parts if p]
    divs = set(get_division(p) for p in parts)
    origin = ", ".join(d for d in DIVISION_ORDER if d in divs)
    no_etc = ", ".join(d for d in DIVISION_ORDER if d in divs and d != "ETC")
    return (origin, no_etc)
```

### 3) CATEGORY 집계 (multipurchase 패턴)

- **CATEGORIES ORIGIN** (신규): pos 순서, 중복 유지, ACC 포함 — 단 `None`/빈/`X`/`ETC` 는 제외
- **CATEGORY**: ACC 제외 + 알파벳 정렬(case-insensitive) + 중복 제거

| 모델 (pos 순) | get_category 결과 | CATEGORIES ORIGIN | CATEGORY |
|---|---|---|---|
| SM-S910, ET-A123, SM-A155 | SMP, ACC, SMP | `SMP, ACC, SMP` | `SMP` |
| QN65, SM-S910, MA-XYZ | TV, SMP, ACC | `TV, SMP, ACC` | `SMP, TV` |
| RS-CN-X, SM-S910 | X, SMP | `SMP` | `SMP` |
| (NaN) | — | (빈) | (빈) |

### 4) DIVISION ORIGIN + CATEGORIES ORIGIN — 우측 끝

기존 best_selling v1.2.1 컬럼 순서를 유지하고 우측 끝에 두 ORIGIN 컬럼 추가:
- `DIVISION ORIGIN` (왼쪽)
- `CATEGORIES ORIGIN` (가장 끝)

---

## 처리 대상 tb_key

non-US 3종 + US 3종. 파일 없는 tb_key는 자동 skip.

| tb_key | PERIOD | 환율 연도 |
|---|---|---|
| `best_selling_modelcode` | 2026 Campaign Period | 2026 |
| `best_selling_modelcode_prior` | 2026 Prior Period | 2026 |
| `last_raw_best_selling_modelcode` | 2025 Campaign Period | 2025 |
| `us_best_selling_modelcode` | 2026 Campaign Period | 2026 |
| `us_best_selling_modelcode_prior` | 2026 Prior Period | 2026 |
| `us_last_raw_best_selling_modelcode` | 2025 Campaign Period | 2025 |

환율 연도는 `currency.csv`에서 해당 연도로 시작하는 컬럼을 자동 선택.  
동일 연도 컬럼이 여러 개면 첫 번째 사용.

---

## 처리 흐름

```
aa_exports/{tb_key}_*.csv
    │
    ├─ 타임스탬프 기준 최신 파일 1개 선택 (_TS_PAT: _YYYYMMDD_HHMM(SS))
    ├─ status 필터: 'fail'/'error' 단어 포함 행 제외 (v1.2.1)
    ├─ value1~4 숫자 변환 (coerce → fillna 0)
    │
    ├─ DIVISION = aggregate_divisions(value)        ← 다중 모델 dedup
    ├─ CATEGORIES_ORIGIN, CATEGORY = aggregate_categories(value)  ← multipurchase 패턴
    │   └─ value 공란/NaN → "" 반환
    ├─ SITE CODE 정규화
    ├─ 환율 적용 (REVENUE = value2 or value4 × rate)
    │
    ├─ S.com 행 생성   (STANDARD="S.com",    ORDER=value1, REVENUE=value2×rate)
    └─ Campaign 행 생성 (STANDARD="Campaign", ORDER=value3, REVENUE=value4×rate)
          ↓
    concat
    ↓
    ORDER == 0 행 제거 (v1.1)
    ↓
    PRICE RANGE 부여 (단가 = REVENUE/ORDER 기준 5구간)
    ↓
    {tb_key}_stacked_separate.csv
```

---

## 출력 컬럼 구조

```
PERIOD, STANDARD, TIER, SUBS, COUNTRY,
SITE CODE, DIVISION, PRODUCT, CATEGORY,
PRICE RANGE, ORDER, REVENUE,
DIVISION ORIGIN, CATEGORIES ORIGIN
```

| 컬럼 | 내용 |
|---|---|
| `PERIOD` | TB_KEYS 설정값 (예: `2026 Campaign Period`) |
| `STANDARD` | `S.com` 또는 `Campaign` |
| `TIER` | 공란 |
| `SUBS` | `Subsidiary` 원본값 |
| `COUNTRY` | `Country` 원본값 |
| `SITE CODE` | 정규화된 site code |
| **`DIVISION`** | **ETC 제외, 고정 순서 MX→VD→DA, dedup (예: `MX, VD, DA`)** |
| `PRODUCT` | `value` 원본 (다중 모델 코드, 쉼표 구분 그대로) |
| **`CATEGORY`** | **ACC 제외, 알파벳 정렬, dedup (예: `SMP, TV`)** |
| `PRICE RANGE` | Under $300 / Under $500 / Under $800 / Under $1000 / Over $1000 — 단가 = REVENUE/ORDER |
| `ORDER` | S.com=`value1`, Campaign=`value3` (0 행은 제거됨) |
| `REVENUE` | S.com=`value2×rate`, Campaign=`value4×rate` (소수점 6자리) |
| **`DIVISION ORIGIN`** | **(신규) ETC 포함, 고정 순서 MX→VD→DA→ETC, dedup** |
| **`CATEGORIES ORIGIN`** | **(신규, 가장 우측) pos 순서, 중복 유지, ACC 포함, X/ETC/None 제외** |

---

## 핵심 함수

### `aggregate_divisions(value) -> tuple[str, str]`

```python
DIVISION_ORDER = ["MX", "VD", "DA", "ETC"]

def aggregate_divisions(value) -> tuple[str, str]:
    if pd.isna(value):
        return ("", "")
    parts = [p.strip() for p in str(value).split(",")]
    parts = [p for p in parts if p]
    divs = set(get_division(p) for p in parts)
    origin = ", ".join(d for d in DIVISION_ORDER if d in divs)
    no_etc = ", ".join(d for d in DIVISION_ORDER if d in divs and d != "ETC")
    return (origin, no_etc)
```

- 반환: `(DIVISION ORIGIN, DIVISION)`
- 출력 순서는 **항상 `MX, VD, DA(, ETC)` 고정** — 입력 등장 순서 무관
- DIVISION은 ETC 제외, DIVISION ORIGIN은 ETC 포함

### `aggregate_categories(value) -> tuple[str, str]`

```python
def aggregate_categories(value) -> tuple[str, str]:
    if pd.isna(value):
        return ("", "")
    parts = [p.strip() for p in str(value).split(",")]
    parts = [p for p in parts if p]
    cats_in_pos = [get_category(p) for p in parts]
    EXCLUDE = {None, "", "X", "ETC"}
    valid = [c for c in cats_in_pos if c not in EXCLUDE]
    non_acc_unique = sorted(set(c for c in valid if c != "ACC"), key=str.lower)
    return (", ".join(valid), ", ".join(non_acc_unique))
```

- `EXCLUDE = {None, "", "X", "ETC"}` — 의미 없는 카테고리 제외
- CATEGORIES ORIGIN: pos 순서, 중복 유지, ACC 포함
- CATEGORY: ACC 제외 + sorted(set(...), key=str.lower) + ", " 조인

> X / ETC 도 보존하길 원하면 `EXCLUDE` 에서 제거.

---

## DIVISION / CATEGORY 분류 기준

best_selling v1.2.1 의 `get_division` / `get_category` 함수와 **완전히 동일**.  
상세 prefix 매핑은 `RESHAPE_best_selling_260413_v1.2.1.md` 참고.

---

## SITE CODE 정규화

| 원본 | 정규화 |
|---|---|
| `ku` | `IQ_KU` |
| `uk_epp` | `UK` |
| 그 외 | `upper()` |

---

## PRICE RANGE 분류

단가 = **`REVENUE / ORDER`** (USD 환산 후 단위당 가격)

| 단가 범위 | PRICE RANGE | 비고 |
|---|---|---|
| `< $300` | `Under $300` | 음수 포함 (반품 등) |
| `$300 ~ < $500` | `Under $500` | |
| `$500 ~ < $800` | `Under $800` | |
| `$800 ~ < $1000` | `Under $1000` | |
| `≥ $1000` | `Over $1000` | |

**경계 처리**: `<` 비교 (해당 임계값 자체는 다음 구간에 포함)

---

## 참조 파일

| 파일 | 위치 | 용도 |
|---|---|---|
| `currency.csv` | `ref/` | site별 연도별 환율 |
| `best_selling_modelcode_*.csv` | `aa_exports/` | AA export raw (TY) |
| `best_selling_modelcode_prior_*.csv` | `aa_exports/` | AA export raw (TY prior) |
| `last_raw_best_selling_modelcode_*.csv` | `aa_exports/` | AA export raw (LY) |
| `us_best_selling_modelcode_*.csv` | `aa_exports/` | AA export raw (TY US) |
| `us_best_selling_modelcode_prior_*.csv` | `aa_exports/` | AA export raw (TY US prior) |
| `us_last_raw_best_selling_modelcode_*.csv` | `aa_exports/` | AA export raw (LY US) |

---

## 실행 방법

```bash
python "RESHAPE_best_selling_for_modelcode_260413_v1.2.1.py"
```

tb_key별로 파일이 없으면 스킵 후 다음 tb_key 계속 처리.

---

## 주의사항

| 항목 | 내용 |
|---|---|
| `status` 필터 | 'fail' / 'error' 단어 포함 행만 제외 (v1.2.1 완화 로직 그대로) |
| `ORDER == 0` 행 | 자동 제외 (v1.1 룰 유지) |
| NaN/공란 PRODUCT | DIVISION = `""`, CATEGORY = `""`, CATEGORIES ORIGIN = `""` (단일 모델 best_selling은 `ETC` 였음 — 다중 모델 집계 함수에선 빈 문자열 반환) |
| **DIVISION 출력 순서** | **고정 `MX→VD→DA→ETC`** — 입력 순서 무관, 항상 정렬됨. 예) 입력이 `DA,MX` 이어도 출력은 `MX, DA` |
| **CATEGORY 정렬** | **알파벳 정렬 case-insensitive (utf8_general_ci 호환)**, ACC 제외 |
| **CATEGORIES ORIGIN 제외값** | None / 빈 문자열 / `X` / `ETC` (`EXCLUDE` set에서 조정 가능) |
| 환율 컬럼 자동 선택 | `currency_year`로 시작하는 컬럼 사용 — currency.csv 연도 컬럼 확인 필요 |
| 타임스탬프 패턴 | `_YYYYMMDD_HHMM(SS)` — HHMM 4자리, HHMMSS 6자리 모두 지원 |
| REVENUE float | `.round(6)` 처리 후 `%.6f` 포맷 저장 |
| TIER 컬럼 | 현재 공란으로 고정 |

---

## 변경 이력

- **2026-04-30** (Jonghyun Park) — 초기 작성. best_selling v1.2.1 베이스 + multipurchase의 다중 모델 카테고리 집계 패턴 결합. DIVISION 순서보존 dedup, CATEGORIES ORIGIN 우측 끝 컬럼 신설.
- **2026-04-30** (Jonghyun Park) — TB_KEYS에 US 3종 추가 (`us_best_selling_modelcode`, `us_best_selling_modelcode_prior`, `us_last_raw_best_selling_modelcode`).
- **2026-04-30** (Jonghyun Park) — DIVISION을 두 컬럼으로 분리 (`DIVISION` = ETC 제외, `DIVISION ORIGIN` = ETC 포함), 고정 순서 `MX→VD→DA(→ETC)` 적용. 컬럼 우측 끝 순서: `..., DIVISION ORIGIN, CATEGORIES ORIGIN`.
