"""
generate_period_notebooks_v3.py
──────────────────────────────────────────────────────────────────
json/ 서브폴더의 JSON 파일을 자동 감지하여 Jupyter notebook을
launch/ 폴더에 생성합니다.

  campaign   -> json/main/           date/site_code.csv
  prior      -> json/main_prior/     date/site_code_prior.csv
  [아래는 폴더가 존재하는 경우에만 생성]
  last       -> json/last_main/      date/last_site_code.csv
  us         -> json/us_main/        date/us_site_code.csv
  us_prior   -> json/us_main_prior/  date/us_site_code_prior.csv
  us_last    -> json/last_us_main/   date/us_last_site_code.csv

v2 → v3 변경:
  - 셀 템플릿을 launch/sample_campaign_for_generate.ipynb 기준으로 통일
    (aa_exporter, tb_columns=None, 인라인 주석 포함)
  - json 서브폴더 존재 여부로 노트북 생성 여부 자동 결정
  - 파일명에 'test' 포함된 json 제외
  - 섹션 헤더 셀 제거 (code_cell로 넣어봤자 문자열 출력에 불과, 불필요)
  - SECTION_HEADERS / BASE_EMPTY_KEYWORDS / make_subheading /
    markdown_cell / strip_prefix 제거

2026-04-09  Jonghyun Park w/ Claude
"""

import json
import re
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).parent
JSON_DIR  = BASE_DIR / "json"
OUT_DIR   = BASE_DIR / "launch"

# 처리 순서 및 각 기간별 설정
PERIOD_CONFIG = [
    {
        "json_subdir": "main",
        "data_csv":    "site_code.csv",
        "out_name":    "campaign_period.ipynb",
    },
    {
        "json_subdir": "main_prior",
        "data_csv":    "site_code_prior.csv",
        "out_name":    "prior_period.ipynb",
    },
    {
        "json_subdir": "last_main",
        "data_csv":    "last_site_code.csv",
        "out_name":    "last_campaign_period.ipynb",
    },
    {
        "json_subdir": "us_main",
        "data_csv":    "us_site_code.csv",
        "out_name":    "US_campaign_period.ipynb",
    },
    {
        "json_subdir": "us_main_prior",
        "data_csv":    "us_site_code_prior.csv",
        "out_name":    "US_prior_period.ipynb",
    },
    {
        "json_subdir": "last_us_main",
        "data_csv":    "us_last_site_code.csv",
        "out_name":    "US_last_campaign_period.ipynb",
    },
]


# ── 유틸 ─────────────────────────────────────────────────────────

def uid() -> str:
    return str(uuid.uuid4())[:8]


def sort_key(fname: str):
    """파일명 앞 숫자(N_M_) 기준 정렬."""
    m = re.match(r"^(\d+)_(\d+)_", fname)
    if m:
        return (int(m.group(1)), int(m.group(2)), fname)
    m = re.match(r"^(\d+)_", fname)
    if m:
        return (int(m.group(1)), 0, fname)
    return (99, 0, fname)


def code_cell(source_lines: list) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": uid(),
        "metadata": {},
        "outputs": [],
        "source": source_lines,
    }


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


# ── 셀 템플릿 (launch/sample_campaign_for_generate.ipynb 기준) ───

def data_cell(json_fname: str, data_csv: str, json_subdir: str) -> dict:
    lines = [
        "from pathlib import Path\n",
        "import importlib\n",
        "import utils.aa_exporter\n",
        "importlib.reload(utils.aa_exporter)\n",
        "\n",
        "from utils.aa_exporter import ExportConfig, AAExporter\n",
        "import pandas as pd\n",
        "\n",
        f'json_file_name = "{json_fname}"\n',
        "\n",
        f'json_path = Path.cwd().parent / "json" / "{json_subdir}" / json_file_name\n',
        "\n",
        "cfg = ExportConfig(\n",
        f'    data_csv=str(Path.cwd().parent / "date" / "{data_csv}"),\n',
        "    json_file=str(json_path),\n",
        '    out_dir=str(Path.cwd().parent / "aa_exports"),\n',
        "    out_prefix=json_path.stem,\n",
        "    limit=10000,          # 요청 횟수\n",
        "    tb_columns=None,\n",
        "    parallel_sites=True,  # 국가(site) 단위 병렬\n",
        "    max_workers=6,        #  5~8 추천\n",
        "    log_each_page=False,  # False로 바꾸면 속도 높아짐\n",
        ")\n",
        "\n",
        "out_path = AAExporter(cfg).run()\n",
        'print("DONE:", out_path)\n',
        "\n",
        '# 생성된 CSV 바로 불러오기\n',
        'df = pd.read_csv(out_path, encoding="utf-8-sig")\n',
        "df.head()",
    ]
    return code_cell(lines)


# ── 노트북 생성 ──────────────────────────────────────────────────

def build_notebook(cfg: dict) -> dict | None:
    """폴더가 없거나 json이 없으면 None 반환."""
    json_subdir     = cfg["json_subdir"]
    data_csv        = cfg["data_csv"]
    period_json_dir = JSON_DIR / json_subdir

    if not period_json_dir.exists():
        return None

    json_files = sorted(
        [f.name for f in period_json_dir.glob("*.json")
         if "test" not in f.name.lower()],
        key=sort_key,
    )

    if not json_files:
        return None

    cells = [data_cell(fname, data_csv, json_subdir) for fname in json_files]
    return make_notebook(cells)


# ── 실행 ────────────────────────────────────────────────────────

if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    print(f"JSON dir : {JSON_DIR}")
    print(f"OUT dir  : {OUT_DIR}\n")

    for cfg in PERIOD_CONFIG:
        nb = build_notebook(cfg)
        if nb is None:
            print(f"  [SKIP] [{cfg['json_subdir']:14s}] 폴더 없음 또는 json 없음")
            continue

        out_path = OUT_DIR / cfg["out_name"]
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)

        print(f"  [OK]   [{cfg['json_subdir']:14s}] {cfg['out_name']}  ({len(nb['cells'])} cells)")

    print("\nDone!")
