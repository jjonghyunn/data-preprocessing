# 후처리 코드 가이드 -- 2026 03 16 jonghyun (최종수정 260316)

AA 추출 후 정제·통합하는 메인 노트북.

```
stack_n_currency_n_chnl_n_seaprate_260313.ipynb
```

---

## 사전 준비

### 필수 마스터 파일

| 파일 | 내용 |
|------|------|
| `tb_column_name_mapping.csv` | value_n → 컬럼명 매핑 마스터 |
| `currency.csv` | 환율 (3번째 컬럼=latest연도, 4번째 컬럼=prior연도) |

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

### 3. 리포트 번호 없는 파일은 전체 skip

- `_숫자_숫자_` 패턴이 없는 파일(`bestselling`, `nextpage`, `raw_multi_purchase_v41` 등)은 dummy 삽입·union 모두 제외
- channel 파일은 리포트 번호 관계없이 처리됨 (tb_key에 `channel` 포함)

### 4. wide → long 변환 및 환율 적용

- `tb_column_name_mapping.csv` 기준으로 value1~N → 실제 컬럼명 rename
- `pd.melt`로 wide → long (metric_col / metric_value_origin)
- `revenue` 포함 컬럼만 `currency.csv` 환율 적용 → `metric_value_adj`

### 5. J1~J7, J11(REPORT NO.) 컬럼 분리

- metric_col을 `_`로 분리하여 J1~J7 파트로 분해
- 숫자_숫자 패턴으로 REPORT NO. 결정 → `report_no_mapping` 딕셔너리 참고

### 6. non-channel 파일: dummy 0행 삽입

- pre-scan 기준 마스터 site_code에서 해당 파일에 없는 site에 dummy 0행 삽입
- US 파일 → `_us_sites` 기준, 글로벌 파일 → `_global_sites` 기준
- `_stacked_separate.csv`로 개별 저장

### 7. channel 파일: 추가 처리

#### 7-1. US 채널명 → 글로벌 채널명 매핑
- US는 AA Report Suite가 달라 채널명이 다름 → `us_mapping` 딕셔너리로 변환
- 예: `"Social (Paid)"` → `"Social Media Campaigns"`, `"PLA"` → `"Pmax"` 등

#### 7-2. mc_needs_ch / mc_has_ch 구분
- **mc_needs_ch**: metric_col이 `_`로 끝나는 컬럼 → 채널명은 value(row) 기준으로 붙임
  - 예: `7_1_all_2026_scom_web_revenue_null_` + value="Paid Search" → `7_1_..._null_Paid Search`
- **mc_has_ch**: metric_col에 채널명이 내장된 컬럼 → value(row) 그대로 유지, metric_col 변경 없음
  - 예: `7_1_all_2026_scom_prior_web_revenue_null_Social Media Campaigns` → 그대로 KEY가 됨

> ⚠️ **tb_column_name_mapping.csv 작성 주의**
> - 채널 파일의 일반 revenue/entry/order 컬럼은 반드시 trailing `_`로 끝나야 함 (mc_needs_ch)
> - 특정 채널만을 나타내는 전용 컬럼만 채널명 내장 형식으로 작성 (mc_has_ch)
> - 예: `us_26_ny_7_1_order_by_channel_scom_prior`의 일반 revenue 컬럼은
>   `7_1_all_2026_scom_prior_web_revenue_null_` (trailing `_`) 로 매핑해야 함

#### 7-3. dummy 0행 삽입 (채널 × site × metric_col 크로스곱)
- mc_needs_ch: `site × channel × metric_col` 크로스곱 기준
  - 채널 마스터: US/글로벌 모두 `global_paid_mapping` 전체 키 기준 (US도 글로벌 채널 전체에 대해 dummy 생성)
- mc_has_ch: `site × metric_col` 크로스곱 (value 차원 없음)
  - 더미 행의 value는 metric_col에서 `_null_(.+)` 추출

#### 7-4. PAID/NONPAID 부여
- mc_needs_ch 행: `value`(채널명) 기준으로 `global_paid_mapping` 조회
- mc_has_ch 행: metric_col에 내장된 채널명 기준으로 조회 (원본 row 채널과 무관)
  - 동일 KEY 내 PAID/NONPAID 일관성 보장

### 8. union 생성

- `all_frames` 합산 → `union_{YYYYMMDD}_{HHMMSS}.csv`
- non-US에 있고 US에 없는 **모든** metric_col에 US dummy 0행 자동 삽입 (채널/비채널 무관)
- PAID_NONPAID NaN → `-` fillna

---

## 출력 컬럼 구조 (finalize_df 기준)

```
TIER, SUBS, COUNTRY, SITE CODE, REPORT NO., DIVISION, DATE, DEVICE TYPE, TYPE, LOGIN/NON,
PAID/NONPAID, ITEM, VALUE, KEY, 공란1, 공란2, 공란3, 공란4, value_origin, start_date, end_date
```

- **KEY** = SITE CODE(소문자) + `_` + metric_col
- **ITEM** = value 컬럼 (채널 파일은 채널명, non-채널 파일은 metric_name)

---

## 실행 후 확인 사항

1. 셀 출력의 `✅ 완료`, `⏭️ 리포트 번호 없어서 skip`, `⚠️ 매핑 없어서 skip` 목록 확인
2. `aa_exports/union_{timestamp}.csv` 파일이 생성되었는지 확인
3. 예상 KEY 누락 여부 확인 시 → `check_41.py` 등 보조 스크립트 활용

---

## 주의사항

| 항목 | 내용 |
|------|------|
| 동일 tb_key 중복 추출 | 타임스탬프 기준 최신 파일만 사용됨. 이전 파일은 자동 무시 |
| FAILED 데이터 | 수기 보완 전 실행하면 해당 site가 dummy 0으로 들어감 |
| tb_column_name_mapping 컬럼명 오류 | `_null_Social Media Campaigns` 처럼 채널명이 내장되면 해당 site의 모든 channel row가 동일 KEY로 귀속됨 → trailing `_` 확인 필수 |
| US 채널 파일 매핑 | US `us_mapping`에 없는 채널명은 원본 값 그대로 유지됨. 단 더미 생성은 `global_paid_mapping` 기준이므로 더미 측 불일치는 없음 |
| 채널 파일 value=NaN 행 | 원본 CSV에서 채널명이 누락된 행(itemId=0 등)은 KEY 생성 불가 → stacked_separate·union에서 자동 제외, 셀 출력에서 확인 가능 |
| bestselling / nextpage / raw_multi_purchase_v41 등 | 리포트 번호(`숫자_숫자`) 없는 파일은 자동 skip. union에 포함되지 않음 |
| currency.csv 컬럼 순서 | 3번째=latest연도, 4번째=prior연도로 고정. 컬럼 추가 시 순서 변경 주의 |

---

## 보조 스크립트

### check_failed_status.py

- CSV 파일별 FAILED 건수 일괄 확인
- VRS 등 수기 보완이 필요한 사이트 식별용
- US 파일은 FAILED 여부 외 OK 데이터 행이 0개인 경우도 경고

### check_mapping_match.py

- `aa_exports/` CSV vs `tb_column_name_mapping.csv` 컬럼 매핑 검수
- 같은 tb_key 파일이 여러 개이면 최신 파일 기준

| 상태 | 의미 |
|------|------|
| ✅ 정상 | 매핑 컬럼 완전 일치 |
| ⚠️ 매핑초과(CSV부족) | 매핑에 있는 컬럼 일부가 CSV에 없음 |
| ⚠️ CSV초과(매핑누락) | CSV에 있는 value 컬럼이 매핑에 없음 |
| ⚠️ 양쪽불일치 | 매핑초과 + CSV초과 동시 발생 |
| 🔴 전혀불일치 | value_vars=[] → metric_name KeyError 원인 |
| ❌ 매핑없음 | skip 대상 |

### ipynb_json_usage_mapper.py

- JSON 파일이 6개 추출 노트북에 실제로 참조되는지 3방향 검수
- 결과: `json_usage_report/_all_check.csv`
