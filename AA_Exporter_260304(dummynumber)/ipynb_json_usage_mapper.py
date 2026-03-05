import os
import re
import json
import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR = BASE_DIR / "json"
OUT_DIR  = BASE_DIR / "json_usage_report"

# ── 옵션: 특정 ipynb만 지정 (비워두면 폴더 내 전체 스캔) ──────────
# 확장자(.ipynb) 있어도 되고 없어도 됨
TARGET_NOTEBOOKS = """
26ny_campaign_period
26ny_prior_period
25ny_last_campaign_period
""".strip().splitlines()
# ─────────────────────────────────────────────────────────────────

JSON_PATTERN = re.compile(r'["\']([^"\']*\.json)["\']')


def extract_json_refs(nb_path: Path) -> list:
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    seen, refs = set(), []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        for m in JSON_PATTERN.findall(source):
            fname = Path(m).name  # 경로 포함된 경우 파일명만 추출
            if fname not in seen:
                seen.add(fname)
                refs.append(fname)
    return refs


# ── 노트북 목록 결정 ───────────────────────────────────────────────
targets = [t.strip() for t in TARGET_NOTEBOOKS if t.strip()]

if targets:
    nb_paths = []
    for name in targets:
        p = BASE_DIR / name
        if p.suffix != ".ipynb":
            p = p.with_suffix(".ipynb")
        if p.exists():
            nb_paths.append(p)
        else:
            print(f"⚠  파일 없음: {p.name}")
else:
    nb_paths = sorted([
        p for p in BASE_DIR.glob("*.ipynb")
        if ".ipynb_checkpoints" not in str(p)
    ])

# ── json 폴더 내 전체 파일 목록 ────────────────────────────────────
all_json_files = sorted([
    f.name for f in JSON_DIR.glob("*.json")
    if ".ipynb_checkpoints" not in str(f)
])

# ── 노트북별 CSV 생성 + 전체 사용 현황 집계 ───────────────────────
OUT_DIR.mkdir(exist_ok=True)
all_used = defaultdict(list)  # json파일명 → [사용된 노트북명 리스트]

print(f"▶ 노트북 {len(nb_paths)}개 처리 중...\n")

for nb_path in nb_paths:
    refs = extract_json_refs(nb_path)
    nb_stem = nb_path.stem

    out_csv = OUT_DIR / f"{nb_stem}_json_usage.csv"
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["no", "json_file", "in_json_folder"])
        for i, ref in enumerate(refs, 1):
            in_folder = "O" if ref in all_json_files else "X"
            w.writerow([i, ref, in_folder])
            all_used[ref].append(nb_stem)

    print(f"  ✔ {nb_stem}_json_usage.csv  ({len(refs)}개 참조)")

# ── 전체 매핑 CSV (json 폴더 파일 기준) ───────────────────────────
mapping_csv = OUT_DIR / "_all_json_mapping.csv"
with open(mapping_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["no", "json_file", "used", "used_in_notebooks"])
    for i, fname in enumerate(all_json_files, 1):
        notebooks = all_used.get(fname, [])
        used = "O" if notebooks else "X"
        w.writerow([i, fname, used, " / ".join(notebooks)])

cnt_used   = sum(1 for f in all_json_files if f in all_used)
cnt_unused = len(all_json_files) - cnt_used

print(f"\n{'─'*45}")
print(f"노트북 수           : {len(nb_paths)}개")
print(f"json 폴더 파일 수   : {len(all_json_files)}개")
print(f"  사용됨  (O)       : {cnt_used}개")
print(f"  미사용  (X)       : {cnt_unused}개")
print(f"\n출력 폴더: {OUT_DIR}")
print(f"  - 노트북별 CSV    : {len(nb_paths)}개")
print(f"  - 전체 매핑 CSV   : _all_json_mapping.csv")
