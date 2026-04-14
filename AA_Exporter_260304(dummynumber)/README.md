# AA Export Workflow

기준 문서 업데이트일: `260414`

---

아래는 AA Export Workflow입니다. STEP 1, 2, 3은 준비 단계이고 STEP 5부터가 실제 API 데이터 추출 단계입니다.

---

## 폴더 구조

```
AA_Exporter/
├── generate_period_notebooks_v3.py   # 노트북 자동 생성
├── ipynb_json_usage_mapper.py        # JSON 참조 검수
├── check_failed_status_260313.py     # FAILED 점검
├── check_mapping_match_260313.py     # 컬럼 매핑 검수
├── metric_value_with_dummy.py        # 공유용 더미 데이터 생성
│
├── date/                             # site code CSV (기간별)
│   ├── site_code.csv                 # 26 NY campaign
│   ├── site_code_prior.csv           # 26 NY prior
│   ├── last_site_code.csv            # 25 NY last campaign
│   ├── us_site_code.csv              # 26 US campaign
│   ├── us_site_code_prior.csv        # 26 US prior
│   └── us_last_site_code.csv         # 25 US last campaign
│
├── ref/                              # 마스터 파일
│   ├── currency.csv                  # 환율 기준표
│   ├── tb_column_name_mapping_corrected.csv
│   └── app_O_X.csv                   # site별 App 유무 (O/X)
│
├── json/                             # AA Workspace JSON (기간별 서브폴더)
│   ├── main/                         # 26 NY campaign
│   ├── main_prior/                   # 26 NY prior
│   ├── us_main/                      # 26 US campaign
│   ├── us_main_prior/                # 26 US prior
│   ├── last_main/                    # 25 NY last campaign
│   ├── last_us_main/                 # 25 US last campaign
│   ├── copy_prior_json.py
│   ├── copy_last_campaign_json.py
│   ├── empty_json_maker_by_input_tb_name.py
│   ├── json_segment_checker.py
│   ├── mark_empty_json.py
│   └── rename_empty.py
│
├── launch/                           # 실행 노트북 + 정제 스크립트
│   ├── campaign_period.ipynb         # 26 NY campaign 추출
│   ├── last_campaign_period.ipynb    # 25 NY last campaign 추출
│   ├── prior_period.ipynb            # 26 NY prior 추출
│   ├── US_campaign_period.ipynb      # 26 US campaign 추출
│   ├── US_last_campaign_period.ipynb # 25 US last campaign 추출
│   ├── US_prior_period.ipynb         # 26 US prior 추출
│   ├── stack_n_currency_n_chnl_n_seaprate_260410.ipynb  # 정제/포맷팅
│   ├── stack_n_currency_n_chnl_n_seaprate_260410.md     # 정제 가이드
│   └── utils/
│       ├── aa_exporter.py            # AA API 추출 코어
│       ├── site_registry.py          # RSID / 사이트 메타
│       └── check_failed_status.py    # FAILED 점검 (노트북용)
│
├── json_segment_report/              # JSON 세그 검수 결과
├── json_usage_report/                # JSON 참조 검수 결과
└── aa_exports/                       # 추출 CSV 출력 (로컬 전용, repo 미포함)
```

---

## 권장 실행 순서

1. 마스터 CSV 최신화 (`ref/`, `date/` 폴더)
2. JSON 생성 및 세그 검수 (`json/` 폴더 내 유틸 활용)
3. `generate_period_notebooks_v2.py` 실행 → `launch/` 에 노트북 6개 생성
4. `launch/` 의 노트북 6개 실행 (3가지 기간 global/us)
5. `check_failed_status_260313.py` 실행 후 수기 보정
6. `check_mapping_match_260313.py` 실행
7. `launch/stack_n_currency_n_chnl_n_seaprate_260331.ipynb` 실행
8. `aa_exports/union_{timestamp}.csv` 최종본 확인

실제 기준 스크립트는 아래 4개입니다.

- `generate_period_notebooks_v3.py`
- `ipynb_json_usage_mapper.py`
- `check_mapping_match_260313.py`
- `launch/stack_n_currency_n_chnl_n_seaprate_260410.ipynb`

---

## STEP 1. Master Data Update

캠페인 시작 전에 아래 마스터 파일을 최신화합니다.

| 파일 | 위치 | 역할 |
|------|------|------|
| `currency.csv` | `ref/` | 환율 기준표. 3번째 컬럼=latest연도, 4번째 컬럼=prior연도 |
| `tb_column_name_mapping_corrected.csv` | `ref/` | `value1~N`을 실제 컬럼명으로 바꾸기 위한 매핑 마스터 |
| `app_O_X.csv` | `ref/` | site_code별 App 유무 (O=앱있음, X=앱없음) |
| site_code CSV 6종 | `date/` | 사이트별 기간, RSID 추출 대상, 국가 범위 관리 |

VRS나 US 경우와 같이 RS ID가 바뀌었다면 `launch/utils/site_registry.py`에서 수정 필요.

site code 계열 CSV (`date/` 폴더):

| 파일 | 대상 기간 |
|------|-----------|
| `site_code.csv` | 26 NY campaign |
| `site_code_prior.csv` | 26 NY prior |
| `last_site_code.csv` | 25 NY last campaign |
| `us_site_code.csv` | 26 US campaign |
| `us_site_code_prior.csv` | 26 US prior |
| `us_last_site_code.csv` | 25 US last campaign |

---

## STEP 2. JSON Preparation

### 2-1. AA Workspace에서 1차 JSON 추출

- 기준은 당해 캠페인 JSON입니다.
- prior 기간과 세그 구성이 겹치는 테이블은 `json/main_prior/` 에 `*_prior.json`으로 먼저 저장합니다.
- US는 별도 Report Suite를 쓰므로 NY와 분리해서 `json/us_main/`, `json/us_main_prior/` 에 저장합니다.

### 2-2. prior JSON을 기준으로 non-prior / last campaign JSON 복사

`json/copy_prior_json.py`

- `json/main_prior/`의 `*_prior.json`을 `json/main/`으로 복사합니다.
- prior와 non-prior 구조가 같은 테이블의 초안 생성용입니다.

`json/copy_last_campaign_json.py`

- `json/main/`의 `26_ny_*.json`을 `json/last_main/`에 `25_ny_*.json`으로 복사합니다.
- 스크립트 상단 `FROM_YEAR = 26`을 기준으로 동작하므로 연도 전환 시 먼저 수정해야 합니다.
- 복사 후 `_cmp_`, `campaign`, `bestselling` 같은 캠페인 종속 세그는 25년용 세그 ID로 수동 교체가 필요합니다.

### 2-3. 빈 JSON 플레이스홀더 생성

`json/empty_json_maker_by_input_tb_name.py`

- prior에서 복사할 수 없는 테이블용 빈 JSON 파일을 일괄 생성합니다.
- 생성 직후에는 내용이 비어 있으므로 이후 AA에서 payload를 채워 넣어야 합니다.

### 2-4. AA Workspace에서 2차 JSON 마무리

- 비어 있는 JSON 파일을 차례로 채워 전체 테이블을 완료합니다.

### 2-5. 미완성 JSON 표시

`json/mark_empty_json.py`

- 내용이 비어 있는 JSON에 `-EMPTY` 접미사를 부여합니다.
- 최종 상태에서 `-EMPTY` 파일이 0개가 되어야 정상입니다.
- 일괄 이름 복구가 필요하면 `json/rename_empty.py`를 사용합니다.

### 2-6. JSON 세그먼트 검수

`json/json_segment_checker.py`

결과 파일 (`json_segment_report/`):

- `_prior_check.csv`
- `_main_vs_last_diff.csv`
- `_filename_panel_check.csv`

검수 기준:

1. `json/main_prior/` vs `json/main/` - prior와 non-prior 구조 비교
2. `json/main/` vs `json/last_main/` - `SHOULD_SAME` / `SHOULD_DIFFER` 확인
3. 파일명 키워드 vs panelName 키워드 일관성

---

## STEP 3. Notebook Generation

실행 스크립트: `generate_period_notebooks_v3.py`

각 JSON 서브폴더를 자동 감지해서 `launch/` 에 아래 6개 노트북을 생성합니다.

| 노트북 | 기간 | data_csv | JSON 서브폴더 |
|--------|------|----------|--------------|
| `campaign_period.ipynb` | 26 NY campaign | `date/site_code.csv` | `json/main/` |
| `last_campaign_period.ipynb` | 25 NY last campaign | `date/last_site_code.csv` | `json/last_main/` |
| `prior_period.ipynb` | 26 NY prior | `date/site_code_prior.csv` | `json/main_prior/` |
| `US_campaign_period.ipynb` | 26 US campaign | `date/us_site_code.csv` | `json/us_main/` |
| `US_last_campaign_period.ipynb` | 25 US last campaign | `date/us_last_site_code.csv` | `json/last_us_main/` |
| `US_prior_period.ipynb` | 26 US prior | `date/us_site_code_prior.csv` | `json/us_main_prior/` |

---

## STEP 4. JSON Usage Verification

실행 스크립트: `ipynb_json_usage_mapper.py`

결과 파일 (`json_usage_report/`):

- `_all_check.csv`
- `*_json_usage.csv` (기간별)

아래 3개 축을 비교합니다.

- `json/` 서브폴더에 파일이 실제로 있는지
- `ref/tb_column_name_mapping_corrected.csv`에 매핑이 있는지
- 노트북 코드에서 실제 참조되는지

---

## STEP 5. AA Data Extraction

`launch/` 의 노트북 6개를 순서대로 실행합니다.

- 출력: `aa_exports/{tb_key}_{YYYYMMDD}_{HHMMSS}.csv`
- 병렬 추출: `parallel_sites=True`, 기본 `max_workers=6`
- 네트워크 오류 대응: 429, 5xx 계열 재시도 로직 포함

### 추출 후 FAILED 점검

`check_failed_status_260313.py`

- `aa_exports/` 루트 원본 CSV만 검사 (`union*`, `*_stacked*` 제외)
- `status=FAILED` 건수가 있는 파일만 출력
- US 파일: FAILED 외 **OK 행이 0개인 경우도 경고** (`⚠️ 추출 값 없음`)

---

## STEP 6. Column Mapping Verification

`check_mapping_match_260313.py`

결과: `aa_exports/` 내 각 CSV와 `ref/tb_column_name_mapping_corrected.csv` 매핑 일치 여부 검수

| 상태 | 의미 |
|------|------|
| ✅ `정상` | 완전 일치 |
| ⚠️ `매핑초과(api 추출된 CSV부족)` | 매핑 컬럼이 CSV보다 많음 |
| ⚠️ `CSV초과(tb_column_name매핑누락)` | CSV 컬럼이 매핑에 없음 |
| ⚠️ `양쪽불일치` | 양방향 불일치 |
| 🔴 `전혀불일치` | matched 0개 → KeyError 원인 |
| ❌ `매핑없음` | tb가 매핑 파일에 없음 |

---

## STEP 7. Post-Processing

기준 파일: `launch/stack_n_currency_n_chnl_n_seaprate_260410.ipynb`
참고 문서: `launch/stack_n_currency_n_chnl_n_seaprate_260410.md`

### 처리 순서 (260410 기준)

1. tb_key별 최신 파일 선택 (타임스탬프 기준, `_stacked` / `_long` / `union_` 제외)
2. Pre-scan: 전체 site_code 수집 (US/글로벌 분리, 중복 검증)
3. 리포트 번호(`숫자_숫자`) 없는 파일 전체 skip
4. `ref/tb_column_name_mapping_corrected.csv` 기준으로 `value1~N` → 실제 컬럼명 rename
5. wide → long 변환 및 `ref/currency.csv` 환율 적용 (revenue 컬럼, **End_Date 연도 기준**)
6. `J1~J7`, `J11(REPORT NO.)` 컬럼 분리
7. **App 없는 site 0처리**: `ref/app_O_X.csv` B열=X인 site에서 J5(DEVICE TYPE)이 `app/android/ios`인 행 → 값 0
8. **non-channel 파일**: year-split 합산 → dummy 0행 삽입 → `_stacked_separate.csv` 저장
9. **channel 파일**: US 채널명 매핑 → dummy 0행 삽입 → PAID/NONPAID 부여
10. union: 모든 non-US metric_col에 US dummy 0행 삽입 → `aa_exports/union_{timestamp}.csv`

### 최종 출력 컬럼

```
TIER, SUBS, COUNTRY, SITE CODE, REPORT NO., DIVISION, DATE, DEVICE TYPE,
TYPE, LOGIN/NON, PAID/NONPAID, ITEM, VALUE, KEY,
공란1, 공란2, 공란3, 공란4, value_origin, start_date, end_date
```

---

## 보조 스크립트

| 스크립트 | 용도 |
|----------|------|
| `check_failed_status_260313.py` | FAILED 건수 확인 + US OK 행 0개 경고 |
| `check_mapping_match_260313.py` | tb_column_name_mapping ↔ CSV 컬럼 매핑 검수 |
| `ipynb_json_usage_mapper.py` | JSON 파일이 노트북에서 실제 참조되는지 3방향 검수 |
| `metric_value_with_dummy.py` | aa_exports/ CSV의 value 숫자를 더미로 교체 (공유용) |
| `best_selling_refine_260413.py` | Best Selling 데이터 정제 (→ `best_selling_refine_notes.md` 참고) |
| `foldering_move_png_251126_26campaign_name.py` | 캠페인별 PNG 파일 폴더 분류 이동 |
