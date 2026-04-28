# RESHAPE_multipurchase_260428.py 가이드
<!-- 2026-04-28  Jonghyun Park w/ Claude -->

`multipurchase_260212 ... (offer예외추가).sql` 의 Python 포팅.
3개 기간(this year / prior / last year) **동시 처리**, raw CSV → 정제 CSV.

---

## 입력 / 출력

| 모드 | 입력 | 출력 |
|---|---|---|
| this year   | `aa_exports/multi_purchase_*.csv`        | `multi_purchase_stacked_separate.csv` |
| prior       | `aa_exports/multi_purchase_prior_*.csv`  | `multi_purchase_prior_stacked_separate.csv` |
| last year   | `aa_exports/last_multi_purchase_*.csv`   | `last_multi_purchase_stacked_separate.csv` |
| **통합**    | (위 3개 결과 concat)                     | `multi_purchase_stacked_separate_union.csv` |

> 3개 prefix 각각 **최신 타임스탬프 1개** 자동 선택 (`find_latest`). HHMM(4자리) / HHMMSS(6자리) 둘 다 지원.

---

## 입력 컬럼 매핑 (AA 표준 형식 기준)

| 원본 헤더 | this year 의미 | prior 의미 | last year 의미 (가정) |
|---|---|---|---|
| `value1` | campaign_total_multiorder_unit | campaign_prior_total_multiorder_unit | last_*_unit |
| `value2` | campaign_total_multiorder | campaign_prior_total_multiorder | last_*_order |
| `value3` | campaign_total_multiorder_revenue | campaign_prior_total_multiorder_revenue | last_*_revenue |
| `value4` | scom_total_multiorder_unit | scom_prior_total_multiorder_unit | last_scom_*_unit |
| `value5` | scom_total_multiorder | scom_prior_total_multiorder | last_scom_*_order |
| `value6` | scom_total_multiorder_revenue | scom_prior_total_multiorder_revenue | last_scom_*_revenue |
| `value` (breakdown) | 구매 모델 코드들 (쉼표 구분) | 동일 | 동일 |

> `value1~3` = Campaign 메트릭 / `value4~6` = S.com 메트릭 (3개 기간 모두 동일 구조).

---

## 실행 전 설정

```python
TB_KEYS = [
    # (prefix, PERIOD 라벨, 환율 연도, 출력 STANDARD 리스트)
    ("multi_purchase",        "Campaign Period",                        "2026", ["S.com", "Campaign"]),
    ("multi_purchase_prior",  "Prior Period (S.com Only)",              "2026", ["S.com"]),
    ("last_multi_purchase",   "Last Year Campaign Period",              "2025", ["S.com", "Campaign"]),
]
```

| 필드 | 변경 가이드 |
|---|---|
| prefix | 실제 AA export 파일명에 맞춰 수정 |
| PERIOD 라벨 | 그대로 출력에 사용. STANDARD 리스트와 일관성 유지 (S.com만이면 `(S.com Only)` 접미사 권장) |
| 환율 연도 | `currency.csv`의 해당 연도 컬럼 자동 선택 |
| 출력 STANDARD | this year/last year는 `["S.com", "Campaign"]`, prior는 `["S.com"]` 기본. **prior에서 Campaign도 필요할 때** `["S.com", "Campaign"]`로 변경하고 PERIOD 라벨에서 `(S.com Only)` 제거 |

---

## 처리 흐름 (SQL CTE 매핑)

```
aa_exports/{prefix}_YYYYMMDD_HHMM(SS).csv
    │
    ├─ status == "OK" 행만 유지
    ├─ value1~6 숫자 변환
    ├─ value(breakdown) 쉼표 분리 → 위치별 model_code 추출
    │     └─ 각 model_code 카테고리 분류 (get_category)
    ├─ pos 순서로 ',' 조인 → CATEGORIES ORIGIN
    ├─ ACC 제외 + 카테고리명 알파벳순 ', ' 조인 → CATEGORY
    ├─ SITE CODE 정규화 (ku→IQ_KU, uk_epp→UK, else upper)
    ├─ 환율 적용: REVENUE = value3(or 6) × rate
    │
    ├─ Campaign 행 생성 (value1=UNIT, value2=ORDER, value3=REVENUE 원본)
    └─ S.com    행 생성 (value4=UNIT, value5=ORDER, value6=REVENUE 원본)
          ↓
    concat
    ↓
    UNIT > 0 필터 + STANDARD 필터
    ↓
    {prefix}_stacked_separate.csv
    ↓
    3개 분리 결과 concat → multi_purchase_stacked_separate_union.csv
```

| SQL CTE | Python 단계 |
|---|---|
| `src` | `pd.read_csv` + status=OK 필터 |
| `split_seed` / `exploded_origin` / `exploded` | `aggregate_categories()`에서 단일 함수로 압축 (recursive 분리 → list 처리) |
| `unpivoted` | Campaign + S.com 2행 생성 |
| `plus_category` | `get_category()` (model_code별) |
| `matched` (rn=1) | 단일 model_code = 단일 카테고리이므로 `aggregate_categories` 내부에서 자연 처리 |
| `final_rows` / `before_last` (group_concat) | `aggregate_categories`에서 한 번에 산출 |
| 최종 SELECT | 환율 적용 + UNIT/STANDARD 필터 |

---

## 카테고리 분류 (`get_category`)

best_selling과 동일한 prefix 매핑이지만 **3가지 차이점**:

1. **예외 → `None`** (best_selling은 `"X"` 반환): SM-M1000QW, RS-CN%, LUMAFU%, ARCSITE%, UNSPECIFIED, UNDEFINED, AW-EW%, AC-TC%, NL-%, MLT%, VCA-%, DV-%, WA-TC%, DW-%, AF-%, DF-%, RF-TC%, APL-%, WF-%, WT-%, SC-WATCH%, SC1TAB%, WATCHES-IFIT%, BUDS
2. **`-OFFER` 포함 시 `None`** (multipurchase 전용 추가 예외)
3. **스페인어 displayname fallthrough 없음** (best_selling에만 있음)

분류 카테고리: SMP / Tablet / NPC / Wearable / ACC / TV / Monitor / Sound Bar / AC / Air Purifier / Washer / Dryer / Air Dresser / Shoe Dresser / REF / VC / Cooking / DW / AUDIO / BUNDLE / **None**(미매칭/예외)

---

## 출력 컬럼

```
PERIOD, TIER, SUBS, COUNTRY, SITE CODE, STANDARD, MODEL CODE,
UNIT, ORDER, REVENUE, CATEGORY, REVENUE ORIGIN, CATEGORIES ORIGIN,
START DATE, END DATE
```

| 컬럼 | 내용 |
|---|---|
| `PERIOD` | TB_KEYS 설정값 |
| `TIER`/`SUBS`/`COUNTRY` | 빈 문자열 (campaign_tier 조인 제외) |
| `SITE CODE` | 정규화된 site code |
| `STANDARD` | `S.com` 또는 `Campaign` (TB_KEYS 필터 결과) |
| `MODEL CODE` | 원본 breakdown (쉼표 구분 모델 코드 그대로) |
| `UNIT` | 멀티오더 unit (Campaign=value1, S.com=value4) |
| `ORDER` | 멀티오더 order (Campaign=value2, S.com=value5) |
| `REVENUE` | `value3 or value6 × 환율` (USD 환산) |
| `CATEGORY` | ACC 제외 + 카테고리명 **case-insensitive 알파벳순** `, ` 조인 (MySQL utf8_general_ci 호환) |
| `REVENUE ORIGIN` | 환율 적용 전 원본 revenue (현지 통화) |
| `CATEGORIES ORIGIN` | pos 순서대로 `,` 조인 (ACC 포함, null 제외) |
| `START DATE`/`END DATE` | 원본 그대로 |

---

## SITE CODE 정규화

| 원본 | 정규화 |
|---|---|
| `ku` | `IQ_KU` |
| `uk_epp` | `UK` |
| 그 외 | `upper()` |

---

## 환율 적용

- `currency.csv`에서 `currency_year` (TB_KEYS 3번째 값)로 시작하는 컬럼 자동 선택
- 매칭 안 되는 site_code는 환율 1.0 (USD 가정)
- SQL은 `c.\`2026-02-09\`` 단일 날짜 고정 사용 → PY는 연도만 매칭하므로 같은 연도 내 컬럼이 여러 개일 때 **첫 번째** 사용

---

## 필터

1. `UNIT > 0` — SQL의 `where lst.unit > 0`
2. `STANDARD ∈ TB_KEYS[3]` — SQL의 `where standard = 'S.com'` (PY는 리스트 설정으로 확장)

---

## 타임스탬프 패턴

```python
_TS_PAT = re.compile(r"_(\d{8})_(\d{4,6})$")
```

- `YYYYMMDD_HHMM` (4자리)와 `YYYYMMDD_HHMMSS` (6자리) **둘 다 지원**
- 정렬 시 HHMM은 6자리로 zero-pad (`1234` → `123400` = 12:34:00)

---

## 실행

```bash
python "RESHAPE_multipurchase_260428.py"
```

prefix별 파일이 없으면 스킵 후 다음 prefix 처리. 통합 union은 처리된 부분만 합쳐 저장.

---

## SQL과의 차이점·주의사항

1. **`row_number()` rn=1 필터** — SQL의 `partition by site_code, breakdown, standard, pos`는 사실상 partition별 1행이라 no-op. PY는 단일 model_code → 단일 category 매핑이라 자동 처리.
2. **MAX(unit/order/revenue)** — SQL이 group by 외 컬럼을 max로 가져가지만 같은 (site_code, breakdown, standard) 안에서 모두 동일값이라 의미 없음. PY는 raw 행 그대로 사용.
3. **STANDARD 필터** — SQL은 `S.com only` 하드코딩. PY는 TB_KEYS 4번째 인자로 리스트 변경 가능.
4. **PERIOD 라벨** — SQL에 'Prior Period (S.com Only)' 하드코딩되어 있는데 this year SQL인데 같은 라벨이라 SQL 자체 버그로 추정. PY는 의도대로 보정해 'Campaign Period (S.com Only)' / 'Prior Period (S.com Only)' / 'Last Year Campaign Period (S.com Only)' 사용.
5. **campaign_tier 조인 제외** — TIER/SUBS/COUNTRY 빈 칼럼.
6. **CATEGORY 정렬** — MySQL `ORDER BY`는 기본 case-insensitive (utf8_general_ci). PY는 `sorted(..., key=str.lower)` 사용해 동일 결과. 예: `"Tablet, TV"` (case-insensitive) vs `"TV, Tablet"` (case-sensitive ASCII). 미적용 시 약 0.1% 정도 정렬 순서 불일치 발생.

---

## 주의사항

| 항목 | 내용 |
|---|---|
| `status != "OK"` 행 | 자동 제외됨 |
| `UNIT == 0` 행 | 자동 제외됨 (SQL과 동일) |
| breakdown 쉼표 분리 | `trim(replace(model_code, ',', '')) <> ''` 동일하게 공백 모델 제외 |
| ACC 제외 로직 | `CATEGORY` 컬럼에는 ACC 제거됨, `CATEGORIES ORIGIN`에는 포함 |
| 환율 컬럼 자동 선택 | `currency_year`로 시작하는 컬럼 사용 |
| last year 파일 | 현재 미존재 시 자동 스킵 (에러 아님) |
