# json/ — JSON 유틸리티 스크립트

AA Workspace에서 추출한 JSON 파일을 관리하는 보조 스크립트 모음.  
메인 워크플로우에서는 **STEP 2 (JSON Preparation)** 단계에 해당합니다.

---

## 스크립트 목록

| 스크립트 | 실행 타이밍 | 역할 |
|---|---|---|
| `copy_prior_json.py` | STEP 2-2 초반 | prior JSON → non-prior 초안 복사 |
| `copy_last_campaign_json.py` | STEP 2-2 후반 | current JSON → last year 복사 |
| `empty_json_maker_by_input_tb_name.py` | STEP 2-3 | 빈 JSON 플레이스홀더 일괄 생성 |
| `mark_empty_json.py` | STEP 2-5 | 비어 있는 JSON에 `-EMPTY` 접미사 부여 |
| `rename_empty.py` | 수시 (롤백용) | `-EMPTY` 접미사 일괄 제거 |
| `json_segment_checker.py` | STEP 2-6 | 세그먼트 구조 검수 → CSV 리포트 출력 |
| `insert_segment.py` | 수시 | 모든 서브폴더 JSON의 `"type": "dateRange"` 엔트리 앞에 segment 엔트리 삽입 (중복 방지 포함) |

---

## 스크립트별 상세

### `copy_prior_json.py`

`main_prior/`의 `*_prior.json`을 `main/`으로 복사.  
prior와 non-prior 구조가 동일한 테이블의 작업 초안을 빠르게 생성하는 용도.  
US 버전은 `us_main_prior/` → `us_main/`으로 동일하게 복사.  
`_prior` 파일명에서 suffix를 제거한 이름으로 저장됩니다.

### `copy_last_campaign_json.py`

`main/`의 current 캠페인 JSON을 `last_main/`에 `last_` prefix를 붙여 복사.  
US는 `us_main/` → `last_us_main/`으로 동일하게 처리.

> **주의:** 스크립트 상단 `FROM_YEAR` 변수가 연도를 결정합니다. 연도 전환 시 먼저 수정 필요.  
> 복사 후, 캠페인 종속 세그(`_cmp_`, `campaign`, `bestselling` 등)는 last year용 세그 ID로 수동 교체 필요.

### `empty_json_maker_by_input_tb_name.py`

스크립트 내부에 정의된 약 80개 JSON 파일명 목록을 기준으로, 존재하지 않는 파일만 `{}` 내용으로 생성.  
파일명 prefix에 따라 자동으로 서브폴더를 결정합니다:

| prefix / suffix 패턴 | 대상 폴더 |
|---|---|
| `last_us_` | `last_us_main/` |
| `us_` | `us_main/` |
| `last_` | `last_main/` |
| `*_prior` | `main_prior/` 또는 `us_main_prior/` |
| 기본 | `main/` |

실행 후 이미 있는 파일, 새로 생성된 파일, 목록에 없는 잉여 파일 수를 요약 출력합니다.

### `mark_empty_json.py`

6개 서브폴더(`main`, `main_prior`, `us_main`, `us_main_prior`, `last_main`, `last_us_main`) 전체를 순회하며,  
내용이 없거나 `{}` / `[]`인 JSON 파일에 `-EMPTY` 접미사를 붙여 이름 변경.

```
예) 3_3_homepage_kv_gnb_to_cmp.json  →  3_3_homepage_kv_gnb_to_cmp-EMPTY.json
```

최종 상태에서 `-EMPTY` 파일이 **0개**이어야 추출을 진행할 수 있습니다.

### `rename_empty.py`

`mark_empty_json.py`의 반대 동작. `-EMPTY.json` 파일명에서 `-EMPTY`를 제거해 원래 이름으로 복원.  
AA에서 payload를 다시 채워 넣은 뒤 일괄 롤백할 때 사용합니다.

### `insert_segment.py`

`json/` 하위 모든 서브폴더를 재귀 탐색해서, `"type": "dateRange",` 엔트리 앞에 지정한 segmentId의 `"type": "segment"` 엔트리를 삽입합니다.

- 이미 해당 segmentId가 파일 본문에 있으면 중복 처리 방지를 위해 건너뜀
- 파일명에 `test` 포함된 것은 기본 제외 (`--include-test`로 포함 가능)
- `--dry-run`으로 수정 전 대상 미리 확인
- 실제 수정 직전 y/N 확인 프롬프트

스크립트 상단 `SEGMENT_ID` 상수를 실제 값(`s + 9자리숫자 + _ + 24자리 hex` 형태)으로 교체한 뒤 실행.

### `json_segment_checker.py`

세 가지 검수를 수행하고 결과를 `json_segment_report/`에 CSV로 저장합니다.

| 검수 항목 | 비교 대상 | 결과 파일 |
|---|---|---|
| Prior 일치성 | `main/X.json` ↔ `main_prior/X_prior.json` (US 동일) | `_prior_check.csv` |
| 업데이트 여부 | `main/` ↔ `last_main/` (SHOULD_SAME / SHOULD_DIFFER) | `_main_vs_last_diff.csv` |
| 파일명-panelName 정합성 | 파일명 키워드 vs JSON 내부 `panelName` | `_filename_panel_check.csv` |

검수 기준:
- 세그먼트 ID와 메트릭 수가 prior와 일치해야 정상
- `SHOULD_SAME` 테이블은 last_main과 변경 없어야 함, `SHOULD_DIFFER`는 변경이 있어야 함
- 파일명에 `cmp` / `scom` / `prior` 등의 키워드가 있으면 `panelName`도 같은 키워드를 포함해야 함

---

## 서브폴더 구조

```
json/
├── main/           # This Year Campaign
├── main_prior/     # This Year Prior
├── us_main/        # This Year US Campaign
├── us_main_prior/  # This Year US Prior
├── last_main/      # Last Year Campaign
└── last_us_main/   # Last Year US Campaign
```
