# RESHAPE_nextpage_260428.py 가이드  
<sub>2026-04-28  Jonghyun Park w/ Claude</sub>  

`nextpage_260129_da_separate.sql` 의 Python 포팅 버전.
nextpage 데이터 → SQL의 마지막 SELECT 결과 CSV 생성.

**두 가지 입력 모드 자동 감지**:
- (A) **단일 파일 모드** — `COMBINED_PREFIX` 파일이 있으면 사용 (value1~4)
- (B) **분리 파일 모드** — `A_PREFIX` + `B_PREFIX` 두 파일 (각 value1~2)

---

## 입력 / 출력

| 모드 | 입력 | 비고 |
|---|---|---|
| **COMBINED** (우선) | `aa_exports/{COMBINED_PREFIX}_*.csv` | 단일 파일에 value1~4 포함 |
| **SEPARATE** (fallback) | `aa_exports/{A_PREFIX}_*.csv` + `aa_exports/{B_PREFIX}_*.csv` | 각 value1~2 |
| 출력 | `aa_exports/nextpage_vdda_separate.csv` | UTF-8-SIG |

> 우선순위: COMBINED 파일이 발견되면 그것만 사용. 없으면 A+B 모두 필요.

### 모드별 컬럼 의미 매핑

**COMBINED 모드 (단일 파일)**

| 실제 CSV 헤더 | 의미 |
|---|---|
| `value1` | TOTAL |
| `value2` | DIV1 |
| `value3` | DIV2 |
| `value4` | DIV3 |

**SEPARATE 모드 (A + B)**

| 파일 | 실제 CSV 헤더 | 의미 |
|---|---|---|
| A | `value1` | TOTAL |
| A | `value2` | DIV1 |
| B | `value1` | DIV2 |
| B | `value2` | DIV3 |

> SEPARATE 모드의 B는 헤더가 `value1, value2`로 A와 동일하지만 AA 추출 단위가 달라 의미만 다름. (site_code, breakdown) 기준 LEFT JOIN.

---

## 실행 전 설정

코드 상단:

```python
COMBINED_PREFIX = "nextpage"            # value1=TOTAL, value2=DIV1, value3=DIV2, value4=DIV3
A_PREFIX        = "nextpage_total_div1"   # value1=TOTAL, value2=DIV1
B_PREFIX        = "nextpage_div2_div3"      # value1=DIV2,    value2=DIV3
TOP_N           = 10                    # site_code별 상위 N개
```

실제 AA 추출 파일명이 정해지면 위 prefix만 교체.

> `find_latest()`는 정규식 fullmatch로 prefix 직후가 정확히 `_YYYYMMDD_HHMM(SS)` 인 파일만 매칭 → `nextpage_*` 가 `nextpage_total_div1_*`까지 잡지 않음. HHMM(4자리) / HHMMSS(6자리) 둘 다 지원 (정렬 시 4자리는 6자리로 zero-pad).

---

## 처리 흐름 (SQL CTE 매핑)

| SQL CTE | Python 단계 | 내용 |
|---|---|---|
| `origin` | `load_origin()` | 모드별 입력 → 동일 스키마 `[site_code, breakdown, total, div1, div2, div3]` |
| `mapped` (1) | `map_breakdown()` | URL/페이지명 → 카테고리명 정규화 |
| `mapped` (2) | `get_pagetype2()` | PCD / PD / PF / SD 태깅 |
| `unpivoted` | TOTAL/DIV1/DIV2/DIV3 4개 division 행으로 변환 | `pd.concat` |
| `with_div2` | `division_pagetype2 = "{division} {pagetype2}"` (예: "DIV1 PD") + `breakdown != '*'` | distinct |
| `totals_ranked` | TOTAL division만, `groupby(site_code).rank()` | row_number 등가 |
| `part1` | top N (`rn <= TOP_N`) → site_code 정규화 | UK/IQ_KU 변환 포함 |
| `part2` | top N에 속한 page_type만, division_pagetype2별 sum | EXISTS → merge |
| `tr` | part1 + part2 (part2는 'TOTAL%' 제외) | concat |
| 최종 SELECT | distinct + `VALUE > 0` | CATEGORY/VALUE_TYPE 부여 |

> COMBINED 모드와 SEPARATE 모드는 `load_origin()` 단계에서만 분기되며, 이후 로직은 동일.

---

## SITE CODE 정규화 (SQL part1/part2 case 절)

| 입력 | 출력 |
|---|---|
| `uk_epp` | `UK` |
| `ku` | `IQ_KU` |
| 그 외 | `UPPER(site_code)` |

---

## breakdown 매핑 규칙 (SQL: mapped CTE 1번 case)

### US (`site_code = 'us'`)

| 조건 (lower(breakdown)) | 매핑 |
|---|---|
| `www.company_name.com/us` 또는 `www.company_name.com/us/` (https:// 제거 후) | `home` |
| `'%/buy/%'` 포함 | `product detail` |
| `'%/us/tvs/%'` 포함 | `product category detail` |
| `'%/all-%'` 포함 | `product finder` |
| `'%/offer/%'` 포함 | `offer main` |
| `'%/shop/featured-offers/%'` 포함 | `offer main` |
| `'%/web/account/%'` 포함 | `my account` |

### HQ (`site_code = 'hq'`)

| 조건 | 매핑 |
|---|---|
| `revamp product finder` 또는 `revamp product detail` | `product finder` / `product detail` |
| `buying configurator` | `product detail` |

### 그 외: 원본 breakdown 그대로

---

## pagetype2 부여 규칙 (SQL: mapped CTE 2번 case)

| 매핑된 breakdown | pagetype2 |
|---|---|
| `product category detail` | `PCD` |
| `product detail`, `revamp product detail` | `PD` |
| `product finder`, `revamp product finder` | `PF` |
| `shop detail` | `SD` |
| `buying configurator` (hq) | `PD` |
| 그 외 | `null` |

---

## 출력 컬럼

```
TIER, SUBS, COUNTRY, SITE CODE, CATEGORY, PAGE TYPE, Origin_page_type, VALUE, VALUE_TYPE
```

| 컬럼 | 비고 |
|---|---|
| TIER, SUBS, COUNTRY | **빈 문자열** (SQL 원본은 `campaign_tier_260128` 조인이지만 PY에선 제외) |
| SITE CODE | 정규화된 site_code (대문자 + UK/IQ_KU 변환) |
| PAGE TYPE | part1=mapped breakdown / part2=`{division} {pagetype2}` |
| Origin_page_type | 원본 breakdown |
| VALUE | TOTAL은 row 값, DIV1/DIV2/DA는 pagetype2별 합산 |
| CATEGORY | suffix 기반 (`%PD`/`%PF`/`%PCD`/`%SD` → 카테고리명, hq `buying configurator` → `product detail`) |
| VALUE_TYPE | `both` (페이지타입 7종) / `division` (`DIV1*`/`DIV2*`/`DIV3*` prefix) / `non-division` |

---

## SQL과의 차이점·주의사항

원본 SQL과 **동작 의도는 동일**하지만 다음 항목은 SQL 엔진/구현에 따라 다른 결과가 나올 수 있음:

1. **pagetype2 산출 시 사용되는 breakdown**
   - SQL의 `case when lower(breakdown) in ('product detail',...)` 에서 `breakdown`은 SQL 엔진에 따라 ① 같은 SELECT의 alias(매핑된 값) 또는 ② 원본 컬럼 중 하나를 참조함
   - 본 PY는 **매핑된 breakdown**을 기준으로 pagetype2를 부여 (의미상 더 자연스러움)
   - 영향: US URL 패턴(`/buy/`, `/us/tvs/` 등) 행에서 PY는 PCD/PD를 부여, MySQL이 원본 컬럼을 참조하는 경우 SQL은 `null`이 될 수 있음 → part2의 division 합산 행 수가 달라질 수 있음

2. **row_number tie-breaking**
   - SQL `row_number() over (partition by site_code order by value desc)` → 동률일 때 순서는 엔진 임의
   - PY `rank(method="first", ascending=False)` → 데이터 순서 기준
   - top N 경계에서 동률이 있는 경우 선택 결과가 달라질 수 있음

3. **part2 group by 외 컬럼 (`origin_breakdown`)**
   - SQL은 group by에 없는 `origin_breakdown`을 그대로 select → 엔진별 임의값
   - PY는 `groupby(...).first()` 사용

4. **campaign_tier 조인 제외**
   - SQL: `left join campaign_tier_260128` 으로 TIER/SUBS/COUNTRY 채움
   - PY: 빈 문자열로 출력

5. **모드별 입력 차이 (PY 전용)**
   - COMBINED 모드: 단일 파일 → JOIN 단계 없음 (모든 행에 total/div1/div2/div3 같이 존재)
   - SEPARATE 모드: A LEFT JOIN B → A에 있고 B에 없는 (site_code, breakdown)은 div2/div3=0 으로 채워짐
   - 두 모드 결과가 다를 수 있는 경우: SEPARATE의 A,B 추출 시 site/breakdown 셋이 다른 경우

---

## 실행

```bash
python RESHAPE_nextpage_260428.py
```

`aa_exports/` 에 COMBINED 또는 (A + B) 파일이 있어야 함. 둘 다 없으면 `FileNotFoundError`.
