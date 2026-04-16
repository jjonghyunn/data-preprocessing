import os
import re
import json
import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR    = Path(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR    = BASE_DIR / "json"
OUT_DIR     = BASE_DIR / "json_usage_report"
MAPPING_CSV = BASE_DIR / "ref" / "tb_column_name_mapping_corrected.csv"

JSON_SUBDIRS = ["main", "main_prior", "us_main", "us_main_prior", "last_main", "last_us_main"]

# 검사할 노트북 목록 (비워두면 launch/ 폴더 전체 스캔)
TARGET_NOTEBOOKS = """
campaign_period
last_campaign_period
prior_period
US_campaign_period
US_last_campaign_period
US_prior_period
""".strip().splitlines()

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
            fname = Path(m).name
            if fname not in seen:
                seen.add(fname)
                refs.append(fname)
    return refs


def get_status(in_folder: bool, in_mapping: bool, in_nb: bool) -> str:
    if in_folder and in_mapping and in_nb:
        return "정상"
    if in_folder and in_mapping and not in_nb:
        return "노트북미사용"
    if in_folder and not in_mapping and in_nb:
        return "매핑없음->skip될것"
    if in_folder and not in_mapping and not in_nb:
        return "불필요JSON(매핑/노트북 모두없음)"
    if not in_folder and in_mapping and in_nb:
        return "JSON없음(노트북에있으나파일없음)"
    if not in_folder and in_mapping and not in_nb:
        return "JSON없음(매핑만있음)"
    return "-"


mapping_tbs = set()
if MAPPING_CSV.exists():
    with open(MAPPING_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tb = row.get("tb", "").strip()
            if tb:
                mapping_tbs.add(tb)
    print(f"매핑CSV tb 항목: {len(mapping_tbs)}개")
else:
    print(f"매핑CSV 없음: {MAPPING_CSV}")

# 노트북 목록 결정 (launch/ 폴더에서 검색)
targets = [t.strip() for t in TARGET_NOTEBOOKS if t.strip()]
launch_dir = BASE_DIR / "launch"

all_ipynb = [
    p for p in launch_dir.glob("*.ipynb")
    if ".ipynb_checkpoints" not in str(p)
]

if targets:
    nb_paths = []
    for name in targets:
        keyword = Path(name).stem
        matched = [p for p in all_ipynb if keyword in p.stem]
        if matched:
            nb_paths.extend(matched)
        else:
            print(f"매칭되는 파일 없음: '{keyword}'")
    nb_paths = sorted(set(nb_paths))
else:
    nb_paths = sorted(all_ipynb)

# json 전체 파일 목록 (서브폴더 포함)
all_json_files = sorted([
    f.name for subdir in JSON_SUBDIRS
    for f in (JSON_DIR / subdir).glob("*.json")
    if ".ipynb_checkpoints" not in str(f)
])
all_json_stems = {Path(f).stem for f in all_json_files}

OUT_DIR.mkdir(exist_ok=True)
all_used = defaultdict(list)

print(f"노트북 {len(nb_paths)}개 처리 중...\n")

for nb_path in nb_paths:
    refs = extract_json_refs(nb_path)
    nb_stem = nb_path.stem

    out_csv = OUT_DIR / f"{nb_stem}_json_usage.csv"
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["no", "json_file", "in_json_folder", "in_mapping_csv", "status"])
        for i, ref in enumerate(refs, 1):
            stem       = Path(ref).stem
            in_folder  = stem in all_json_stems
            in_mapping = stem in mapping_tbs
            w.writerow([
                i, ref,
                "O" if in_folder  else "X",
                "O" if in_mapping else "X",
                get_status(in_folder, in_mapping, True),
            ])
            all_used[ref].append(nb_stem)

    print(f"  {nb_stem}_json_usage.csv  ({len(refs)}개 참조)")

# 전체 통합 CSV
all_stems = all_json_stems | mapping_tbs

unified_csv = OUT_DIR / "_all_check.csv"
with open(unified_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["no", "stem", "in_json_folder", "in_mapping_csv", "used_in_nb", "used_in_notebooks", "status"])
    for i, stem in enumerate(sorted(all_stems), 1):
        fname      = f"{stem}.json"
        in_folder  = stem in all_json_stems
        in_mapping = stem in mapping_tbs
        notebooks  = all_used.get(fname, [])
        in_nb      = bool(notebooks)
        w.writerow([
            i, stem,
            "O" if in_folder  else "X",
            "O" if in_mapping else "X",
            "O" if in_nb      else "X",
            " / ".join(notebooks),
            get_status(in_folder, in_mapping, in_nb),
        ])

cnt_ok         = sum(1 for s in all_stems if s in all_json_stems and s in mapping_tbs and f"{s}.json" in all_used)
cnt_no_mapping = sum(1 for s in all_json_stems if s not in mapping_tbs)
cnt_nb_unused  = sum(1 for s in all_json_stems if s in mapping_tbs and f"{s}.json" not in all_used)
cnt_tb_no_json = sum(1 for tb in mapping_tbs if tb not in all_json_stems)
cnt_nb_no_map  = sum(1 for f, nbs in all_used.items() if nbs and Path(f).stem not in mapping_tbs)

print(f"\n{'─'*50}")
print(f"노트북 수                  : {len(nb_paths)}개")
print(f"json 폴더 파일 수          : {len(all_json_files)}개")
print(f"매핑CSV tb 항목 수         : {len(mapping_tbs)}개")
print(f"전체 고유 stem 수          : {len(all_stems)}개")
print(f"")
print(f"  정상(폴더+매핑+노트북)  : {cnt_ok}개")
print(f"  매핑없음->skip될것      : {cnt_nb_no_map}개")
print(f"  노트북미사용            : {cnt_nb_unused}개")
print(f"  불필요JSON              : {cnt_no_mapping - cnt_nb_no_map}개")
print(f"  JSON없음(매핑만있음)    : {cnt_tb_no_json}개  <- JSON 생성 필요")
print(f"\n출력 폴더: {OUT_DIR}")
print(f"  - 노트북별 CSV          : {len(nb_paths)}개")
print(f"  - 통합 검수 CSV         : _all_check.csv")
