# generate_period_notebooks_v3.py

`json/` 서브폴더의 JSON 파일을 자동 감지하여 **기간별 Jupyter Notebook** 을 `launch/` 폴더에 생성하는 스크립트.

2026-04-09  Jonghyun Park w/ Claude

---

## 실행 방법

```bash
python generate_period_notebooks_v3.py
```

---

## 생성되는 노트북 파일 (`launch/` 폴더)

json 서브폴더가 존재하는 경우에만 생성됨. 폴더 없으면 SKIP.

| 파일명 | 대상 JSON 서브폴더 | site CSV |
|--------|-------------------|---------|
| `campaign_period.ipynb` | `json/main/` | `date/site_code.csv` |
| `prior_period.ipynb` | `json/main_prior/` | `date/site_code_prior.csv` |
| `last_campaign_period.ipynb` | `json/last_main/` | `date/last_site_code.csv` |
| `US_campaign_period.ipynb` | `json/us_main/` | `date/us_site_code.csv` |
| `US_prior_period.ipynb` | `json/us_main_prior/` | `date/us_site_code_prior.csv` |
| `US_last_campaign_period.ipynb` | `json/last_us_main/` | `date/us_last_site_code.csv` |

---

## 기간별 설정 (PERIOD_CONFIG)

각 기간마다 아래 3가지를 설정:

| 항목 | 설명 |
|------|------|
| `json_subdir` | JSON 소스 서브폴더 (`json/{subdir}/`) |
| `data_csv` | site_code CSV 파일명 (`date/{file}`) |
| `out_name` | 출력 노트북 파일명 |

---

## 생성되는 노트북 구조

각 `.ipynb` 는 **JSON 파일 1개당 셀 1개**로 구성. 파일명에 `test` 가 포함된 json은 제외.

### 셀 예시 (launch/sample_campaign_for_generate.ipynb 기준)

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

## v2 → v3 주요 변경

| 항목 | v2 | v3 |
|------|----|----|
| 셀 템플릿 | `aa_exporter_jh2`, `base`/`tb_cols` 포함 | `aa_exporter`, `tb_columns=None` 고정 |
| 노트북 생성 조건 | 항상 6개 생성 | 폴더 존재 여부로 자동 결정 |
| test json 제외 | 없음 | 파일명에 `test` 포함 시 제외 |
| 섹션 헤더 셀 | 섹션마다 code_cell로 삽입 | 제거 |
| 서브 제목 셀 | json마다 `#### **제목**` 셀 삽입 | 제거 |

---

## 주요 함수 요약

| 함수 | 역할 |
|------|------|
| `sort_key(fname)` | 파일명 앞 숫자(`N_M_`) 기준 정렬 키 생성 |
| `code_cell(source_lines)` | Jupyter code cell dict 생성 |
| `make_notebook(cells)` | 노트북 전체 dict 생성 |
| `data_cell(json_fname, data_csv, json_subdir)` | AAExporter 실행 코드 셀 생성 |
| `build_notebook(cfg)` | 기간 설정 받아 노트북 dict 생성, 폴더 없으면 `None` 반환 |
