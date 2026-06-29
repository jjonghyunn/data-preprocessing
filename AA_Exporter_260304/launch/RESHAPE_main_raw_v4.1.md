# 후처리 코드 가이드  
<sub>2026-04-21  Jonghyun Park w/ Claude</sub>  

AA 추출 후 정제·통합하는 메인 노트북.

```
RESHAPE_main_raw_v4.1.ipynb
```

베이스: `RESHAPE_main_raw_v4.ipynb`

---

## 버전 이력

| 버전 | 날짜 | 주요 변경 |
|---|---|---|
| v3 | 이전 | 글로벌 마스터 기준 dummy 삽입 |
| v4 | 2026-04-17 | [FIX-9] dummy 범위를 파일 내 실제 site로 제한; nextpage 분할 병합; `_TB_KEY_REMAP` 추가; `_TS_PAT` 정규식 확장 |
| v4.1 | 2026-04-20 | [FIX-10] post-union dummy 추가 (파일 간 누락 보완) |

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
- VRS 등 누락 사이트의 value# 값도 CSV에 채운 후 실행

---

## 처리 순서

### 1. tb_key별 최신 파일 선택

- `aa_exports/` 내 동일 tb_key로 여러 번 추출된 경우 타임스탬프(`_YYYYMMDD_HHMM(SS)`) 기준 최신 파일 1개만 사용
- `_stacked`, `_long`, `union_` prefix 파일은 처리 대상 제외

### 1-1. nextpage 분할 파일 병합

AA에서 next_page 쿼리가 두 파일(`_ttlmx`, `_vdda`)로 분리 출력되는 경우 처리 전 자동 병합.

| 분할 A | 분할 B | 병합 결과 |
|---|---|---|
| `next_page_ttlmx` | `next_page_vdda` | `next_page` |
| `last_next_page_ttlmx` | `last_next_page_vdda` | `last_next_page` |
| `us_next_page_ttlmx` | `us_next_page_vdda` | `us_next_page` |
| `us_last_next_page_ttlmx` | `us_last_next_page_vdda` | `us_last_next_page` |

분할 파일이 없으면 아무것도 하지 않음.

### 2. Pre-scan (US site_code 수집)

- `us_` prefix 파일 → `_us_sites` 목록 수집
- `_global_sites` pre-scan 제거 (FIX-9에서 dummy 삽입이 파일 내 실제 site 기준으로 변경됐으므로 불필요)

### 3. 리포트 번호 없는 파일은 전체 skip

- `_숫자_숫자_` 패턴이 없는 파일은 dummy 삽입·union 모두 제외
- channel 파일은 리포트 번호 관계없이 처리됨

### 4. wide → long 변환 및 환율 적용

- `tb_column_name_mapping.csv` 기준으로 value1~N → 실제 컬럼명 rename
- `pd.melt`로 wide → long (metric_col / metric_value_origin)
- `revenue` 포함 컬럼만 `currency.csv` 환율 적용 → `metric_value_adj`
- 환율 연도 기준: `End_Date` 연도 사용

### 5. J1~J7, J11(REPORT NO.) 컬럼 분리

- metric_col을 `_`로 분리하여 J1~J7 파트로 분해
- 숫자_숫자 패턴으로 REPORT NO. 결정 → `report_no_mapping` 딕셔너리 참고

### 5-1. App 없는 site 0처리

- `_apply_j_cols` 직후 실행
- `app_O_X.csv` B열 `X`인 site에서 `J5`(DEVICE TYPE) = `app` / `android` / `ios` 인 행의 값을 `0`으로 처리

### 6. non-channel 파일: year-split 합산 → dummy 0행 삽입

#### 6-1. year-split 합산
- prior 기간이 연도를 넘을 때 AA가 연도별로 행을 분리 추출함
- `value`가 `^20\d{2}` 패턴인 행들을 `site × metric_col` 기준으로 집계
  - `_time` 계열: 평균(mean), 그 외: 합산(sum)

#### 6-2. dummy 0행 삽입 (FIX-9)
- **해당 파일의 df_long에 실제 존재하는 site만** 기준으로 dummy 삽입
- US 파일 → `_us_sites` 기준, 글로벌 파일 → 파일 내 실제 site 기준
- `_stacked_separate.csv`로 개별 저장

### 7. channel 파일: 추가 처리

#### 7-1. US 채널명 → 글로벌 채널명 매핑
#### 7-2. mc_needs_ch / mc_has_ch 구분
#### 7-3. dummy 0행 삽입 (FIX-9: 파일 내 실제 site 기준)
#### 7-4. PAID/NONPAID 부여

### 8. union 생성

- `all_frames` 합산 → `union_{YYYYMMDD}_{HHMMSS}.csv`
- non-US에 있고 US에 없는 metric_col에 US dummy 0행 자동 삽입 (실제 존재 site 기준)
- PAID_NONPAID NaN → `-` fillna

### 8-1. Post-union dummy 삽입 (FIX-10)

FIX-9에서 파일 내 실제 site만 대상으로 dummy를 생성하도록 변경했으나,
**특정 파일 자체에 없는 site**는 해당 tb_key의 metric_col dummy가 아예 생성되지 않았음.

예시 — `3_1_external_smartthings_cmp` 파일에 없는 site:
- AE_AR, IL, MX, PE, TH (5개)
- → union에서 smartthings 관련 KEY가 통째로 0개

**해결**: union 생성 후 `J11(REPORT NO.)` 기준으로 그룹핑 → 각 그룹에서
`전체 site × 전체 metric_col` cross product → 누락 조합만 value=0으로 삽입.

```
union_df
  └─ groupby J11
       └─ 각 REPORT NO.별: all_sites × all_metric_cols
            └─ _exists 체크 → 누락 조합만 dummy(0) 삽입
```

- 기존 조합은 `_exists` 체크로 중복 삽입 방지
- 메타(Subsidiary, Country, RSID, Start_Date, End_Date)는 site별 mode 값으로 채움
- J1~J11, metric_name, PAID_NONPAID는 metric_col별 기존 값 참조

**효과**: 동일 REPORT NO. 내 모든 site가 동일한 metric_col 집합을 가짐
→ union 행수 증가, KEY 기준 vlookup/피벗 정합성 확보

---

## 출력 컬럼 구조 (finalize_df 기준)

```
TIER, SUBS, COUNTRY, SITE CODE, REPORT NO., DIVISION, DATE, DEVICE TYPE, TYPE, LOGIN/NON,
PAID/NONPAID, ITEM, VALUE, KEY, 공란1, 공란2, 공란3, 공란4, value_origin, start_date, end_date
```

---

## 실행 후 확인 사항

1. App 없는 site의 `→ App 없는 site App 데이터 N행 0처리` 로그 확인
2. `aa_exports/union_{timestamp}.csv` 파일 생성 확인
3. Post-union dummy 삽입 로그 확인 (FIX-10: REPORT NO.별 누락 조합 수)
4. 예상 KEY 누락 여부 확인 시 → 보조 스크립트 활용

---

## 주의사항

| 항목 | 내용 |
|------|------|
| app_O_X.csv | B열 값은 `O` 또는 `X`로 관리. 대소문자 무관 처리됨 |
| 환율 연도 기준 | End_Date 연도 기준. currency.csv 연도 컬럼 확인 필요 |
| 동일 tb_key 중복 추출 | 타임스탬프 기준 최신 파일만 사용됨 |
| FAILED 데이터 | 수기 보완 전 실행하면 해당 site가 dummy 0으로 들어감 |
| currency.csv 컬럼 순서 | 3번째=latest연도, 4번째=prior연도로 고정 |
| `_TB_KEY_REMAP` | 파일명과 매핑 CSV tb명이 다를 때 보정 딕셔너리. 캠페인별 필요 시 추가 |
| `_TS_PAT` 타임스탬프 정규식 | `\d{4,6}` — HHMM·HHMMSS 모두 처리 가능 |

---

## 보조 스크립트

### check_failed_status.py
- CSV 파일별 FAILED 건수 일괄 확인

### check_mapping_match.py
- `aa_exports/` CSV vs `tb_column_name_mapping.csv` 컬럼 매핑 검수
