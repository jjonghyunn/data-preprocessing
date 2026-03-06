# generate_period_notebooks_v2.py

`json/` 폴더의 JSON 파일을 자동 감지하여 **6개 기간별 Jupyter Notebook(.ipynb)** 을 생성하는 스크립트.

---

## 실행 방법

```bash
python generate_period_notebooks_v2.py
```

실행하면 스크립트와 같은 폴더에 아래 6개 파일이 생성됩니다.

---

## 생성되는 노트북 파일

| 파일명 | 대상 JSON 패턴 |
|--------|---------------|
| `01.26ny_campaign_period.ipynb` | `26_ny_*.json` (`_prior` 제외) |
| `02.25ny_last_campaign_period.ipynb` | `25_ny_*.json` |
| `03.26ny_prior_period.ipynb` | `26_ny_*_prior.json` |
| `04.us_26ny_campaign_period.ipynb` | `us_26_*.json` (`_prior` 제외) |
| `05.us_25ny_last_campaign_period.ipynb` | `us_25_*.json` |
| `06.us_26ny_prior_period.ipynb` | `us_26_*_prior.json` |

출력 파일명은 코드 상단 `OUT_NAMES` 딕셔너리에서 변경 가능.

---

## 기간별 설정 (PERIOD_CONFIG)

각 기간마다 아래 3가지를 설정:

| 항목 | 설명 |
|------|------|
| `data_csv` | 사이트 코드 CSV 파일명 (AA Exporter 입력) |
| `base_default` | 테이블 컬럼 형식 기본값 (`make_tb_columns(base)` 에 전달) |
| `json_filter` | 해당 기간에 포함할 JSON 파일 판별 함수 |

> `raw_multi_purchase`, `bestselling`, `nextpage`, `cc_order`, `cc_revenue`, `cc_visit` 파일은 테이블 컬럼 형식이 불필요하여 `base=""` 로 처리.

---

## 생성되는 노트북 구조

각 `.ipynb` 는 JSON 파일 1개당 아래 3개 셀 묶음으로 구성:

```
[섹션 헤더 셀]      ← 섹션이 바뀔 때만 삽입 (예: ## 1_1~2. S.com Traffic)
[서브 제목 셀]      ← 파일명 기반 제목 (예: #### DA Traffic Web)
[데이터 실행 셀]    ← AAExporter 실행 코드
```

맨 앞에 `# !pip install tqdm` 셀, 맨 뒤에 CSV → Excel 후처리 셀 2개가 붙음.

### 섹션 구분

| 섹션 번호 | 내용 |
|-----------|------|
| 1 | S.com Traffic by Division |
| 2 | Basic Traffic |
| 3 | Traffic by Channel |
| 4 | Order CVR |
| 5 | Campaign Order CVR |
| 6 | S.com Cross Sell Order |
| 7 | Order Conversion/Traffic by Channel |
| 8 | Multi Purchase |
| 9 | Best Selling Product |
| 10 | Next Page |
| 11 | CC (Contents) |
| 99 | 기타 |

---

## 데이터 실행 셀 내용 (data_cell)

각 JSON 파일에 대해 아래 코드가 자동 삽입됨:

```python
from utils.aa_exporter_jh2 import ExportConfig, AAExporter
from utils.tb_columns import make_tb_columns

base = "2_1_all_2026_scom"   # 기간별 base_default 값
tb_cols = make_tb_columns(base)

json_file_name = "26_ny_xxx.json"
json_path = Path.cwd() / "json" / json_file_name

cfg = ExportConfig(
    data_csv="26_ny_site_code.csv",
    json_file=str(json_path),
    out_dir="aa_exports",
    out_prefix=json_path.stem,
    limit=10000,
    tb_columns=None,
    parallel_sites=True,
    max_workers=6,
    log_each_page=False,
)

out_path = AAExporter(cfg).run()
df = pd.read_csv(out_path, encoding="utf-8-sig")
df.head()
```

---

## 후처리 셀 (CSV → Excel)

`notebook_jh5-campaign_period.ipynb` 의 마지막 2셀을 복사해서 붙임.
해당 파일이 없으면 플레이스홀더 셀이 대신 삽입됨.

---

## 주요 함수 요약

| 함수 | 역할 |
|------|------|
| `strip_prefix(fname)` | `26_ny_`, `us_26_ny_` 등 앞 접두어 제거 |
| `get_section_key(fname)` | 파일명에서 섹션 번호 추출 |
| `sort_key(fname)` | 테이블 번호 기준 정렬 키 생성 |
| `make_subheading(fname)` | 파일명 → `#### **제목**` 형식 변환 |
| `get_base(fname, default)` | base 값 결정 (특수 키워드 파일은 `""` 반환) |
| `data_cell(...)` | AAExporter 실행 코드 셀 생성 |
| `build_notebook(period_key)` | 기간 키 받아 전체 노트북 dict 생성 |
| `load_postprocess_cells()` | 기존 노트북에서 후처리 셀 2개 로드 |
