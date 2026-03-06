"""
generate_period_notebooks.py
─────────────────────────────────────────────────────────────────────
json/ 폴더의 JSON 파일을 자동 감지하여 6개 기간 Jupyter notebook을 생성합니다.

  [NY]
  campaign         → 26_ny_*.json  (_prior 제외)
  last_campaign    → 25_ny_*.json
  prior            → 26_ny_*_prior.json

  [US]
  us_campaign      → us_26_*.json  (_prior 제외)
  us_last_campaign → us_25_*.json
  us_prior         → us_26_*_prior.json

▶ 출력 파일명은 아래 OUT_NAMES 딕셔너리에서 자유롭게 수정하세요.
"""

import json
import re
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).parent
JSON_DIR  = BASE_DIR / "json"

# ── 출력 파일명 설정 (원하는 이름으로 변경) ──────────────────────────────
OUT_NAMES = {
    # NY
    "campaign":         "01.26ny_campaign_period.ipynb",
    "last_campaign":    "02.25ny_last_campaign_period.ipynb",
    "prior":            "03.26ny_prior_period.ipynb",
    # US
    "us_campaign":      "04.us_26ny_campaign_period.ipynb",
    "us_last_campaign": "05.us_25ny_last_campaign_period.ipynb",
    "us_prior":         "06.us_26ny_prior_period.ipynb",
}

# ── 기간별 설정 ───────────────────────────────────────────────────────────
PERIOD_CONFIG = {
    # ── NY ──────────────────────────────────────────────────────────────
    "campaign": {
        "data_csv":     "26_ny_site_code.csv",
        "base_default": "2_1_all_2026_scom",
        "json_filter":  lambda f: f.startswith("26_") and "_prior" not in f,
    },
    "last_campaign": {
        "data_csv":     "25_bl_site_code.csv",
        "base_default": "2_1_all_2025_scom",
        "json_filter":  lambda f: f.startswith("25_"),
    },
    "prior": {
        "data_csv":     "26_ny_site_code_prior.csv",
        "base_default": "2_1_all_2026_scom",
        "json_filter":  lambda f: f.startswith("26_") and f.endswith("_prior.json"),
    },
    # ── US ──────────────────────────────────────────────────────────────
    "us_campaign": {
        "data_csv":     "us_26_ny_site_code.csv",       # US용 csv로 교체 가능
        "base_default": "2_1_all_2026_scom",
        "json_filter":  lambda f: f.startswith("us_26_") and "_prior" not in f,
    },
    "us_last_campaign": {
        "data_csv":     "us_25_bl_site_code.csv",       # US용 csv로 교체 가능
        "base_default": "2_1_all_2025_scom",
        "json_filter":  lambda f: f.startswith("us_25_"),
    },
    "us_prior": {
        "data_csv":     "us_26_ny_site_code_prior.csv", # US용 csv로 교체 가능
        "base_default": "2_1_all_2026_scom",
        "json_filter":  lambda f: f.startswith("us_26_") and f.endswith("_prior.json"),
    },
}

# base="" 를 사용하는 파일 키워드 (테이블 컬럼 형식 불필요)
BASE_EMPTY_KEYWORDS = [
    "raw_multi_purchase", "bestselling", "nextpage",
    "cc_order", "cc_revenue", "cc_visit",
]

# 섹션 번호 → 섹션 헤더 (## 수준)
SECTION_HEADERS = {
    "1":  "## **1_1~2. S.com Traffic by Division**",
    "2":  "## **2_1~4. Basic Traffic**",
    "3":  "## **3. Traffic by Channel**",
    "4":  "## **4. Order CVR**",
    "5":  "## **5. Campaign Order CVR**",
    "6":  "## **6. S.com Cross Sell Order**",
    "7":  "## **7. Order Conversion/Traffic by Channel**",
    "8":  "## **Multi Purchase**",
    "9":  "## **Best Selling Product**",
    "10": "## **Next Page**",
    "11": "## **CC (Contents)**",
    "99": "## **기타**",
}

# ─────────────────────────────────────────────────────────────────────────────


def uid() -> str:
    return str(uuid.uuid4())[:8]


def strip_prefix(fname: str) -> str:
    """26_ny_, 25_ny_, us_26_ny_ 등 앞 접두어 제거"""
    return re.sub(r"^(?:us_)?\d+_[a-z]+_", "", fname)


def get_section_key(fname: str) -> str:
    """파일명에서 섹션 번호 문자열 반환 (1, 2, ..., 99)"""
    clean = strip_prefix(fname).lower()
    m = re.match(r"^(\d+)[_.]", clean)
    if m:
        return m.group(1)
    if "raw_multi_purchase" in clean:  return "8"
    if "bestselling"        in clean:  return "9"
    if "nextpage"           in clean:  return "10"
    if clean.startswith("cc_"):        return "11"
    return "99"


def sort_key(fname: str):
    """테이블 번호 기준 정렬 키"""
    clean = strip_prefix(fname).replace(".json", "").replace("-EMPTY", "")
    m = re.match(r"^(\d+)_(\d+)_(.+)$", clean)
    if m:
        return (int(m.group(1)), int(m.group(2)), clean)
    m = re.match(r"^(\d+)_(.+)$", clean)
    if m:
        return (int(m.group(1)), 0, clean)
    # 숫자 접두어 없는 파일 (bestselling 등)
    for kw, order in [("raw_multi_purchase", 8), ("bestselling", 9),
                      ("nextpage", 10), ("cc_", 11)]:
        if kw in clean.lower():
            return (order, 0, clean)
    return (99, 0, clean)


def make_subheading(fname: str) -> str:
    """파일명 → #### 수준 제목 문자열"""
    is_us = fname.startswith("us_")
    clean = strip_prefix(fname).replace(".json", "")
    clean = re.sub(r"-EMPTY$", "", clean)
    clean = re.sub(r"_prior$",  "", clean)
    parts = clean.split("_")
    # 앞의 테이블 번호 제거 (예: 1_1 → ['1','1','scom',...] → ['scom',...])
    while parts and re.match(r"^\d+$", parts[0]):
        parts.pop(0)
    title = " ".join(p.upper() if len(p) <= 3 else p.title() for p in parts)
    if is_us:
        title += " (US)"
    return f"#### **{title}**"


def get_base(fname: str, default_base: str) -> str:
    name = fname.lower()
    if any(kw in name for kw in BASE_EMPTY_KEYWORDS):
        return ""
    return default_base


# ── 셀 생성 헬퍼 ──────────────────────────────────────────────────────────

def code_cell(source_lines: list) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": uid(),
        "metadata": {},
        "outputs": [],
        "source": source_lines,
    }


def markdown_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "id": uid(),
        "metadata": {},
        "source": [text],
    }


def data_cell(json_fname: str, data_csv: str, base: str) -> dict:
    lines = [
        "from pathlib import Path\n",
        "import importlib\n",
        "import utils.aa_exporter_jh2\n",
        "importlib.reload(utils.aa_exporter_jh2)\n",
        "\n",
        "from utils.aa_exporter_jh2 import ExportConfig, AAExporter\n",
        "from utils.tb_columns import make_tb_columns\n",
        "import pandas as pd\n",
        "\n",
        f'base = "{base}"  # 테이블 형태 맞게 설정\n',
        "tb_cols = make_tb_columns(base)\n",
        "\n",
        f'json_file_name = "{json_fname}"\n',
        "\n",
        'json_path = Path.cwd() / "json" / json_file_name\n',
        "\n",
        "cfg = ExportConfig(\n",
        f'    data_csv="{data_csv}",\n',
        "    json_file=str(json_path),\n",
        '    out_dir="aa_exports",\n',
        "    out_prefix=json_path.stem,\n",
        "    limit=10000,\n",
        "    tb_columns=None,\n",
        "    parallel_sites=True,\n",
        "    max_workers=6,\n",
        "    log_each_page=False,\n",
        ")\n",
        "\n",
        "out_path = AAExporter(cfg).run()\n",
        'print("DONE:", out_path)\n',
        "\n",
        'df = pd.read_csv(out_path, encoding="utf-8-sig")\n',
        "df.head()",
    ]
    return code_cell(lines)


def make_notebook(cells: list) -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.9.0",
            },
        },
        "cells": cells,
    }


# ── 후처리 셀 로드 (기존 campaign 노트북에서 마지막 2셀 복사) ────────────

def load_postprocess_cells() -> list:
    """
    기존 notebook_jh5-campaign_period.ipynb 의 마지막 2셀
    (# CSV to Excel Raw Sheet Format 섹션)을 그대로 재사용합니다.
    파일이 없으면 플레이스홀더를 반환합니다.
    """
    ref_path = BASE_DIR / "notebook_jh5-campaign_period.ipynb"
    if not ref_path.exists():
        return [
            markdown_cell("# **CSV to Excel Raw Sheet Format**"),
            code_cell(["# 후처리 코드를 여기에 추가하세요.\n"]),
        ]
    with open(ref_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    # 마지막 2셀 복사 (id만 새로 발급)
    tail = nb["cells"][-2:]
    result = []
    for cell in tail:
        c = dict(cell)
        c["id"] = uid()
        if "outputs" not in c:
            c["outputs"] = []
        if "execution_count" not in c:
            c["execution_count"] = None
        result.append(c)
    return result


# ── 노트북 빌드 ───────────────────────────────────────────────────────────

def build_notebook(period_key: str) -> dict:
    cfg          = PERIOD_CONFIG[period_key]
    data_csv     = cfg["data_csv"]
    base_default = cfg["base_default"]
    json_filter  = cfg["json_filter"]

    # 해당 기간 JSON 파일 필터링 & 정렬
    json_files = sorted(
        [f.name for f in JSON_DIR.glob("*.json") if json_filter(f.name)],
        key=sort_key,
    )

    cells = []

    # 첫 번째 셀: pip 설치 주석
    cells.append(code_cell(["# !pip install tqdm"]))

    prev_section = None
    for fname in json_files:
        sec = get_section_key(fname)

        # 섹션이 바뀌면 섹션 헤더 삽입
        if sec != prev_section:
            header = SECTION_HEADERS.get(sec, f"## **Section {sec}**")
            cells.append(code_cell([header]))
            prev_section = sec

        # 서브 제목 셀
        cells.append(code_cell([make_subheading(fname)]))

        # 데이터 셀
        base = get_base(fname, base_default)
        cells.append(data_cell(fname, data_csv, base))

    # 후처리 섹션 (CSV → Excel)
    cells.extend(load_postprocess_cells())

    return make_notebook(cells)


# ── 메인 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"JSON dir: {JSON_DIR}\n")

    for period_key, out_name in OUT_NAMES.items():
        out_path = BASE_DIR / out_name
        nb = build_notebook(period_key)

        # JSON 셀 수 집계
        json_count = sum(
            1 for c in nb["cells"]
            if c.get("source") and any(".json" in l for l in c["source"])
        )

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)

        print(f"  [OK] [{period_key:13s}] {out_name}  ({json_count} JSON cells)")

    print("\nDone!")
