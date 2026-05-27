# data-preprocessing  
<sub>2026-05-27  Jonghyun Park w/ Claude</sub>  

AA(Adobe Analytics) 추출·정제, 캠페인 매핑, 일정 자동화 스크립트 모음.

> 각 모듈 상세는 해당 폴더의 README를 참고하세요.  
> - AA Export 워크플로우: [`AA_Exporter_260304/README.md`](AA_Exporter_260304/README.md)  
> - 일정 자동화: [`260324_schedule/README.md`](260324_schedule/README.md)

## 요구사항

```bash
pip install pandas requests tqdm aanalytics2 openpyxl pywin32
```

- Python 3.10+
- Windows (일정 자동화 모듈의 Outlook COM 연동)
- Jupyter (노트북 실행/생성)

## 폴더 구조

```
data-preprocessing/
├── AA_Exporter_260304/                ← AA 추출·후처리 메인 워크플로우
│   ├── date/                          ← site_code CSV (더미 데이터)
│   ├── ref/                           ← 마스터 CSV + generate_column v2.0
│   ├── json/                          ← AA Workspace JSON + 유틸리티 스크립트
│   ├── launch/                        ← 추출 노트북 6종 + 후처리 스크립트
│   │   ├── RESHAPE_main_raw_v4.3.*    ← ★최신 후처리 (ipynb + md)
│   │   ├── best_selling_product/      ← Best Selling 정제 (v1.2, v2, modelcode v1.2.1)
│   │   ├── nextpage/                  ← nextpage 정제 + 원본 SQL
│   │   ├── multipurchase/             ← multipurchase 정제 + 원본 SQL
│   │   ├── utils/                     ← 공통 유틸 (aa_exporter, site_registry)
│   │   └── old/                       ← 구버전 (v4.1, v4.1.1, v4.2 등)
│   ├── generate_period_notebooks_v3.py
│   └── ...
├── 260324_schedule/
│   ├── update_schedule.py             ← 고객 일정 xlsx → Auto 정제 파일 업데이트
│   └── check_mail_attachment.py       ← Outlook 신규 첨부 xlsx 감지·저장
├── campaign_mapping_key_separator_260109v3.py
├── campaign_main_value_mapping_251224_add_date.py
└── campaign_default_value_splitter_251217.py
```

---

## AA_Exporter_260304

* `value#` 칼럼들의 숫자값은 모두 dummy화 되어 있습니다.
* `date/` 폴더의 CSV 파일도 더미 데이터입니다.

### 추출 노트북 (`launch/`)

`generate_period_notebooks_v3.py`로 기간별 6개 노트북 자동 생성:

| 노트북 | 기간 |
|---|---|
| `campaign_period.ipynb` | This Year Campaign |
| `prior_period.ipynb` | This Year Prior |
| `last_campaign_period.ipynb` | Last Year Campaign |
| `US_campaign_period.ipynb` | This Year US Campaign |
| `US_prior_period.ipynb` | This Year US Prior |
| `US_last_campaign_period.ipynb` | Last Year US Campaign |

### 후처리 — `RESHAPE_main_raw_v4.3` ★최신

기준: `launch/RESHAPE_main_raw_v4.3.ipynb` (가이드: `RESHAPE_main_raw_v4.3.md`)

처리 흐름:
1. AA 추출 raw CSV에서 `value#` → 실제 컬럼명 rename, wide → long 변환
2. `ref/currency.csv` 환율 적용
3. `ref/app_O_X.csv` 기준 App 없는 site app/android/ios 행 0처리
4. 파일 내 실제 site 기준 dummy 0행 삽입
5. US 채널 매핑 + PAID/NONPAID 부여
6. union 생성 → `aa_exports/union_{ts}.csv`
7. 누락 조합 보완, 추출 0행 fallback dummy

### 보조작업

| 도구 | 설명 |
|---|---|
| `check_failed_status.py` | csv 내 `status=FAILED` 건수 일괄 확인 |
| `ipynb_json_usage_mapper.py` | JSON ↔ 노트북 참조 3축 검수 |
| `cleanup_old_exports.py` | 오래된 추출 파일 정리 |

---

## 260324_schedule

캠페인 법인별 일정 파일을 자동 정제하고, Outlook에서 첨부파일을 감지·저장하는 자동화.

| 파일 | 역할 |
|---|---|
| `update_schedule.py` | 최신 고객 일정 xlsx → Auto 정제 파일 업데이트 |
| `check_mail_attachment.py` | Outlook 수신함 → 신규 첨부 xlsx 로컬 저장 |

상세: `260324_schedule/README.md`

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-27 | 구버전 `old/` 이동, README 최신화 (v4.3 기준) |
| 2026-05-08 | launch/utils 추가 (aa_exporter, site_registry) |
| 2026-04-28 | best_selling v1.2, multipurchase/nextpage RESHAPE 추가 |
| 2026-04-15 | generate_period_notebooks v3 |
| 2026-03-12 | 초기 구성 — AA_Exporter, 260324_schedule, campaign 매핑 |

> 구버전: `launch/old/`, `best_selling_product/old/`, `ref/old/` 에 보존.

---

## License

MIT
