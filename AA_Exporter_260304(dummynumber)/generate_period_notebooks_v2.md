# generate_period_notebooks_v2.py

`json/` 서브폴더의 JSON 파일을 자동 감지하여 **6개 기간별 Jupyter Notebook** 을 `launch/` 폴더에 생성하는 스크립트.

---

## 실행 방법

```bash
python generate_period_notebooks_v2.py
```

---

## 생성되는 노트북 파일 (`launch/` 폴더)

| 파일명 | 대상 JSON 서브폴더 | site CSV |
|--------|-------------------|---------|
| `campaign_period.ipynb` | `json/main/` | `date/site_code.csv` |
| `last_campaign_period.ipynb` | `json/last_main/` | `date/last_site_code.csv` |
| `prior_period.ipynb` | `json/main_prior/` | `date/site_code_prior.csv` |
| `US_campaign_period.ipynb` | `json/us_main/` | `date/us_site_code.csv` |
| `US_last_campaign_period.ipynb` | `json/last_us_main/` | `date/us_last_site_code.csv` |
| `US_prior_period.ipynb` | `json/us_main_prior/` | `date/us_site_code_prior.csv` |

출력 파일명은 코드 상단 `OUT_NAMES` 딕셔너리에서 변경 가능.

---

## 기간별 설정 (PERIOD_CONFIG)

각 기간마다 아래 3가지를 설정:

| 항목 | 설명 |
|------|------|
| `json_subdir` | JSON 소스 서브폴더 (`json/{subdir}/`) |
| `data_csv` | site_code CSV 파일명 (`date/{file}`) |
| `base_default` | 테이블 컬럼 형식 기본값 |

> `raw_multi_purchase`, `bestselling`, `nextpage`, `cc_*` 파일은 `base=""` 로 처리.

---

## 생성되는 노트북 구조

각 `.ipynb` 는 JSON 파일 1개당 아래 3개 셀 묶음으로 구성:

```
[섹션 헤더 셀]   ← 섹션이 바뀔 때만 삽입
[서브 제목 셀]   ← 파일명 기반 제목
[데이터 실행 셀] ← AAExporter 실행 코드
```

### 데이터 실행 셀 예시

```python
from utils.aa_exporter import ExportConfig, AAExporter

base = "2_1_all_2026_scom"
json_file_name = "1_1_scom_da_traffic_web.json"
json_path = Path.cwd().parent / "json" / "main" / json_file_name

cfg = ExportConfig(
    data_csv=str(Path.cwd().parent / "date" / "site_code.csv"),
    json_file=str(json_path),
    out_dir=str(Path.cwd().parent / "aa_exports"),
    out_prefix=json_path.stem,
    limit=50000,
    parallel_sites=True,
    max_workers=6,
    log_each_page=False,
)

out_path = AAExporter(cfg).run()
df = pd.read_csv(out_path, encoding="utf-8-sig")
df.head()
```

> 노트북은 `launch/` 폴더에서 실행되므로 JSON/site CSV 경로는 `Path.cwd().parent` 기준.

---

## 섹션 구분

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
