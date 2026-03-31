"""
generate_period_notebooks_v2.py
─────────────────────────────────────────────────────────────────────
json/ 서브폴더의 JSON 파일을 자동 감지하여 6개 기간 Jupyter notebook을
launch/ 폴더에 생성합니다.

  [NY]
  campaign         -> json/main/           site: date/site_code.csv
  last_campaign    -> json/last_main/      site: date/last_site_code.csv
  prior            -> json/main_prior/     site: date/site_code_prior.csv

  [US]
  us_campaign      -> json/us_main/        site: date/us_site_code.csv
  us_last_campaign -> json/last_us_main/   site: date/us_last_site_code.csv
  us_prior         -> json/us_main_prior/  site: date/us_site_code_prior.csv

출력 경로: launch/ 폴더 (노트북 실행 시 Path.cwd() = launch/)
"""

import json
import re
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).parent
JSON_DIR = BASE_DIR / "json"
OUT_DIR  = BASE_DIR / "launch"

OUT_NAMES = {
    "campaign":         "campaign_period.ipynb",
    "last_campaign":    "last_campaign_period.ipynb",
    "prior":            "prior_period.ipynb",
    "us_campaign":      "US_campaign_period.ipynb",
    "us_last_campaign": "US_last_campaign_period.ipynb",
    "us_prior":         "US_prior_period.ipynb",
}

PERIOD_CONFIG = {
    "campaign": {
        "json_subdir":  "main",
        "data_csv":     "site_code.csv",
        "base_default": "2_1_all_2026_scom",
    },
    "last_campaign": {
        "json_subdir":  "last_main",
        "data_csv":     "last_site_code.csv",
        "base_default": "2_1_all_2025_scom",
    },
    "prior": {
        "json_subdir":  "main_prior",
        "data_csv":     "site_code_prior.csv",
        "base_default": "2_1_all_2026_scom",
    },
    "us_campaign": {
        "json_subdir":  "us_main",
        "data_csv":     "us_site_code.csv",
        "base_default": "2_1_all_2026_scom",
    },
    "us_last_campaign": {
        "json_subdir":  "last_us_main",
        "data_csv":     "us_last_site_code.csv",
        "base_default": "2_1_all_2025_scom",
    },
    "us_prior": {
        "json_subdir":  "us_main_prior",
        "data_csv":     "us_site_code_prior.csv",
        "base_default": "2_1_all_2026_scom",
    },
}

BASE_EMPTY_KEYWORDS = [
    "raw_multi_purchase", "multi_purchase", "bestselling", "nextpage",
    "cc_order", "cc_revenue", "cc_visit",
]

SECTION_HEADERS = {
    "1":  "## **1_1~2. S.com Traffic by Division**",
    "2":  "## **2_1~4. Basic Traffic**",
    "3":  "## **3. Traffic by Channel**",
    "4":  "## **4. Order CVR**",
    "5":  "## **5. Campaign Order CVR**",
    "6":  "## **6. S.com Cross Sell Order**",
    "7":  "## **7. Order Conversion/Traffic by Channel**",
    "8":  "## **8. Campaign Page**",
    "9":  "## **Best Selling Product**",
    "10": "## **Next Page**",
    "11": "## **CC (Contents)**",
    "99": "## **기타**",
}


def uid() -> str:
    return str(uuid.uuid4())[:8]


def strip_prefix(fname: str) -> str:
    """last_us_, last_, us_ 접두어 및 _prior 접미어 제거"""
    name = re.sub(r"\.json$", "", fname)
    name = re.sub(r"^(?:last_us_|last_|us_)", "", name)
    name = re.sub(r"_prior$", "", name)
    return name


def get_section_key(fname: str) -> str:
    clean = strip_prefix(fname).lower()
    m = re.match(r"^(\d+)[_.]", clean)
    if m:
        return m.group(1)
    if "multi_purchase" in clean: return "8"
    if "bestselling"    in clean: return "9"
    if "nextpage"       in clean: return "10"
    if clean.startswith("cc_"):   return "11"
    return "99"


def sort_key(fname: str):
    clean = strip_prefix(fname)
    m = re.match(r"^(\d+)_(\d+)_(.+)$", clean)
    if m:
        return (int(m.group(1)), int(m.group(2)), clean)
    m = re.match(r"^(\d+)_(.+)$", clean)
    if m:
        return (int(m.group(1)), 0, clean)
    for kw, order in [("multi_purchase", 8), ("bestselling", 9),
                      ("nextpage", 10), ("cc_", 11)]:
        if kw in clean.lower():
            return (order, 0, clean)
    return (99, 0, clean)


def make_subheading(fname: str) -> str:
    is_us = fname.startswith("us_") or fname.startswith("last_us_")
    clean = strip_prefix(fname)
    parts = clean.split("_")
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


def data_cell(json_fname: str, data_csv: str, base: str, json_subdir: str) -> dict:
    # 노트북은 launch/ 폴더에서 실행 -> Path.cwd().parent = 260330 root
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
        f'json_path = Path.cwd().parent / "json" / "{json_subdir}" / json_file_name\n',
        f'data_csv_path = str(Path.cwd().parent / "date" / "{data_csv}")\n',
        "\n",
        "cfg = ExportConfig(\n",
        "    data_csv=data_csv_path,\n",
        "    json_file=str(json_path),\n",
        '    out_dir=str(Path.cwd().parent / "aa_exports"),\n',
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


def build_notebook(period_key: str) -> dict:
    cfg          = PERIOD_CONFIG[period_key]
    data_csv     = cfg["data_csv"]
    json_subdir  = cfg["json_subdir"]
    base_default = cfg["base_default"]

    period_json_dir = JSON_DIR / json_subdir
    json_files = sorted(
        [f.name for f in period_json_dir.glob("*.json")],
        key=sort_key,
    )

    cells = [code_cell(["# !pip install tqdm"])]

    prev_section = None
    for fname in json_files:
        sec = get_section_key(fname)
        if sec != prev_section:
            header = SECTION_HEADERS.get(sec, f"## **Section {sec}**")
            cells.append(code_cell([header]))
            prev_section = sec

        cells.append(code_cell([make_subheading(fname)]))
        base = get_base(fname, base_default)
        cells.append(data_cell(fname, data_csv, base, json_subdir))

    return make_notebook(cells)


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    print(f"JSON dir : {JSON_DIR}")
    print(f"OUT dir  : {OUT_DIR}\n")

    for period_key, out_name in OUT_NAMES.items():
        out_path = OUT_DIR / out_name
        nb = build_notebook(period_key)

        json_count = sum(
            1 for c in nb["cells"]
            if c.get("source") and any(".json" in l for l in c["source"])
        )

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)

        print(f"  [OK] [{period_key:14s}] {out_name}  ({json_count} JSON cells)")

    print("\nDone!")
