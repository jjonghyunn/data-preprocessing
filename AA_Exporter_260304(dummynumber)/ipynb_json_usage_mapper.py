import os
import re
import json
import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR    = Path(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR    = BASE_DIR / "json"
OUT_DIR     = BASE_DIR / "json_usage_report"
MAPPING_CSV = BASE_DIR / "tb_column_name_mapping.csv"

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
            fname = Path(m).name
            if fname not in seen:
                seen.add(fname)
                refs.append(fname)
    return refs


def get_status(in_folder: bool, in_mapping: bool, in_nb: bool) -> str:
    if in_folder and in_mapping and in_nb:
        return "✅ 정상"
    if in_folder and in_mapping and not in_nb:
        return "⚠️ 노트북미사용"
    if in_folder and not in_mapping and in_nb:
        return "⚠️ 매핑없음→skip될것"
    if in_folder and not in_mapping and not in_nb:
        return "❌ 불필요JSON(매핑·노트북 모두없음)"
    if not in_folder and in_mapping and in_nb:
        return "🔴 JSON없음(노트북에있으나파일없음)"
    if not in_folder and in_mapping and not in_nb:
        return "🔴 JSON없음(매핑만있음)"
    return "-"


# ── tb_column_name_mapping.csv 로드 ───────────────────────────────
mapping_tbs = set()
if MAPPING_CSV.exists():
    with open(MAPPING_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tb = row.get("tb", "").strip()
            if tb:
                mapping_tbs.add(tb)
    print(f"▶ 매핑CSV tb 항목: {len(mapping_tbs)}개")
else:
    print(f"⚠  매핑CSV 없음: {MAPPING_CSV}")

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
all_json_stems = {Path(f).stem for f in all_json_files}

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

    print(f"  ✔ {nb_stem}_json_usage.csv  ({len(refs)}개 참조)")

# ── 전체 통합 CSV (json폴더 + 매핑CSV 합집합 기준) ────────────────
all_stems = all_json_stems | mapping_tbs  # 합집합

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

# ── 요약 출력 ─────────────────────────────────────────────────────
cnt_ok            = sum(1 for s in all_stems if s in all_json_stems and s in mapping_tbs and f"{s}.json" in all_used)
cnt_no_mapping    = sum(1 for s in all_json_stems if s not in mapping_tbs)
cnt_nb_unused     = sum(1 for s in all_json_stems if s in mapping_tbs and f"{s}.json" not in all_used)
cnt_tb_no_json    = sum(1 for tb in mapping_tbs if tb not in all_json_stems)
cnt_nb_no_map     = sum(1 for f, nbs in all_used.items() if nbs and Path(f).stem not in mapping_tbs)

print(f"\n{'─'*50}")
print(f"노트북 수                  : {len(nb_paths)}개")
print(f"json 폴더 파일 수          : {len(all_json_files)}개")
print(f"매핑CSV tb 항목 수         : {len(mapping_tbs)}개")
print(f"전체 고유 stem 수          : {len(all_stems)}개")
print(f"")
print(f"  ✅ 정상(폴더+매핑+노트북): {cnt_ok}개")
print(f"  ⚠️  매핑없음→skip될것    : {cnt_nb_no_map}개")
print(f"  ⚠️  노트북미사용         : {cnt_nb_unused}개")
print(f"  ❌ 불필요JSON            : {cnt_no_mapping - cnt_nb_no_map}개")
print(f"  🔴 JSON없음(매핑만있음)  : {cnt_tb_no_json}개  ← JSON 생성 필요")
print(f"\n출력 폴더: {OUT_DIR}")
print(f"  - 노트북별 CSV           : {len(nb_paths)}개")
print(f"  - 통합 검수 CSV          : _all_check.csv")
