# RESHAPE_best_selling_260413_v1.1.py 가이드  
<sub>2026-04-28  Jonghyun Park w/ Claude</sub>  

`best_selling_product` raw CSV → 정제 CSV (`_stacked_separate`) 생성 스크립트.  
SQL 기준: `best selling product_260212(카테고리displayname스페인어보완).sql`

---

## v1 → v1.1 변경사항 (2026-04-28, Jonghyun Park)

### [FIX-1] PRODUCT 공란/NaN 시 CATEGORY/DIVISION = ETC 강제

- **문제**: `value` (PRODUCT 모델번호) 컬럼이 공란/NaN일 때 `str(NaN)` → `"nan"` → `.upper()` → `"NAN"` 으로 변환되며, `"NA"` prefix와 일치 → Cooking 카테고리로 오분류
- **수정**: `get_division`, `get_category` 진입부에 가드 추가
  ```python
  if pd.isna(v):
      return "ETC"
  u = str(v).upper().strip()
  if not u or u == "NAN":
      return "ETC"
  ```
- **효과**: 공란/NaN PRODUCT 행은 모두 `DIVISION="ETC"`, `CATEGORY="ETC"` 로 정확하게 분류

### [FIX-2] ORDER == 0 행 결과에서 제거

- **문제**: shop/camp 분리 후 한쪽 ORDER가 0인 행이 그대로 출력 → 후속 분석에서 무의미한 0행이 다수
- **수정**: `pd.concat([shop, camp])` 후 `result[result["ORDER"] != 0]` 필터 적용
- **효과**: shop/camp 각각 독립적으로 ORDER=0 행 제거. 한쪽만 0이면 그쪽만 제거됨
- **로그**: `ORDER=0 제거: {n}행 → {m}행`

> **참고**: v2(`RESHAPE_best_selling_260427_v2.py`)는 [FIX-1]은 동일하게 적용했지만 [FIX-2]는 미적용. v1.1은 v1 구조(2분할 출력) 유지하면서 두 보정만 추가.

---

## 처리 대상 tb_key

| tb_key | PERIOD | 환율 연도 |
|---|---|---|
| `best_selling_product` | 2026 Campaign Period | 2026 |
| `best_selling_product_prior` | 2026 Prior Period | 2026 |
| `last_best_selling_product` | 2025 Campaign Period | 2025 |

환율 연도는 `currency.csv`에서 해당 연도로 시작하는 컬럼을 자동 선택.  
동일 연도 컬럼이 여러 개면 첫 번째 사용.

---

## 처리 흐름

```
aa_exports/{tb_key}_*.csv
    │
    ├─ 타임스탬프 기준 최신 파일 1개 선택 (_TS_PAT: _YYYYMMDD_HHMM(SS))
    ├─ status == "OK" 행만 유지
    ├─ value1~4 숫자 변환 (coerce → fillna 0)
    ├─ DIVISION / CATEGORY 분류 (value 컬럼 = 제품 모델번호 기준)
    │   └─ [v1.1 FIX-1] NaN/공란/"NAN" → ETC 강제
    ├─ SITE CODE 정규화
    ├─ 환율 적용 (REVENUE = value2 or value4 × rate)
    │
    ├─ Shop 행 생성   (STANDARD="Shop",    ORDER=value1, REVENUE=value2×rate)
    └─ Campaign 행 생성 (STANDARD="Campaign", ORDER=value3, REVENUE=value4×rate)
          ↓
    concat
    ↓
    [v1.1 FIX-2] ORDER == 0 행 제거
    ↓
    {tb_key}_stacked_separate.csv
```

---

## 출력 컬럼 구조

```
PERIOD, STANDARD, TIER, SUBS, COUNTRY, SITE CODE, DIVISION, PRODUCT, CATEGORY, ORDER, REVENUE
```

| 컬럼 | 내용 |
|---|---|
| `PERIOD` | TB_KEYS 설정값 (예: `2026 Campaign Period`) |
| `STANDARD` | `Shop` 또는 `Campaign` |
| `TIER` | 공란 |
| `SUBS` | `Subsidiary` 원본값 |
| `COUNTRY` | `Country` 원본값 |
| `SITE CODE` | 정규화된 site code |
| `DIVISION` | DIV1 / DIV2 / DIV3 / **ETC (NaN 포함)** |
| `PRODUCT` | `value` 원본 (제품 모델명) |
| `CATEGORY` | SMP / TV / REF / AC / Washer / Tablet / NPC / Wearable / Monitor / Sound Bar / Cooking / VC / ACC / Air Purifier / Dryer / Air Dresser / Shoe Dresser / DW / AUDIO / BUNDLE / X / **ETC (NaN 포함)** |
| `ORDER` | Shop=`value1`, Campaign=`value3` (**0 행은 제거됨**) |
| `REVENUE` | Shop=`value2×rate`, Campaign=`value4×rate` (소수점 6자리) |

---

## SITE CODE 정규화

| 원본 | 정규화 |
|---|---|
| `ku` | `IQ_KU` |
| `uk_epp` | `UK` |
| 그 외 | `upper()` |

---

## DIVISION 분류 기준

`value` (제품 모델번호) prefix 기반.

| DIVISION | 주요 prefix |
|---|---|
| DIV1 | SM-S/G/A/F/M/E/W/X/P/T/R/Q/L, NT, NP, SM-R/Q/L, F-9/A/F7/M/S7/S9/X/NP, SMARTWATCH, XE5/XE3 |
| DIV2 | GQ/KQ/QA/QE/QN/TQ/UN/UA/UE/KU, LS/LF/LT/LU/LV/LC, HW-Q/S/A/B/C/LS/T, F-55/65/80/58/70/75/85/LS/Q/UN/3X, S2/S3/C2/C3 등 |
| DIV3 | AF/AC/AR/AJ/AM/AW/AX/AY, WW/WA/WV/WD/WF/WR/WH/WT, DV/DF/DJ, RB/RF/RL/RQ/RR/RS/RT/RW/RZ/RH/RP, VR/VS/VC, ME/MJ/ML/MM/MQ/MW, NA~NZ, MC/MG/MS/DW 등 |
| **ETC** | **NaN/공란/"NAN" (v1.1 신규)**, LUMAFUSION, ARCSITE, UNSPECIFIED, 기타 미매칭 |

---

## CATEGORY 분류 기준

`value` prefix 기반 (DIVISION보다 세분화). 스페인어 displayname 대응 fallthrough 로직 포함.

| CATEGORY | 주요 조건 |
|---|---|
| SMP | SM-S/G/A/F/M/E/W/N 등 (스마트폰) |
| Tablet | SM-X/P/T |
| NPC | NT, NP, XE |
| Wearable | SM-R/Q/L, L325N/L705N/L330N/L500N, SMARTWATCH |
| ACC | ET/EF/GP/EI/EE/EB/EJ/EP/EO, WMN/CFX/MA/RA/VCA/SKK 등 |
| TV | GQ/KQ/QA/QE/QN/TQ/UN/UA/UE/KU, TU3~9, GU 등 |
| Monitor | LS/LF/LT/LU/LV/LC, S2/S3/S40/S43/S49/S5, U32 등 |
| Sound Bar | HW-Q/S/A/B/C/LS/T |
| AC | AF/AC/AR/AJ/AM/AW/AN, PC1, KFR- |
| Air Purifier | AX/AY/AP |
| Washer | WW/WA/WV/WD/WF/WR/WH/WT |
| Dryer | DV |
| Air Dresser | DF |
| Shoe Dresser | DJ |
| REF | RF/RB/RL/RQ/RR/RS/RT/RW/RZ/RH/RP/RM/BR/RK70/RK80 |
| VC | VR/VS/VC/SC |
| Cooking | ME/MJ/ML/MM/MQ/MW, NA~NZ, MC/MG/MS/NS/CC/CTR 등 |
| DW | DW |
| AUDIO | JBL, HK |
| BUNDLE | F-9/55/65/80/AR/A/F7/M/S7/S9/X/NP/58/70/75/85/LS/Q/UN/3X 등, PACKGE |
| X | SM-M1000QW, RS-CN, LUMAFUSION, ARCSITE, UNSPECIFIED, UNDEFINED 등 예외 |
| **ETC** | **NaN/공란/"NAN" (v1.1 신규)**, 미매칭 |

**스페인어 displayname fallthrough** (prefix 미매칭 시):  
`MONITOR`, `CAMPAIGN NAME` (→TV), `FUNDA`/`SOPORTE` (→ACC), `BUDS` (→Wearable), `AIRE ACONDICIONADO` (→AC), `SMART TV` (→TV), `REFRIGERADOR` (→REF), `AURA STUDIO`/`JBL LIVE 770NC`/`TUNE BEAM`/`JBL TOUR ONE` (→AUDIO), `SMARTWATCH` (→Watch), `IN EAR CORDED EARP` (→Wearable), `메모리카드`/`REMOCON-ECO`/`SOLARCELL REMOTE` (→X)

---

## 참조 파일

| 파일 | 위치 | 용도 |
|---|---|---|
| `currency.csv` | `ref/` | site별 연도별 환율 |
| `best_selling_product_*.csv` | `aa_exports/` | AA export raw |
| `best_selling_product_prior_*.csv` | `aa_exports/` | AA export raw |
| `last_best_selling_product_*.csv` | `aa_exports/` | AA export raw |

---

## 실행 방법

```bash
python "RESHAPE_best_selling_260413_v1.1.py"
```

tb_key별로 파일이 없으면 스킵 후 다음 tb_key 계속 처리.

---

## 주의사항

| 항목 | 내용 |
|---|---|
| `status != "OK"` 행 | 자동 제외됨 (FAILED 등) |
| **`ORDER == 0` 행** | **v1.1부터 자동 제외됨** — shop/camp 각각 필터됨 (한쪽만 0이면 그쪽만 제거) |
| **NaN/공란 PRODUCT** | **v1.1부터 ETC로 분류** (기존엔 Cooking 오분류) |
| 환율 컬럼 자동 선택 | `currency_year`로 시작하는 컬럼 사용 — currency.csv 연도 컬럼 확인 필요 |
| 타임스탬프 패턴 | `_YYYYMMDD_HHMM(SS)` — HHMM 4자리, HHMMSS 6자리 모두 지원 (정렬 시 4자리는 6자리로 zero-pad) |
| REVENUE float | `.round(6)` 처리 후 `%.6f` 포맷 저장 |
| TIER 컬럼 | 현재 공란으로 고정 |
