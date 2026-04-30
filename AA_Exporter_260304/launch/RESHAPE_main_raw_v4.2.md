# 후처리 코드 가이드 -- 2026-04-23 Jonghyun Park w/ Claude

AA 추출 후 정제·통합하는 메인 노트북.

```
RESHAPE_main_raw_v4.2.ipynb
```

베이스: `RESHAPE_main_raw_v4.1.ipynb`

---

## 버전 이력

| 버전 | 날짜 | 주요 변경 |
|---|---|---|
| v3 | 이전 | 글로벌 마스터 기준 dummy 삽입 |
| v4 | 2026-04-17 | [FIX-9] dummy 범위를 파일 내 실제 site로 제한; nextpage 분할 병합; `_TB_KEY_REMAP` 추가 |
| v4.1 | 2026-04-20 | [FIX-10] post-union dummy 추가 (파일 간 누락 보완) |
| v4.2 | 2026-04-23 | [FIX-11] 추출 0행 fallback dummy 생성 |

---

## [FIX-11] 추출 0행 fallback dummy (v4.2 신규)

### 문제

AA 추출 결과 CSV가 0행(미추출)이면 `df_long`도 0행이 됩니다.

- `_insert_nonchannel_dummy`: `all_sites = []`, `metric_cols = []` → cross product 불가 → dummy 생성 안 됨
- `FIX-10`: union에 해당 `metric_col` 자체가 없으면 추가 불가

결과적으로 해당 tb_key의 metric_col이 union에서 통째로 누락됩니다.

**실제 발생 케이스**: `last_3_1_external_smartthings_cmp`, `last_3_1_external_smartthings_push_cmp`
- 26cmp / 26prior에는 pc/mobile/app/android/ios device type 각 행 존재
- 25cmp(last)는 추출 0행 → device type 행 전체 누락

### 해결

**(1) Pre-scan 확장** — `_fallback_dates` 수집

```python
_fallback_dates = {}  # (is_last: bool, site_code) → {"Start_Date": ..., "End_Date": ...}
```

- `last_` prefix 여부로 구분해 Start_Date / End_Date를 site별로 수집
- 추출 0행 파일에 날짜 정보를 제공하기 위한 용도

**(2) FIX-11 fallback** — `df_long`이 비었을 때 seed 생성

```python
if df_long.empty and value_vars and _site_meta_map:
    _is_last_fb = tb_key.startswith("last_") and not _is_us_table(tb_key)
    # value_vars × _site_meta_map 전체 site로 0값 seed DataFrame 생성
    # 날짜는 _fallback_dates에서 동일 prefix 파일로부터 차용
```

- `value_vars`: 매핑 CSV에서 실제 `value1~N`으로 정의된 유효 컬럼
- `_site_meta_map`: pre-scan에서 수집한 전체 site (Subsidiary / Country / RSID)
- 날짜: `_fallback_dates[(is_last, site)]`에서 동일 캠페인 prefix의 다른 파일에서 차용
- seed 생성 후 `_apply_j_cols` 적용 → `_insert_nonchannel_dummy`가 정상 동작

### 실행 로그 예시

```
▶ Pre-scan 확장: last 날짜 31개 site, cur 날짜 31개 site 수집

  last_3_1_external_smartthings_cmp → 추출 0행: 31site × 5metric → 155행 fallback dummy [FIX-11]
  last_3_1_external_smartthings_push_cmp → 추출 0행: 31site × 5metric → 155행 fallback dummy [FIX-11]
```

이후 FIX-10(post-union dummy)이 동일 J11 그룹 내 site 간 cross product를 수행해 최종 정합성을 확보합니다.

---

## 캠페인 전용 설정 예시

| 항목 | 값 |
|---|---|
| `MAPPING_CSV` | `tb_column_name_mapping.csv` |
| `report_no_mapping` | 1_1~5_1 (캠페인 기준) |

```python
report_no_mapping = {
    "1_1": "1. Campaign Basic Traffic",
    "2_1": "2. Campaign Time Spent Per Visit By Country",
    "3_1": "3-1. Campaign Internal/External Traffic By Channel",
    "3_2": "3-2. Campaign Order Conversion/Traffic By Channel",
    "3_3": "3-3. Campaign Home Kv & Offer Kv Clicks",
    "4_1": "4-1. Campaign Order Conversion Funnel",
    "4_2": "4-2. Campaign Order Conversion Funnel (Login/Non-Login)",
    "5_1": "5. Campaign Order Conversion",
}
```

---

## 사전 준비

### 필수 마스터 파일

| 파일 | 내용 |
|------|------|
| `../ref/tb_column_name_mapping.csv` | value_n → 컬럼명 매핑 마스터 |
| `../ref/currency.csv` | 환율 (3번째 컬럼=latest연도, 4번째 컬럼=prior연도) |
| `../ref/app_O_X.csv` | site_code별 App 유무 (A열=site_code, B열=O/X) |

### aa_exports 폴더 상태 확인

- 6개 추출 노트북(`01~06`)이 모두 실행된 상태여야 함
- FAILED 사이트는 수기 입력 완료 후 실행할 것 (`check_failed_status.py` 참고)
- **추출 0행 파일이 있어도 v4.2에서 자동 fallback dummy 생성됨** (FIX-11)

---

## 처리 순서

### 1. tb_key별 최신 파일 선택

- `_stacked`, `_long`, `union_` prefix 파일은 처리 대상 제외

### 1-1. nextpage 분할 파일 병합

| 분할 A | 분할 B | 병합 결과 |
|---|---|---|
| `next_page_ttlmx` | `next_page_vdda` | `next_page` |
| `last_next_page_ttlmx` | `last_next_page_vdda` | `last_next_page` |
| `us_next_page_ttlmx` | `us_next_page_vdda` | `us_next_page` |
| `us_last_next_page_ttlmx` | `us_last_next_page_vdda` | `us_last_next_page` |

### 2. Pre-scan

- Subsidiary / Country / RSID per site → `_site_meta_map`
- US site 목록 → `_us_sites`
- **[FIX-11 신규]** Start_Date / End_Date per (last prefix, site) → `_fallback_dates`

### 3. 리포트 번호 없는 파일 skip

### 4. wide → long 변환 및 환율 적용

### 5. J1~J7, J11 컬럼 분리

### 5-1. App 없는 site 0처리

### 6. non-channel 파일: year-split 합산 → dummy 0행 삽입

#### 6-1. year-split 합산

#### 6-2. [FIX-11] 추출 0행 fallback (v4.2 신규)

추출 CSV가 0행이면 `value_vars × _site_meta_map` 전체 site로 seed 생성.  
날짜는 `_fallback_dates`에서 동일 prefix(last/non-last)의 다른 파일로부터 차용.

#### 6-3. dummy 0행 삽입 (FIX-9)

**파일 내 실제 존재하는 site** 기준으로 누락 site × metric_col 조합에 0행 삽입.  
FIX-11 fallback seed가 있으면 모든 조합이 이미 채워진 상태이므로 추가 삽입 없음.

### 7. channel 파일: 추가 처리

### 8. union 생성

### 8-1. Post-union dummy 삽입 (FIX-10)

FIX-11로 last_ 0행 파일의 metric_col이 union에 진입하면,  
FIX-10이 동일 J11 그룹 내 누락 site에 대해 추가 cross product를 수행합니다.

---

## 출력 컬럼 구조

```
TIER, SUBS, COUNTRY, SITE CODE, REPORT NO., DIVISION, DATE, DEVICE TYPE, TYPE, LOGIN/NON,
PAID/NONPAID, ITEM, VALUE, KEY, 공란1, 공란2, 공란3, 공란4, value_origin, start_date, end_date
```

---

## 실행 후 확인 사항

1. `[FIX-11]` 로그 확인 — 추출 0행 파일이 fallback dummy를 생성했는지 확인
2. App 없는 site의 `→ App 없는 site App 데이터 N행 0처리` 로그 확인
3. `aa_exports/union_{timestamp}.csv` 파일 생성 확인
4. Post-union dummy 삽입 로그 확인 (FIX-10)

---

## 주의사항

| 항목 | 내용 |
|------|------|
| FIX-11 site 범위 | fallback은 `_site_meta_map` 전체 site 기준 → 해당 tb에 없는 나라도 포함됨. FIX-10이 J11 그룹 내 정합성을 최종 보정 |
| app_O_X.csv | B열 값은 `O` 또는 `X`로 관리 |
| 환율 연도 기준 | End_Date 연도 기준. currency.csv 연도 컬럼 확인 필요 |
| 동일 tb_key 중복 추출 | 타임스탬프 기준 최신 파일만 사용 |
| FAILED 데이터 | 수기 보완 전 실행하면 해당 site가 dummy 0으로 들어감 |
| `_TB_KEY_REMAP` | 파일명과 매핑 CSV tb명이 다를 때 보정 딕셔너리 |
| `_TS_PAT` 타임스탬프 정규식 | `\d{4,6}` — HHMM·HHMMSS 모두 처리 가능 |

---

## 보조 스크립트

### check_failed_status.py
- CSV 파일별 FAILED 건수 일괄 확인

### check_mapping_match.py
- `aa_exports/` CSV vs `tb_column_name_mapping.csv` 컬럼 매핑 검수
