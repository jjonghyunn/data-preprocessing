# 후처리 코드 가이드 -- 2026-03-31 Jonghyun Park (최종수정 260410)

AA 추출 후 정제·통합하는 메인 노트북.

```
stack_n_currency_n_chnl_n_seaprate_(by종현과장님)v3.1.ipynb
```

---

## v3 → v3.1 변경사항 (2026-04-10, Jonghyun Park)

### [FIX-9] 타임스탬프 정규식 수정 (`_TS_PAT`: `\d{6}` → `\d{4}`)

- **문제**: `_TS_PAT = re.compile(r"_(\d{8}_\d{6})$")` 가 실제 파일 타임스탬프(`YYYYMMDD_HHMM`, 4자리) 와 불일치 → deduplication 실패 → 동일 tb_key 파일이 2개 이상일 때 모두 처리됨
- **수정**: `\d{6}` → `\d{4}` (HHMM 형식에 맞게)
- **효과**: 최신 파일 1개만 선택, union에 중복 데이터 삽입 방지

### [FIX-10] `_is_channel_table` — `3_1_channel_external` 포함

- **문제**: FIX-2에서 channel 판별을 `3_2`, `7_1` 패턴으로만 제한하면서 `3_1_channel_external_cmp`가 non-channel 경로로 처리됨 → `value` 컬럼(채널명) 무시 → stacked_separate·union의 ITEM=NaN
- **수정**: `_CHANNEL_TABLE_PATTERNS`에 `3_1_channel_external` 패턴 추가
- **효과**: `3_1_channel_external_cmp` 및 `_prior`의 채널명이 ITEM으로 정상 입력, PAID_NONPAID 분류도 적용됨
- **참고**: `3_1_channel_internal`은 column명에 이미 채널명이 내장되어 있어 non-channel 처리 유지

---

## v2 → v3 변경사항 (2026-03-31, Jonghyun Park)

### [FIX-5] 더미 삽입 US 포함 여부 확인

- **결과**: `_global_sites -= _us_sites` 로직으로 이미 올바르게 분리됨
- 글로벌 더미에 US site 미포함, US 더미에만 US site 적용 확인
- Pre-scan 완료 후 `_global_sites & _us_sites` 중복 검증 로그 추가
  - 중복 없으면: `[FIX-5 확인] Global/US site 중복 없음 → 더미 삽입 기준 올바름 ✓`
  - 중복 감지 시: `[WARN] Global/US site 중복 감지: {...}` 경고 출력

### [FIX-6] App 없는 site의 App 데이터 0처리 (신규)

- **기준 파일**: `ref/app_O_X.csv`
  - A열: `site_code`
  - B열: `O`(앱 있음) / `X`(앱 없음)
- **처리 방식**: B열이 `X`인 site에 대해, `J5`(DEVICE TYPE) 값이 `app`, `android`, `ios`인 행의 수치를 `0`으로 처리 (행 삭제 아님)
  - `metric_value_origin = 0.0`
  - `metric_value_adj = 0.0`
- **적용 시점**: `_apply_j_cols` 호출 후, dummy 삽입 전
- **대소문자**: `str.lower()` 비교로 무관
- **로그**: `{tb_key} → App 없는 site App 데이터 {n}행 0처리`

### [FIX-7] Revenue 환율 적용 기준 연도를 End_Date 기준으로 변경

- **기존**: `pd.to_datetime(df_long["Start_Date"]).dt.year`
- **변경**: `pd.to_datetime(df_long["End_Date"]).dt.year`
- **이유**: 리포팅 기간이 연도를 걸치는 경우(예: 2025-12-01 ~ 2026-01-31) start date가 아닌 end date 연도의 환율을 적용하는 것이 맞음

---

## 사전 준비

### 필수 마스터 파일

| 파일 | 내용 |
|------|------|
| `tb_column_name_mapping.csv` | value_n → 컬럼명 매핑 마스터 |
| `currency.csv` | 환율 (3번째 컬럼=latest연도, 4번째 컬럼=prior연도) |
| `app_O_X.csv` | site_code별 App 유무 (A열=site_code, B열=O/X) |

### aa_exports 폴더 상태 확인

- 6개 추출 노트북(`01~06`)이 모두 실행된 상태여야 함
- FAILED 사이트는 수기 입력 완료 후 실행할 것 (`check_failed_status.py` 참고)
- VRS 등 누락 사이트의 value# 값도 CSV에 채운 후 실행

---

## 처리 순서

### 1. tb_key별 최신 파일 선택

- `aa_exports/` 내 동일 tb_key로 여러 번 추출된 경우 타임스탬프(`_YYYYMMDD_HHMMSS`) 기준 최신 파일 1개만 사용
- `_stacked`, `_long`, `union_` prefix 파일은 처리 대상 제외

### 2. Pre-scan (전체 site_code 수집)

- 처리 전 전체 CSV를 스캔하여 site_code 목록 및 메타(Subsidiary, Country, RSID) 수집
- `us_` prefix 파일 → `_us_sites` 목록
- 그 외 → `_global_sites` 목록
- 이후 dummy 삽입의 기준이 됨
- **[FIX-5]** Pre-scan 완료 후 `_global_sites & _us_sites` 중복 검증 로그 출력

### 3. 리포트 번호 없는 파일은 전체 skip

- `_숫자_숫자_` 패턴이 없는 파일(`bestselling`, `nextpage`, `raw_multi_purchase_v41` 등)은 dummy 삽입·union 모두 제외
- channel 파일은 리포트 번호 관계없이 처리됨 (tb_key에 `channel` 포함)

### 4. wide → long 변환 및 환율 적용

- `tb_column_name_mapping.csv` 기준으로 value1~N → 실제 컬럼명 rename
- `pd.melt`로 wide → long (metric_col / metric_value_origin)
- `revenue` 포함 컬럼만 `currency.csv` 환율 적용 → `metric_value_adj`
- **[FIX-7]** 환율 연도 기준: `End_Date` 연도 사용 (기존 Start_Date에서 변경)

### 5. J1~J7, J11(REPORT NO.) 컬럼 분리

- metric_col을 `_`로 분리하여 J1~J7 파트로 분해
- 숫자_숫자 패턴으로 REPORT NO. 결정 → `report_no_mapping` 딕셔너리 참고

### 5-1. App 없는 site 0처리 (신규, FIX-6)

- `_apply_j_cols` 직후 실행
- `app_O_X.csv` B열 `X`인 site에서 `J5`(DEVICE TYPE) = `app` / `android` / `ios` 인 행의 값을 `0`으로 처리

### 6. non-channel 파일: year-split 합산 → dummy 0행 삽입

#### 6-1. year-split 합산
- prior 기간이 연도를 넘을 때 AA가 연도별로 행을 분리 추출함 (value = "2025", "2026" 등)
- `value`가 `^20\d{2}` 패턴인 행들을 `site × metric_col` 기준으로 집계
  - `_time` 계열 (`metric_col`에 `"time"` 포함): **평균** (mean)
  - 그 외: **합산** (sum)
- `itemId`는 연도별로 다르므로 groupby 제외 → `first`로 처리

#### 6-2. dummy 0행 삽입
- pre-scan 기준 마스터 site_code에서 해당 파일에 없는 site에 dummy 0행 삽입
- US 파일 → `_us_sites` 기준, 글로벌 파일 → `_global_sites` 기준
- `_stacked_separate.csv`로 개별 저장

### 7. channel 파일: 추가 처리

#### 7-1. US 채널명 → 글로벌 채널명 매핑
- US는 AA Report Suite가 달라 채널명이 다름 → `us_mapping` 딕셔너리로 변환

#### 7-2. mc_needs_ch / mc_has_ch 구분
- **mc_needs_ch**: metric_col이 `_`로 끝나는 컬럼 → 채널명은 value(row) 기준으로 붙임
- **mc_has_ch**: metric_col에 채널명이 내장된 컬럼 → value(row) 그대로 유지

#### 7-3. dummy 0행 삽입 (채널 × site × metric_col 크로스곱)
- mc_needs_ch: `site × channel × metric_col` 크로스곱 기준
  - 채널 마스터: US/글로벌 모두 `global_paid_mapping` 전체 키 기준
- mc_has_ch: `site × metric_col` 크로스곱

#### 7-4. PAID/NONPAID 부여

### 8. union 생성

- `all_frames` 합산 → `union_{YYYYMMDD}_{HHMMSS}.csv`
- non-US에 있고 US에 없는 **모든** metric_col에 US dummy 0행 자동 삽입
- PAID_NONPAID NaN → `-` fillna

---

## 출력 컬럼 구조 (finalize_df 기준)

```
TIER, SUBS, COUNTRY, SITE CODE, REPORT NO., DIVISION, DATE, DEVICE TYPE, TYPE, LOGIN/NON,
PAID/NONPAID, ITEM, VALUE, KEY, 공란1, 공란2, 공란3, 공란4, value_origin, start_date, end_date
```

---

## 실행 후 확인 사항

1. 셀 출력의 `[FIX-5 확인] Global/US site 중복 없음` 메시지 확인
2. App 없는 site의 `→ App 없는 site App 데이터 N행 0처리` 로그 확인
3. `aa_exports/union_{timestamp}.csv` 파일 생성 확인
4. 예상 KEY 누락 여부 확인 시 → `check_41.py` 등 보조 스크립트 활용

---

## 주의사항

| 항목 | 내용 |
|------|------|
| app_O_X.csv | B열 값은 `O` 또는 `X`로 관리. 대소문자 무관 처리됨 |
| 환율 연도 기준 | End_Date 연도 기준으로 변경됨 (v3 FIX-7). currency.csv 연도 컬럼 확인 필요 |
| 동일 tb_key 중복 추출 | 타임스탬프 기준 최신 파일만 사용됨 |
| FAILED 데이터 | 수기 보완 전 실행하면 해당 site가 dummy 0으로 들어감 |
| currency.csv 컬럼 순서 | 3번째=latest연도, 4번째=prior연도로 고정 |

---

## 보조 스크립트

### check_failed_status.py
- CSV 파일별 FAILED 건수 일괄 확인

### check_mapping_match.py
- `aa_exports/` CSV vs `tb_column_name_mapping.csv` 컬럼 매핑 검수
