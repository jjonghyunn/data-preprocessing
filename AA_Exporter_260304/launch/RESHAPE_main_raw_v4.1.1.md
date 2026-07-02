# 후처리 코드 가이드 (RESHAPE_main_raw)  
<sub>2026-04-21  Jonghyun Park w/ Claude</sub>  

이전 버전: `RESHAPE_main_raw_v4.1.ipynb`

---

## 버전 이력

| 버전 | 날짜 | 주요 변경 |
|---|---|---|
| v3 | 이전 | 글로벌 마스터 기준 dummy 삽입 |
| v4 | 2026-04-17 | [FIX-9] dummy 범위를 파일 내 실제 site로 제한; nextpage 분할 병합; `_TB_KEY_REMAP` 추가; `_TS_PAT` 정규식 확장 |
| v4.1 | 2026-04-20 | [FIX-10] post-union dummy 추가 (파일 간 누락 보완) |
| v4.1.1 | 2026-04-21 | 문서 보완 — 전체 내용 통합, 처음 실행자용 가이드 추가 |

---

## 이 노트북이 하는 일

AA(Adobe Analytics)에서 추출한 raw CSV 파일들을 읽어 정제·통합하는 후처리 스크립트.

```
aa_exports/*.csv (raw)
    ↓  wide → long 변환
    ↓  환율 적용
    ↓  컬럼 분리 (J1~J7, REPORT NO.)
    ↓  App 없는 site 0처리
    ↓  dummy 0행 삽입 (site × metric_col 완전성 보장)
    ↓  union 생성
    ↓  post-union dummy 보완
aa_exports/union_YYYYMMDD_HHMMSS.csv (최종 출력)
```

최종 union CSV가 보고서 템플릿의 데이터 소스가 됨.

---

## 처음 실행하는 경우

### 1단계 — 폴더 구조 확인

```
[캠페인 폴더]/
├── launch/
│   ├── RESHAPE_main_raw_v4.1.1.ipynb  ← 이 노트북
│   └── ...
├── ref/
│   ├── tb_column_name_mapping_corrected.csv     ← 필수 마스터
│   ├── currency.csv                   ← 필수 마스터
│   └── app_O_X.csv                    ← 필수 마스터
└── aa_exports/
    ├── 01_*.csv ~ 06_*.csv            ← 추출 노트북 실행 결과
    └── union_*.csv                    ← 이 노트북 실행 결과 (자동 생성)
```

### 2단계 — 실행 전 체크리스트

- [ ] `ref/tb_column_name_mapping_corrected.csv` 존재 확인
- [ ] `ref/currency.csv` 존재 확인 (환율 연도 컬럼 순서: 3번째=TY, 4번째=PY)
- [ ] `ref/app_O_X.csv` 존재 확인 (A열=site_code, B열=O/X)
- [ ] `aa_exports/` 안에 01~06 추출 노트북 실행 결과 CSV 존재 확인
- [ ] FAILED 사이트 있으면 수기 입력 완료 후 실행 (`check_failed_status.py` 참고)
- [ ] 노트북 상단 캠페인 설정값 (`report_no_mapping` 등) 현재 캠페인에 맞게 수정

### 3단계 — 실행

노트북 전체 셀 실행 (Run All).

### 4단계 — 결과 확인

- `aa_exports/union_YYYYMMDD_HHMMSS.csv` 생성 여부
- 콘솔 로그에서 아래 항목 확인:
  - `[WEEKNUM 셀]`, `[읽은 행 수]` — 정상 파싱 여부
  - `→ App 없는 site App 데이터 N행 0처리` — App 없는 site 처리 여부
  - `[FIX-10] REPORT NO. XX: N행 dummy 삽입` — post-union 보완 여부
- 예상 KEY 누락 시 → `check_mapping_match_260313.py` 활용

---

## 캠페인 전용 설정

노트북 상단에서 캠페인마다 아래 값을 수정해야 함.

| 항목 | 설명 |
|---|---|
| `MAPPING_CSV` | `tb_column_name_mapping_corrected.csv` (보통 고정) |
| `report_no_mapping` | 이번 캠페인의 리포트 번호 ↔ 리포트명 매핑 |

```python
# 캠페인마다 리포트 구성이 다르므로 반드시 확인 후 수정
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

`_TB_KEY_REMAP`: 파일명과 매핑 CSV의 tb명이 다를 때 보정. 대부분 비워 둠.

```python
_TB_KEY_REMAP = {
    # 예) "파일명_tb_key": "매핑_csv_tb_key"
}
```

---

## 처리 순서 (내부 동작)

### 1. tb_key별 최신 파일 선택

- 동일 tb_key가 여러 번 추출됐으면 타임스탬프(`_YYYYMMDD_HHMM(SS)`) 기준 최신 1개만 사용
- `_stacked`, `_long`, `union_` prefix 파일은 처리 대상 제외

### 1-1. nextpage 분할 파일 병합

AA에서 next_page 쿼리가 `_ttlmx`/`_vdda` 두 파일로 분리 출력되는 경우 자동 병합.

| 분할 A | 분할 B | 병합 결과 |
|---|---|---|
| `next_page_ttlmx` | `next_page_vdda` | `next_page` |
| `last_next_page_ttlmx` | `last_next_page_vdda` | `last_next_page` |
| `us_next_page_ttlmx` | `us_next_page_vdda` | `us_next_page` |
| `us_last_next_page_ttlmx` | `us_last_next_page_vdda` | `us_last_next_page` |

### 2. Pre-scan (US site_code 수집)

- `us_` prefix 파일 → `_us_sites` 목록 수집
- v4부터 `_global_sites` pre-scan 제거 (dummy 삽입이 파일 내 실제 site 기준으로 변경됐으므로 불필요)

### 3. 리포트 번호 없는 파일 skip

- `_숫자_숫자_` 패턴이 없는 파일은 dummy 삽입·union 모두 제외
- channel 파일은 리포트 번호 관계없이 처리됨

### 4. wide → long 변환 및 환율 적용

- `tb_column_name_mapping_corrected.csv` 기준으로 value1~N → 실제 컬럼명 rename
- `pd.melt`로 wide → long (metric_col / metric_value_origin)
- `revenue` 포함 컬럼만 `currency.csv` 환율 적용 → `metric_value_adj`
- 환율 연도 기준: `End_Date` 연도 사용

### 5. J1~J7, J11(REPORT NO.) 컬럼 분리

- metric_col을 `_`로 분리 → J1~J7 파트
- 숫자_숫자 패턴으로 REPORT NO. 결정 → `report_no_mapping` 참고

### 5-1. App 없는 site 0처리

- `app_O_X.csv` B열 `X`인 site에서 `J5`(DEVICE TYPE) = `app` / `android` / `ios` 인 행 → value=0

### 6. non-channel 파일: year-split 합산 → dummy 0행 삽입

#### 6-1. year-split 합산
- prior 기간이 연도를 넘을 때 AA가 연도별로 행을 분리 추출 → `site × metric_col` 기준으로 재집계
  - `_time` 계열: 평균(mean), 그 외: 합산(sum)

#### 6-2. dummy 0행 삽입 (FIX-9)
- **해당 파일에 실제 존재하는 site만** 기준으로 dummy 삽입 (전체 글로벌 기준 아님)
- US 파일 → `_us_sites` 기준, 글로벌 파일 → 파일 내 실제 site 기준
- `_stacked_separate.csv`로 개별 저장

### 7. channel 파일: 추가 처리

- 7-1. US 채널명 → 글로벌 채널명 매핑
- 7-2. mc_needs_ch / mc_has_ch 구분
- 7-3. dummy 0행 삽입 (FIX-9: 파일 내 실제 site 기준)
- 7-4. PAID/NONPAID 부여

### 8. union 생성

- `all_frames` 합산 → `union_{YYYYMMDD}_{HHMMSS}.csv`
- non-US에 있고 US에 없는 metric_col에 US dummy 0행 자동 삽입
- PAID_NONPAID NaN → `-` fillna

### 8-1. Post-union dummy 삽입 (FIX-10)

**배경**: FIX-9에서 파일 내 실제 site 기준으로 변경했으나, 특정 파일 자체에 없는 site는 그 tb_key의 metric_col dummy가 아예 생성되지 않는 문제 잔존.

예시 — `3_1_external_smartthings_cmp` 파일에 없는 site (AE_AR, IL, MX, PE, TH):
- 해당 site들의 smartthings 관련 KEY가 union에서 통째로 0개

**해결**: union 완성 후 `J11(REPORT NO.)` 기준 그룹핑 → `전체 site × 전체 metric_col` cross product → 누락 조합만 value=0으로 삽입.

```
union_df
  └─ groupby J11
       └─ 각 REPORT NO.별: all_sites × all_metric_cols
            └─ _exists 체크 → 누락 조합만 dummy(0) 삽입
```

- 기존 조합은 `_exists` 체크로 중복 삽입 방지
- 메타(Subsidiary, Country, RSID, Start_Date, End_Date)는 site별 mode 값으로 채움
- J1~J11, metric_name, PAID_NONPAID는 metric_col별 기존 값 참조

---

## 출력 컬럼 구조 (finalize_df 기준)

```
TIER, SUBS, COUNTRY, SITE CODE, REPORT NO., DIVISION, DATE, DEVICE TYPE, TYPE, LOGIN/NON,
PAID/NONPAID, ITEM, VALUE, KEY, 공란1, 공란2, 공란3, 공란4, value_origin, start_date, end_date
```

---

## 주의사항

| 항목 | 내용 |
|------|------|
| `report_no_mapping` | 캠페인마다 리포트 구성이 다름 — 반드시 확인 후 수정 |
| `app_O_X.csv` | B열 값은 `O` 또는 `X`. 대소문자 무관 처리됨 |
| 환율 연도 기준 | End_Date 연도 기준. `currency.csv` 연도 컬럼 순서 확인 필요 |
| 동일 tb_key 중복 추출 | 타임스탬프 기준 최신 파일만 사용됨 |
| FAILED 데이터 | 수기 보완 전 실행하면 해당 site가 dummy 0으로 들어감 |
| `_TS_PAT` 타임스탬프 정규식 | `\d{4,6}` — HHMM·HHMMSS 모두 처리 가능 |

---

## 보조 스크립트

### check_failed_status.py
- `aa_exports/` CSV 파일별 FAILED 건수 일괄 확인
- 실행 전 FAILED 사이트 파악에 사용

### check_mapping_match_260313.py
- `aa_exports/` CSV의 컬럼명 vs `tb_column_name_mapping_corrected.csv` 매핑 검수
- KEY 누락 원인 추적에 사용
