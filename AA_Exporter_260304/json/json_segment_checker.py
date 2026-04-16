"""
json_segment_checker.py
──────────────────────────────────────────────────────────────────────
json 서브폴더의 JSON 파일 간 세그먼트 ID 일관성을 검수합니다.

[검사 1] main/X.json vs main_prior/X_prior.json
         us_main/us_X.json vs us_main_prior/us_X_prior.json
  -> 세그 ID + metric 수 완전 동일해야 정상

[검사 2] main/X.json vs last_main/last_X.json
         us_main/us_X.json vs last_us_main/last_us_X.json
  달라야정상: 업데이트됨(다름) / 미업데이트
  같아야정상: 정상(동일)       / 문제(달라짐)
  특수케이스: 동일 / 다름

[검사 3] json 파일명 키워드 vs panelName 키워드 일관성

[결과 저장]
  ../json_segment_report/_prior_check.csv
  ../json_segment_report/_main_vs_last_diff.csv
  ../json_segment_report/_filename_panel_check.csv
"""

import json
import re
import sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR     = Path(__file__).parent
MAIN_DIR     = BASE_DIR / "main"
PRIOR_DIR    = BASE_DIR / "main_prior"
LAST_DIR     = BASE_DIR / "last_main"
US_DIR       = BASE_DIR / "us_main"
US_PRIOR_DIR = BASE_DIR / "us_main_prior"
LAST_US_DIR  = BASE_DIR / "last_us_main"
OUT_DIR      = BASE_DIR.parent / "json_segment_report"

print(f"JSON DIR : {BASE_DIR}")
print(f"OUT DIR  : {OUT_DIR}\n")

OUT_DIR.mkdir(exist_ok=True)


def load_segments(path: Path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    segs = set()
    for gf in d.get("globalFilters", []):
        if gf.get("type") == "segment":
            segs.add(gf["segmentId"])
    for mf in d.get("metricContainer", {}).get("metricFilters", []):
        if mf.get("type") == "segment":
            segs.add(mf["segmentId"])
    metrics_cnt = len(d.get("metricContainer", {}).get("metrics", []))
    return segs, metrics_cnt


def get_panel_name(path: Path) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        for s in d.get("capacityMetadata", {}).get("associations", []):
            if s.get("name") == "panelName":
                return s.get("value", "")
    except Exception:
        pass
    return ""


def check_filename_vs_panel(fname: str, panel_name: str) -> tuple:
    stem  = Path(fname).stem.lower()
    clean = re.sub(r"^(?:last_us_|last_|us_)", "", stem)
    tokens = set(clean.split("_"))

    has_cmp   = "cmp"  in tokens or "campaign" in tokens
    has_scom  = "scom" in tokens
    has_prior = "prior" in tokens

    has_campaign_panel = "campaign" in panel_name.lower()
    has_scom_panel     = "s.com"    in panel_name.lower()
    has_prior_panel    = "prior"    in panel_name.lower()

    fn_cmp_repr = next((k for k in ["cmp", "campaign"] if k in tokens), None)
    filename_kw = "/".join(filter(None, [
        fn_cmp_repr if has_cmp else None,
        "scom"  if has_scom  else None,
        "prior" if has_prior else None,
    ])) or "-"
    panel_kw = "/".join(k for k, f in [
        ("Campaign", has_campaign_panel),
        ("S.com",    has_scom_panel),
        ("Prior",    has_prior_panel),
    ] if f) or "-"

    if not panel_name:
        return filename_kw, panel_kw, "panelName없음"

    if not has_cmp and not has_scom:
        if has_prior:
            status = "정상. json은 prior, 패널명에 Prior포함." if has_prior_panel \
                     else "확인필요. json은 prior이나 패널명에 Prior없음."
            return filename_kw, panel_kw, status
        if not has_campaign_panel and not has_scom_panel:
            return filename_kw, panel_kw, "해당없음"
        parts = []
        if has_campaign_panel: parts.append("Campaign")
        if has_scom_panel:     parts.append("S.com")
        joined = "/".join(parts)
        return filename_kw, panel_kw, f"확인필요. json키워드(cmp/scom)없음이나 패널명에 {joined}포함."

    statuses = []
    cmp_label = fn_cmp_repr if fn_cmp_repr else "cmp"

    if has_cmp:
        if has_campaign_panel and not has_scom_panel:
            statuses.append(f"정상. json은 {cmp_label}, 패널명에 Campaign포함.")
        elif has_scom_panel and not has_campaign_panel:
            statuses.append(f"확인필요. json은 {cmp_label}이나 패널명에 S.com포함.")
        elif has_campaign_panel and has_scom_panel:
            statuses.append(f"정상. json은 {cmp_label}, 패널명에 Campaign포함(+S.com도 있음).")
        else:
            statuses.append(f"확인필요. json은 {cmp_label}이나 패널명에 Campaign/S.com 없음.")

    if has_scom:
        if has_scom_panel and not has_campaign_panel:
            statuses.append("정상. json은 scom, 패널명에 S.com포함.")
        elif has_campaign_panel and not has_scom_panel:
            statuses.append("확인필요. json은 scom이나 패널명에 Campaign포함.")
        elif has_scom_panel and has_campaign_panel:
            statuses.append("정상. json은 scom, 패널명에 S.com포함(+Campaign도 있음).")
        else:
            statuses.append("확인필요. json은 scom이나 패널명에 S.com/Campaign 없음.")

    return filename_kw, panel_kw, " / ".join(statuses)


SHOULD_DIFFER = ["_cmp", "campaign", "3_1_", "4_1_", "bestselling"]
SHOULD_SAME   = ["_scom_", "6_1_", "6_2_", "4_2_"]


def seg_type(fname: str) -> str:
    name = fname.lower()
    for kw in SHOULD_DIFFER:
        if kw in name:
            return "달라야정상"
    for kw in SHOULD_SAME:
        if kw in name:
            return "같아야정상"
    return "특수케이스"


def diff_status_prior(same_seg: bool, same_metric: bool) -> str:
    if same_seg and same_metric:
        return "정상(동일)"
    if same_seg and not same_metric:
        return "metric수다름"
    return "세그다름"


def diff_status_main_vs_last(stype: str, same_seg: bool, same_metric: bool) -> str:
    if stype == "같아야정상":
        return "정상(동일)" if (same_seg and same_metric) else "문제(달라짐)"
    if stype == "달라야정상":
        if not same_seg:
            return "업데이트됨(다름)"
        if same_seg and not same_metric:
            return "세그동일·metric수다름"
        return "미업데이트(last용세그갱신필요)"
    return "동일" if (same_seg and same_metric) else "다름"


main_files   = {f.name: f for f in MAIN_DIR.glob("*.json")}
prior_files  = {f.name: f for f in PRIOR_DIR.glob("*.json")}
last_files   = {f.name: f for f in LAST_DIR.glob("*.json")}
us_files_map = {f.name: f for f in US_DIR.glob("*.json")}
us_prior_map = {f.name: f for f in US_PRIOR_DIR.glob("*.json")}
last_us_map  = {f.name: f for f in LAST_US_DIR.glob("*.json")}


def check1_pair(base_files, prior_files_map, base_label):
    rows = []
    for fname, fpath in sorted(base_files.items()):
        prior_name = Path(fname).stem + "_prior.json"
        if prior_name not in prior_files_map:
            rows.append({"base_file": f"{base_label}/{fname}", "prior_file": prior_name,
                         "status": "prior파일없음",
                         "metric_base": "", "metric_prior": "",
                         "only_in_base": "", "only_in_prior": ""})
            continue

        s_base,  m_base  = load_segments(fpath)
        s_prior, m_prior = load_segments(prior_files_map[prior_name])
        only_base  = sorted(s_base  - s_prior)
        only_prior = sorted(s_prior - s_base)
        same_seg   = not only_base and not only_prior
        status     = diff_status_prior(same_seg, m_base == m_prior)

        rows.append({"base_file": f"{base_label}/{fname}", "prior_file": prior_name,
                     "status": status,
                     "metric_base": m_base, "metric_prior": m_prior,
                     "only_in_base": " / ".join(only_base),
                     "only_in_prior": " / ".join(only_prior)})
        print(f"  {status}  {fname} (m:{m_base}) vs {prior_name} (m:{m_prior})")
        if only_base:  print(f"      base에만 : {only_base}")
        if only_prior: print(f"      prior에만: {only_prior}")
    return rows


print("=" * 65)
print("검사 1: base.json vs base_prior.json  (동일해야 정상)")
print("=" * 65)
rows_prior = []
print("[글로벌]")
rows_prior += check1_pair(main_files, prior_files, "main")
print("[US]")
rows_prior += check1_pair(us_files_map, us_prior_map, "us_main")

pd.DataFrame(rows_prior, columns=[
    "base_file", "prior_file", "status",
    "metric_base", "metric_prior", "only_in_base", "only_in_prior"
]).to_csv(OUT_DIR / "_prior_check.csv", index=False, encoding="utf-8-sig")
print(f"\n저장: {OUT_DIR / '_prior_check.csv'}")


def check2_pair(cur_files, last_files_map, cur_label, last_label):
    rows = []
    no_pair = []
    for fname, fpath in sorted(cur_files.items()):
        last_name = "last_" + fname
        stype     = seg_type(fname)

        if last_name not in last_files_map:
            no_pair.append(fname)
            rows.append({"cur_file": f"{cur_label}/{fname}",
                         "last_file": f"{last_label}/{last_name}",
                         "seg_type": stype, "status": "last파일없음",
                         "metric_cur": "", "metric_last": "",
                         "only_in_cur": "", "only_in_last": ""})
            continue

        s_cur,  m_cur  = load_segments(fpath)
        s_last, m_last = load_segments(last_files_map[last_name])
        only_cur  = sorted(s_cur  - s_last)
        only_last = sorted(s_last - s_cur)
        same_seg  = not only_cur and not only_last
        status    = diff_status_main_vs_last(stype, same_seg, m_cur == m_last)

        rows.append({"cur_file": f"{cur_label}/{fname}",
                     "last_file": f"{last_label}/{last_name}",
                     "seg_type": stype, "status": status,
                     "metric_cur": m_cur, "metric_last": m_last,
                     "only_in_cur": " / ".join(only_cur),
                     "only_in_last": " / ".join(only_last)})
        print(f"  {status}  [{stype}] m:{m_cur}→{m_last}  {fname}")
        if only_cur:  print(f"      현재에만: {only_cur}")
        if only_last: print(f"      last에만: {only_last}")

    if no_pair:
        print(f"\n  last파일 없음 ({len(no_pair)}개)")
        for f in no_pair:
            print(f"      {f}")
    return rows


print()
print("=" * 65)
print("검사 2: main/*.json vs last_main/last_*.json")
print("  같아야정상: 동일=정상  /  다름=문제")
print("  달라야정상: 다름=업데이트됨  /  동일=미업데이트")
print("=" * 65)
rows_diff = []
print("[글로벌]")
rows_diff += check2_pair(main_files, last_files, "main", "last_main")
print("[US]")
rows_diff += check2_pair(us_files_map, last_us_map, "us_main", "last_us_main")

pd.DataFrame(rows_diff, columns=[
    "cur_file", "last_file", "seg_type", "status",
    "metric_cur", "metric_last", "only_in_cur", "only_in_last"
]).to_csv(OUT_DIR / "_main_vs_last_diff.csv", index=False, encoding="utf-8-sig")
print(f"\n저장: {OUT_DIR / '_main_vs_last_diff.csv'}")


print()
print("=" * 65)
print("검사 3: json 파일명 키워드 vs panelName 키워드 일관성")
print("=" * 65)

all_panel_files = {}
for subdir, folder in [("main", MAIN_DIR), ("main_prior", PRIOR_DIR),
                        ("us_main", US_DIR), ("us_main_prior", US_PRIOR_DIR),
                        ("last_main", LAST_DIR), ("last_us_main", LAST_US_DIR)]:
    for f in folder.glob("*.json"):
        all_panel_files[f"{subdir}/{f.name}"] = f

rows_panel = []
for label_fname, fpath in sorted(all_panel_files.items()):
    panel_name = get_panel_name(fpath)
    fn_kw, p_kw, status = check_filename_vs_panel(Path(fpath).name, panel_name)
    rows_panel.append({"file": label_fname, "filename_kw": fn_kw,
                        "panel_name": panel_name, "panel_kw": p_kw, "status": status})
    if status != "해당없음":
        print(f"  {status}  [{label_fname}]")
        if panel_name:
            print(f"      panelName: {panel_name}")

pd.DataFrame(rows_panel, columns=["file", "filename_kw", "panel_name", "panel_kw", "status"]
).to_csv(OUT_DIR / "_filename_panel_check.csv", index=False, encoding="utf-8-sig")
print(f"\n저장: {OUT_DIR / '_filename_panel_check.csv'}")


print()
print("=" * 65)
cnt_p_ok  = sum(1 for r in rows_prior if "정상" in r["status"])
print(f"[검사 1] prior 기준: 정상 {cnt_p_ok} / 문제 {len(rows_prior) - cnt_p_ok}")

ok_same   = sum(1 for r in rows_diff if r["seg_type"] == "같아야정상" and r["status"] == "정상(동일)")
err_same  = sum(1 for r in rows_diff if r["seg_type"] == "같아야정상" and "문제" in r["status"])
ok_diff   = sum(1 for r in rows_diff if r["seg_type"] == "달라야정상" and r["status"] == "업데이트됨(다름)")
warn_diff = sum(1 for r in rows_diff if r["seg_type"] == "달라야정상" and "미업데이트" in r["status"])
special   = sum(1 for r in rows_diff if r["seg_type"] == "특수케이스" and "last파일없음" not in r["status"])
no_last   = sum(1 for r in rows_diff if r["status"] == "last파일없음")
print(f"[검사 2] 같아야정상: 정상 {ok_same} / 문제 {err_same}")
print(f"         달라야정상: 업데이트됨 {ok_diff} / 미업데이트 {warn_diff}")
print(f"         특수케이스: {special}")
print(f"         last파일없음: {no_last}")

cnt_ok   = sum(1 for r in rows_panel if r["status"].startswith("정상"))
cnt_chk  = sum(1 for r in rows_panel if r["status"].startswith("확인필요"))
cnt_na   = sum(1 for r in rows_panel if r["status"] == "해당없음")
cnt_warn = sum(1 for r in rows_panel if "panelName없음" in r["status"])
print(f"[검사 3] 파일명->패널명: 정상 {cnt_ok} / 확인필요 {cnt_chk} / 해당없음 {cnt_na} / panelName없음 {cnt_warn}")
print(f"\n출력 폴더: {OUT_DIR}")
print(f"  _prior_check.csv  /  _main_vs_last_diff.csv  /  _filename_panel_check.csv")
