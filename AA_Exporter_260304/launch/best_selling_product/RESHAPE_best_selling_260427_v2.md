# RESHAPE_best_selling_260427_v2.py 가이드
<!-- 2026-04-27  Jonghyun Park w/ Claude -->

`best_selling_product` raw CSV → 정제 CSV (`_stacked_separate`) 생성 스크립트.  
SQL 기준: `best selling product_260212(카테고리displayname스페인어보완).sql`

---

## v1 → v2 변경사항

| 항목 | v1 | v2 |
|---|---|---|
| 출력 컬럼 | 11개 | **12개** (`SITE CODE` 다음 `WEB/APP` 추가) |
| value 컬럼 | value1~4 | **value1~8** (1~4=Web, 5~8=App) |
| 한 raw 행 → 출력 | 2줄 (S.com / Campaign) | **4줄** (Web S.com / Web Campaign / App S.com / App Campaign) |
| PRODUCT 공란 처리 | NaN→"NA" prefix→Cooking 오분류 | **CATEGORY=ETC 강제** (NaN/None/공백/공란 모두) |

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
    ├─ 타임스탬프 기준 최신 파일 1개 선택 (_TS_PAT: _YYYYMMDD_HHMM)
    ├─ status == "OK" 행만 유지
    ├─ value1~8 숫자 변환 (coerce → fillna 0)
    ├─ DIVISION / CATEGORY 분류 (value 컬럼 = 제품 모델번호 기준)
    │     · PRODUCT 공란/NaN → CATEGORY=ETC 강제
    ├─ SITE CODE 정규화
    ├─ 환율 적용 (REVENUE = value{2,4,6,8} × rate)
    │
    ├─ Web S.com    : STANDARD="S.com",    WEB/APP="WEB", ORDER=value1, REVENUE=value2×rate
    ├─ Web Campaign : STANDARD="Campaign", WEB/APP="WEB", ORDER=value3, REVENUE=value4×rate
    ├─ App S.com    : STANDARD="S.com",    WEB/APP="APP", ORDER=value5, REVENUE=value6×rate
    └─ App Campaign : STANDARD="Campaign", WEB/APP="APP", ORDER=value7, REVENUE=value8×rate
          ↓
    concat → {tb_key}_stacked_separate.csv  (raw 1행 → 4행)
```

---

## 출력 컬럼 구조

```
PERIOD, STANDARD, TIER, SUBS, COUNTRY, SITE CODE, WEB/APP, DIVISION, PRODUCT, CATEGORY, ORDER, REVENUE
```

| 컬럼 | 내용 |
|---|---|
| `PERIOD` | TB_KEYS 설정값 (예: `2026 Campaign Period`) |
| `STANDARD` | `S.com` 또는 `Campaign` |
| `TIER` | 공란 |
| `SUBS` | `Subsidiary` 원본값 |
| `COUNTRY` | `Country` 원본값 |
| `SITE CODE` | 정규화된 site code |
| `WEB/APP` | `WEB` 또는 `APP` |
| `DIVISION` | MX / VD / DA / ETC |
| `PRODUCT` | `value` 원본 (제품 모델명) |
| `CATEGORY` | SMP / TV / REF / AC / Washer / Tablet / NPC / Wearable / Monitor / Sound Bar / Cooking / VC / ACC / Air Purifier / Dryer / Air Dresser / Shoe Dresser / DW / AUDIO / BUNDLE / X / ETC |
| `ORDER` | Web S.com=`value1`, Web Campaign=`value3`, App S.com=`value5`, App Campaign=`value7` |
| `REVENUE` | 같은 순서로 `value{2,4,6,8} × rate` (소수점 6자리) |

---

## PRODUCT 공란 → ETC 처리 (v2 신규)

v1에서 `value`가 NaN이면 `str(nan)` → `"NAN"` → `startswith("NA")` 매칭으로 **Cooking**으로 잘못 분류되던 문제 차단.

처리 위치: `get_category()` 함수 진입부에서 아래 케이스를 모두 ETC로 즉시 반환.

| 입력 | 처리 |
|---|---|
| `pd.NaN` / `None` | `"ETC"` |
| 빈 문자열 `""` | `"ETC"` |
| 공백만 (`" "`, `"  "` 등) | `"ETC"` |
| 문자열 `"NAN"` (대소문자 무관) | `"ETC"` |

DIVISION은 v1 기준에서도 빈 값 → 마지막 `return "ETC"`로 빠져 영향 없음.

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
| MX | SM-S/G/A/F/M/E/W/X/P/T/R/Q/L, NT, NP, SM-R/Q/L, F-9/A/F7/M/S7/S9/X/NP, GALAXY WATCH, XE5/XE3 |
| VD | GQ/KQ/QA/QE/QN/TQ/UN/UA/UE/KU, LS/LF/LT/LU/LV/LC, HW-Q/S/A/B/C/LS/T, F-55/65/80/58/70/75/85/LS/Q/UN/3X, S2/S3/C2/C3 등 |
| DA | AF/AC/AR/AJ/AM/AW/AX/AY, WW/WA/WV/WD/WF/WR/WH/WT, DV/DF/DJ, RB/RF/RL/RQ/RR/RS/RT/RW/RZ/RH/RP, VR/VS/VC, ME/MJ/ML/MM/MQ/MW, NA~NZ, MC/MG/MS/DW 등 |
| ETC | LUMAFUSION, ARCSITE, UNSPECIFIED, 빈 값/NaN, 기타 미매칭 |

---

## CATEGORY 분류 기준

`value` prefix 기반 (DIVISION보다 세분화). 스페인어 displayname 대응 fallthrough 로직 포함.

| CATEGORY | 주요 조건 |
|---|---|
| SMP | SM-S/G/A/F/M/E/W/N 등 (스마트폰) |
| Tablet | SM-X/P/T |
| NPC | NT, NP, XE |
| Wearable | SM-R/Q/L, L325N/L705N/L330N/L500N, GALAXY WATCH |
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
| ETC | **PRODUCT 공란/NaN (v2 신규)**, 미매칭 |

**스페인어 displayname fallthrough** (prefix 미매칭 시):  
`MONITOR`, `CAMPAIGN NAME` (→TV), `FUNDA`/`SOPORTE` (→ACC), `BUDS` (→Wearable), `AIRE ACONDICIONADO` (→AC), `SMART TV` (→TV), `REFRIGERADOR` (→REF), `AURA STUDIO`/`JBL LIVE 770NC`/`TUNE BEAM`/`JBL TOUR ONE` (→AUDIO), `GALAXY WATCH` (→Watch), `IN EAR CORDED EARP` (→Wearable), `메모리카드`/`REMOCON-ECO`/`SOLARCELL REMOTE` (→X)

---

## 참조 파일

| 파일 | 위치 | 용도 |
|---|---|---|
| `currency.csv` | `ref/` | site별 연도별 환율 |
| `best_selling_product_*.csv` | `aa_exports/` | AA export raw (value1~8 포함) |
| `best_selling_product_prior_*.csv` | `aa_exports/` | AA export raw |
| `last_best_selling_product_*.csv` | `aa_exports/` | AA export raw |

---

## 실행 방법

```bash
python RESHAPE_best_selling_260427_v2.py
```

tb_key별로 파일이 없으면 스킵 후 다음 tb_key 계속 처리.

---

## 주의사항

| 항목 | 내용 |
|---|---|
| raw CSV value 컬럼 | **value1~8 모두 존재해야 함** (v1은 1~4까지). 누락 시 `KeyError` |
| `status != "OK"` 행 | 자동 제외됨 (FAILED 등) |
| 환율 컬럼 자동 선택 | `currency_year`로 시작하는 컬럼 사용 — currency.csv 연도 컬럼 확인 필요 |
| 타임스탬프 패턴 | `_YYYYMMDD_HHMM` (4자리 시분) — 6자리면 매칭 안됨 |
| REVENUE float | `.round(6)` 처리 후 `%.6f` 포맷 저장 |
| TIER 컬럼 | 현재 공란으로 고정 |
| 출력 행수 | raw 행수 × 4 (Web S.com / Web Campaign / App S.com / App Campaign) |
