# generate_period_notebooks_v3.py 가이드
<!-- 2026-04-17  Jonghyun Park w/ Claude -->

`json/` 서브폴더의 JSON 파일을 자동 감지하여 **기간별 Jupyter Notebook** 을 `launch/` 폴더에 생성하는 스크립트.

---

## 역할

AA Exporter용 노트북(`.ipynb`)을 매번 수작업으로 만드는 대신,  
`json/` 아래 각 기간 폴더에 있는 JSON 파일 수만큼 셀을 자동 생성한다.

---

## 실행 방법

```bash
python generate_period_notebooks_v3.py
```

실행 위치: 스크립트와 같은 폴더 (`Path(__file__).parent` 기준)

### 출력 예시

```
JSON dir : ...\AA_Exporter\json
OUT dir  : ...\AA_Exporter\launch

  [OK]   [main          ] campaign_period.ipynb  (19 cells)
  [OK]   [main_prior    ] prior_period.ipynb  (7 cells)
  [SKIP] [last_main     ] 폴더 없음 또는 json 없음
  ...

Done!
```

---

## 입력 → 출력 매핑 (PERIOD_CONFIG)

json 서브폴더가 존재하는 경우에만 생성됨. 폴더 없거나 json 없으면 SKIP.

| 생성되는 노트북 | json 서브폴더 | site CSV |
|---|---|---|
| `launch/campaign_period.ipynb` | `json/main/` | `date/site_code.csv` |
| `launch/prior_period.ipynb` | `json/main_prior/` | `date/site_code_prior.csv` |
| `launch/last_campaign_period.ipynb` | `json/last_main/` | `date/last_site_code.csv` |
| `launch/US_campaign_period.ipynb` | `json/us_main/` | `date/us_site_code.csv` |
| `launch/US_prior_period.ipynb` | `json/us_main_prior/` | `date/us_site_code_prior.csv` |
| `launch/US_last_campaign_period.ipynb` | `json/last_us_main/` | `date/us_last_site_code.csv` |

각 기간 설정은 `PERIOD_CONFIG` 리스트에서 관리:

| 항목 | 설명 |
|---|---|
| `json_subdir` | JSON 소스 서브폴더 (`json/{subdir}/`) |
| `data_csv` | site_code CSV 파일명 (`date/{file}`) |
| `out_name` | 출력 노트북 파일명 |

---

## 처리 흐름

```
json/{subdir}/*.json
    │
    ├─ 파일명에 'test' 포함된 json 제외
    ├─ 파일명 앞 숫자(N_M_) 기준 정렬 (sort_key)
    │
    └─ JSON 파일 1개당 code_cell 1개 생성
          ↓
    make_notebook() → launch/{out_name}.ipynb 저장
```

---

## 생성되는 셀 형태

`launch/sample_campaign_for_generate.ipynb` 템플릿 기준. JSON 파일 1개당 셀 1개 생성.

```python
from pathlib import Path
import importlib
import utils.aa_exporter
importlib.reload(utils.aa_exporter)

from utils.aa_exporter import ExportConfig, AAExporter
import pandas as pd

json_file_name = "1_1_basic_traffic_cmp.json"

json_path = Path.cwd().parent / "json" / "main" / json_file_name

cfg = ExportConfig(
    data_csv=str(Path.cwd().parent / "date" / "site_code.csv"),
    json_file=str(json_path),
    out_dir=str(Path.cwd().parent / "aa_exports"),
    out_prefix=json_path.stem,
    limit=10000,          # 요청 횟수
    tb_columns=None,
    parallel_sites=True,  # 국가(site) 단위 병렬
    max_workers=6,        #  5~8 추천
    log_each_page=False,  # False로 바꾸면 속도 높아짐
)

out_path = AAExporter(cfg).run()
print("DONE:", out_path)

# 생성된 CSV 바로 불러오기
df = pd.read_csv(out_path, encoding="utf-8-sig")
df.head()
```

> 노트북은 `launch/` 폴더에서 실행되므로 JSON/site CSV 경로는 `Path.cwd().parent` 기준.

---

## 주요 함수 요약

| 함수 | 역할 |
|---|---|
| `sort_key(fname)` | 파일명 앞 숫자(`N_M_`) 기준 정렬 키 생성 |
| `code_cell(source_lines)` | Jupyter code cell dict 생성 |
| `make_notebook(cells)` | 노트북 전체 dict 생성 |
| `data_cell(json_fname, data_csv, json_subdir)` | AAExporter 실행 코드 셀 생성 |
| `build_notebook(cfg)` | 기간 설정 받아 노트북 dict 생성, 폴더 없으면 `None` 반환 |

### 파일명 정렬 기준 (`sort_key`)

파일명 앞 `N_M_` 숫자 패턴 기준 정렬 → 노트북 내 셀 순서가 리포트 번호 순으로 유지됨.

| 패턴 | 예시 | 정렬키 |
|---|---|---|
| `N_M_*` | `3_1_channel_external_cmp.json` | `(3, 1, ...)` |
| `N_*` | `1_basic_traffic.json` | `(1, 0, ...)` |
| 기타 | `misc.json` | `(99, 0, ...)` |

---

## v2 → v3 변경사항 (2026-04-09)

| 항목 | v2 | v3 |
|---|---|---|
| 셀 템플릿 | `aa_exporter_jh2`, `base`/`tb_cols` 포함 | `aa_exporter`, `tb_columns=None` 고정 |
| 노트북 생성 조건 | 항상 6개 생성 | 폴더 존재 여부로 자동 결정 |
| test json 제외 | 없음 | 파일명에 `test` 포함 시 제외 |
| 섹션 헤더 셀 | 섹션마다 code_cell로 삽입 | 제거 |
| 서브 제목 셀 | json마다 `#### **제목**` 셀 삽입 | 제거 |
| 제거된 코드 | — | `SECTION_HEADERS`, `BASE_EMPTY_KEYWORDS`, `make_subheading`, `markdown_cell`, `strip_prefix` |

---

## 폴더 구조

```
AA_Exporter/
├── generate_period_notebooks_v3.py   ← 이 스크립트
├── json/
│   ├── main/            (campaign)
│   ├── main_prior/      (prior)
│   ├── last_main/       (last campaign, 있을 때만)
│   ├── us_main/         (US campaign, 있을 때만)
│   ├── us_main_prior/   (US prior, 있을 때만)
│   └── last_us_main/    (US last, 있을 때만)
├── date/
│   ├── site_code.csv
│   ├── site_code_prior.csv
│   ├── last_site_code.csv
│   ├── us_site_code.csv
│   ├── us_site_code_prior.csv
│   └── us_last_site_code.csv
└── launch/
    ├── campaign_period.ipynb      ← 생성됨
    ├── prior_period.ipynb         ← 생성됨
    └── ...
```

---

## 주의사항

| 항목 | 내용 |
|---|---|
| 기존 노트북 덮어쓰기 | 동일 파일명이 있으면 경고 없이 덮어씀 |
| `test` json | 파일명에 `test`(대소문자 무관) 포함되면 자동 제외 |
| 실행 경로 | `Path(__file__).parent` 기준이므로 py 파일 위치에서 실행 |
