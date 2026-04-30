# data-preprocessing
<!-- 2026-04-30  Jonghyun Park w/ Claude -->

preprocessing data — AA(Adobe Analytics) 추출·정제, 캠페인 매핑, 일정 자동화 스크립트 모음.

> 각 모듈 상세는 해당 폴더의 README를 참고하세요.  
> - AA Export 워크플로우: [`AA_Exporter_260304/README.md`](AA_Exporter_260304/README.md)  
> - 일정 자동화: [`260324_schedule/README.md`](260324_schedule/README.md)  
> - 일정 파일 정제 함수(Excel): [`260427_schedule_refine/README.md`](260427_schedule_refine/README.md)

## 폴더 구조

```
data-preprocessing/
├── AA_Exporter_260304/                ← AA 추출·후처리 메인 워크플로우
│   ├── date/                          ← site_code CSV (더미 데이터, 하단 참고)
│   ├── ref/                           ← 마스터 CSV (currency, app_O_X, tb_column_name_mapping)
│   ├── json/                          ← AA Workspace JSON + 유틸리티 스크립트
│   ├── json_segment_report/           ← 세그먼트 패널 점검 결과 (로컬 전용)
│   ├── json_usage_report/             ← JSON 사용 여부 점검 결과 (로컬 전용)
│   ├── launch/                        ← 추출 노트북 6종 + 후처리 스크립트
│   │   ├── best_selling_product/      ← Best Selling 정제 (v1, v1.1, v1.2, v2)
│   │   ├── nextpage/                  ← nextpage 정제 + 원본 SQL
│   │   ├── multipurchase/             ← multipurchase 정제 + 원본 SQL (this year/prior/last year)
│   │   ├── utils/                     ← 공통 유틸 (aa_exporter, site_registry)
│   │   └── old/                       ← 구버전 정제 노트북 아카이브
│   ├── generate_period_notebooks_v3.py
│   ├── ipynb_json_usage_mapper.py
│   ├── check_failed_status.py
│   ├── check_mapping_match_260313.py
│   ├── cleanup_old_exports.py
│   └── metric_value_with_dummy.py
├── 260324_schedule/
│   ├── update_schedule.py             ← 고객 일정 xlsx → Auto 정제 파일 업데이트
│   └── check_mail_attachment.py       ← Outlook 신규 첨부 xlsx 감지·저장
├── 260427_schedule_refine/            ← 캠페인 일정 원본 xlsx 정제용 Excel 함수 모음
├── campaign_mapping_key_separator_260109v3.py
├── campaign_main_value_mapping_251224_add_date.py
└── campaign_default_value_splitter_251217.py
```

---

## **AA_Exporter_260304**

* 보안을 위해 추출된 `value#` 칼럼들의 숫자값들은 모두 dummy화 했습니다.
* `date/` 폴더의 CSV 파일(`site_code.csv`, `us_site_code.csv` 등)도 더미 데이터입니다.

### 추출 노트북 (`launch/`)

기간별로 6개 노트북을 사용. `generate_period_notebooks_v3.py`로 자동 생성됩니다.

| 노트북 | 기간 |
|---|---|
| `campaign_period.ipynb` | This Year Campaign |
| `prior_period.ipynb` | This Year Prior |
| `last_campaign_period.ipynb` | Last Year Campaign |
| `US_campaign_period.ipynb` | This Year US Campaign |
| `US_prior_period.ipynb` | This Year US Prior |
| `US_last_campaign_period.ipynb` | Last Year US Campaign |

US는 별도 Report Suite를 쓰므로 non-US와 분리해서 추출합니다.

### 보조작업 — FAILED 점검

`check_failed_status.py`  
어떤 csv 파일에 몇 건의 `status=FAILED`가 있는지 일괄 확인. UK 등 VRS site에서 추출 누락 시 수기 보완용.

### 추출 후 작업 (후처리)

기준 노트북: `launch/RESHAPE_main_raw_v4.2.ipynb` (가이드: `RESHAPE_main_raw_v4.2.md`)

처리 흐름:
1. AA 추출 raw CSV에서 `value#` → 실제 컬럼명 rename, `wide → long` 변환
2. `ref/currency.csv` 환율 적용 (revenue 컬럼, End_Date 연도 기준)
3. `ref/app_O_X.csv` 기준 App 없는 site의 app/android/ios 행 0처리
4. 파일 내 실제 site 기준 dummy 0행 삽입 (FIX-9)
5. US 채널 매핑 + PAID/NONPAID 부여
6. union 생성 → `aa_exports/union_{YYYYMMDD_HHMMSS}.csv`
7. union 후 누락 조합 보완 (FIX-10), 추출 0행 fallback dummy (FIX-11)

> 구버전 정제 노트북(`stack_n_currency_n_chnl_n_seaprate_*.ipynb`)은 `launch/old/`로 아카이브.

### 보조작업 — JSON 참조 검수

`ipynb_json_usage_mapper.py`  
JSON 파일을 추출 노트북에서 누락 없이 다 사용했는지 3축(JSON 폴더 / 매핑 CSV / 노트북 코드)으로 검수. 결과는 `json_usage_report/`에 저장됩니다.

---

## **260324_schedule**

캠페인 법인별 일정 파일을 자동 정제 Excel에 반영하고, Outlook 수신함에서 첨부파일을 감지해 저장하는 자동화 스크립트 모음.

### 주요 스크립트

| 파일 | 역할 |
|---|---|
| `update_schedule.py` | 최신 고객 일정 xlsx → Auto 정제 파일 업데이트 |
| `check_mail_attachment.py` | Outlook 수신함 → 신규 첨부 xlsx 로컬 저장 |

### 작업 스케줄러 자동 실행

`pythonw.exe`로 직접 호출하는 방식과 bat/vbs 래퍼 방식 두 가지를 지원.  
등록 명령어, 배터리 모드 허용, 트러블슈팅 등 상세는 `260324_schedule/README.md` 참고.
