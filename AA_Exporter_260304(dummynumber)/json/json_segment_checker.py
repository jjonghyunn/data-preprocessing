"""
json_segment_checker.py
──────────────────────────────────────────────────────────────────────
json 폴더의 JSON 파일 간 세그먼트 ID 일관성을 검수합니다.

[검사 1] 26_ny_X.json vs 26_ny_X_prior.json
  → 세그 ID + metric 수 완전 동일해야 정상
  → 다르면 어느 쪽에만 있는 세그 ID를 명시

[검사 2] 26_ny_X.json vs 25_ny_X.json
  분류는 아래 SHOULD_DIFFER / SHOULD_SAME 키워드 목록으로 관리.
  → 달라야 정상: ✅ 다름(업데이트됨) / ⚠️ 동일(미업데이트)
  → 같아야 정상: ✅ 동일(정상)       / ❌ 다름(의도치않은변경)
  → 특수케이스 : ℹ️ 동일 / ℹ️ 다름 (판단 보류)
  → 25 파일 없음: 별도 표시

[검사 3] json 파일명 키워드 vs panelName 키워드 일관성
  파일명에 cmp → panelName에 "Campaign" 포함 여부
  파일명에 scom → panelName에 "S.com" 포함 여부
  → 일치: 정상  /  불일치: 확인필요

[결과 저장]
  ../json_segment_report/_prior_check.csv        ← 검사 1
  ../json_segment_report/_26vs25_diff.csv        ← 검사 2
  ../json_segment_report/_filename_panel_check.csv ← 검사 3
"""

import json
import re
import os
import sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent          # json/ 폴더
OUT_DIR  = BASE_DIR.parent / "json_segment_report"

print(f"JSON DIR : {BASE_DIR}")
print(f"OUT DIR  : {OUT_DIR}\n")

OUT_DIR.mkdir(exist_ok=True)


# ── 유틸 ──────────────────────────────────────────────────────────────────

def load_segments(path: Path):
    """JSON 파일에서 세그먼트 ID set과 metric 수 반환."""
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
    """JSON 파일의 capacityMetadata.associations에서 panelName 값 추출."""
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
    """
    파일명 키워드(cmp/campaign/scom/prior)와 panelName 키워드(Campaign/S.com/Prior) 일관성 검사.
    Returns: (filename_kw, panel_kw, status)
    """
    stem   = Path(fname).stem.lower()
    tokens = set(stem.split("_"))

    has_cmp   = "cmp"      in tokens or "campaign" in tokens  # cmp / campaign 둘 다 캠페인 의미
    has_scom  = "scom"  in tokens
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
        return filename_kw, panel_kw, "⚠️ panelName없음"

    if not has_cmp and not has_scom:
        # cmp/scom 없는 경우: prior 체크 우선
        if has_prior:
            if has_prior_panel:
                return filename_kw, panel_kw, "정상. json은 prior, 패널명에 Prior포함."
            else:
                return filename_kw, panel_kw, "확인필요. json은 prior이나 패널명에 Prior없음."
        # prior도 없고 cmp/scom도 없음
        if not has_campaign_panel and not has_scom_panel:
            return filename_kw, panel_kw, "해당없음"
        # 파일명에 키워드 없는데 패널에 Campaign/S.com 있음
        parts = []
        if has_campaign_panel: parts.append("Campaign")
        if has_scom_panel:     parts.append("S.com")
        return filename_kw, panel_kw, f"확인필요. json키워드(cmp/scom)없음이나 패널명에 {'/'.join(parts)}포함."

    statuses = []
    cmp_label = fn_cmp_repr if fn_cmp_repr else "cmp"  # 실제 파일명 키워드 그대로 출력

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


# ── 분류 키워드 (매년/캠페인 바뀔 때 여기만 수정) ──────────────────────────
#
# SHOULD_DIFFER: 26 ≠ 25 달라야 정상 (캠페인마다 새 세그 생성)
#   ⚠️ 동일 → copy_last_campaign_json.py 후 25용 세그 미업데이트 의심
#
# SHOULD_SAME: 26 = 25 동일해야 정상 (캠페인 무관 고정 세그)
#   ❌ 다름 → 의도치 않은 변경 가능성
#
# 위 두 목록에 없으면 → 특수케이스(ℹ️)로 표시만 함
# ────────────────────────────────────────────────────────────────────────────
SHOULD_DIFFER = [
    "_cmp",           # *_cmp_* / *_cmp.json
    "campaign",       # *campaign*
    "3_1_",           # 3_1_channel_internal
    "4_1_",           # 4_1_order_cvr_loginout
    "bestselling",    # 연도별 베스트셀러 세그 다름
]

SHOULD_SAME = [
    "_scom_",         # scom 계열 기본 트래픽
    "6_1_",           # 6_1_multi_order_cross_sell (26=25=prior 동일)
    "6_2_",           # 6_2_total_order_cross_sell (26=25=prior 동일)
    "4_2_",           # 4_2_order_cvr_visit_visitor (25 고정, 26 캠페인이나 현재 동일)
]
# ────────────────────────────────────────────────────────────────────────────


def seg_type(fname: str) -> str:
    """파일명으로 세그 유형 분류."""
    name = fname.lower()
    for kw in SHOULD_DIFFER:
        if kw.lower() in name:
            return "달라야정상"
    for kw in SHOULD_SAME:
        if kw.lower() in name:
            return "같아야정상"
    return "특수케이스"


def diff_status_prior(same_seg: bool, same_metric: bool) -> str:
    if same_seg and same_metric:
        return "✅ 정상(동일)"
    if same_seg and not same_metric:
        return "❌ metric수다름"
    return "❌ 세그다름"


def diff_status_26vs25(stype: str, same_seg: bool, same_metric: bool) -> str:
    if stype == "같아야정상":
        if same_seg and same_metric:
            return "✅ 정상(동일)"
        return "❌ 문제(달라짐)"
    if stype == "달라야정상":
        if not same_seg:
            return "✅ 업데이트됨(다름)"
        if same_seg and not same_metric:
            return "⚠️ 세그동일·metric수다름"
        return "⚠️ 미업데이트(25용세그갱신필요)"
    # 특수케이스
    if same_seg and same_metric:
        return "ℹ️ 동일"
    return "ℹ️ 다름"


# ── 파일 목록 ──────────────────────────────────────────────────────────────

all_files = {f.name: f for f in BASE_DIR.glob("*.json") if not f.name.startswith("copy")}

ny26_base  = [n for n in all_files if n.startswith("26_")  and not n.endswith("_prior.json")]
ny26_prior = [n for n in all_files if n.startswith("26_")  and n.endswith("_prior.json")]
ny25       = {n for n in all_files if n.startswith("25_")}


# ── 검사 1: 26_ny_X vs 26_ny_X_prior ──────────────────────────────────────

print("=" * 65)
print("검사 1: 26_ny_X.json vs 26_ny_X_prior.json  (동일해야 정상)")
print("=" * 65)

rows_prior = []
for pf in sorted(ny26_prior):
    base = pf.replace("_prior.json", ".json")
    if base not in all_files:
        rows_prior.append({
            "prior_file"      : pf,
            "base_file"       : base,
            "status"          : "❌ 기준파일없음",
            "metric_prior"    : "",
            "metric_base"     : "",
            "only_in_base"    : "",
            "only_in_prior"   : "",
        })
        print(f"  [기준파일없음] {pf}")
        continue

    s_base,  m_base  = load_segments(all_files[base])
    s_prior, m_prior = load_segments(all_files[pf])

    only_base  = sorted(s_base  - s_prior)
    only_prior = sorted(s_prior - s_base)
    same_seg   = not only_base and not only_prior
    same_m     = m_base == m_prior
    status     = diff_status_prior(same_seg, same_m)

    rows_prior.append({
        "prior_file"    : pf,
        "base_file"     : base,
        "status"        : status,
        "metric_base"   : m_base,
        "metric_prior"  : m_prior,
        "only_in_base"  : " / ".join(only_base),
        "only_in_prior" : " / ".join(only_prior),
    })
    print(f"  {status}  {base} (m:{m_base}) vs {pf} (m:{m_prior})")
    if only_base:  print(f"      base에만 : {only_base}")
    if only_prior: print(f"      prior에만: {only_prior}")

prior_df = pd.DataFrame(rows_prior, columns=[
    "prior_file", "base_file", "status",
    "metric_base", "metric_prior", "only_in_base", "only_in_prior",
])
prior_path = OUT_DIR / "_prior_check.csv"
prior_df.to_csv(prior_path, index=False, encoding="utf-8-sig")
print(f"\n▶ 저장: {prior_path}")


# ── 검사 2: 26_ny_X vs 25_ny_X ────────────────────────────────────────────

print()
print("=" * 65)
print("검사 2: 26_ny_X.json vs 25_ny_X.json")
print("  같아야정상: 동일=✅정상  /  다름=❌문제(의도치않은변경)")
print("  달라야정상: 다름=✅업데이트됨  /  동일=⚠️미업데이트(25용세그갱신필요)")
print("  특수케이스: ℹ️ 그대로 표시")
print("=" * 65)

rows_diff = []
no_pair   = []  # 25 파일 없음

for f26 in sorted(ny26_base):
    f25 = f26.replace("26_ny_", "25_ny_").replace("26_bl_", "25_bl_")
    stype = seg_type(f26)

    if f25 not in ny25:
        no_pair.append(f26)
        rows_diff.append({
            "file_26"       : f26,
            "file_25"       : f25,
            "seg_type"      : stype,
            "status"        : "— 25파일없음",
            "metric_26"     : "",
            "metric_25"     : "",
            "only_in_26"    : "",
            "only_in_25"    : "",
        })
        continue

    s26, m26 = load_segments(all_files[f26])
    s25, m25 = load_segments(all_files[f25])

    only_26  = sorted(s26 - s25)
    only_25  = sorted(s25 - s26)
    same_seg = not only_26 and not only_25
    same_m   = m26 == m25
    status   = diff_status_26vs25(stype, same_seg, same_m)

    rows_diff.append({
        "file_26"    : f26,
        "file_25"    : f25,
        "seg_type"   : stype,
        "status"     : status,
        "metric_26"  : m26,
        "metric_25"  : m25,
        "only_in_26" : " / ".join(only_26),
        "only_in_25" : " / ".join(only_25),
    })
    print(f"  {status}  [{stype}] m:{m26}→{m25}  {f26}")
    if only_26: print(f"      26에만: {only_26}")
    if only_25: print(f"      25에만: {only_25}")

if no_pair:
    print(f"\n  — 25파일 없음 ({len(no_pair)}개, 26전용으로 정상)")
    for f in no_pair:
        print(f"      {f}")

diff_df = pd.DataFrame(rows_diff, columns=[
    "file_26", "file_25", "seg_type", "status",
    "metric_26", "metric_25", "only_in_26", "only_in_25",
])
diff_path = OUT_DIR / "_26vs25_diff.csv"
diff_df.to_csv(diff_path, index=False, encoding="utf-8-sig")
print(f"\n▶ 저장: {diff_path}")


# ── 검사 3: 파일명 키워드 vs panelName 키워드 ─────────────────────────────

print()
print("=" * 65)
print("검사 3: json 파일명 키워드 vs panelName 키워드 일관성")
print("  cmp → 패널명에 'Campaign' 포함 여부")
print("  scom → 패널명에 'S.com' 포함 여부")
print("=" * 65)

rows_panel = []
for fname in sorted(all_files):
    panel_name  = get_panel_name(all_files[fname])
    fn_kw, p_kw, status = check_filename_vs_panel(fname, panel_name)
    rows_panel.append({
        "file"        : fname,
        "filename_kw" : fn_kw,
        "panel_name"  : panel_name,
        "panel_kw"    : p_kw,
        "status"      : status,
    })
    if status != "해당없음":
        print(f"  {status}  [{fname}]")
        if panel_name:
            print(f"      panelName: {panel_name}")

panel_df   = pd.DataFrame(rows_panel, columns=["file", "filename_kw", "panel_name", "panel_kw", "status"])
panel_path = OUT_DIR / "_filename_panel_check.csv"
panel_df.to_csv(panel_path, index=False, encoding="utf-8-sig")
print(f"\n▶ 저장: {panel_path}")


# ── 요약 ──────────────────────────────────────────────────────────────────

print()
print("=" * 65)

# 검사 1 요약
cnt_p_ok  = sum(1 for r in rows_prior if r["status"] == "✅ 정상(동일)")
cnt_p_err = len(rows_prior) - cnt_p_ok
print(f"[검사 1] prior ↔ base: 정상 {cnt_p_ok} / 문제 {cnt_p_err}")

# 검사 2 요약
ok_same    = sum(1 for r in rows_diff if r["seg_type"] == "같아야정상" and r["status"] == "✅ 정상(동일)")
err_same   = sum(1 for r in rows_diff if r["seg_type"] == "같아야정상" and "❌" in r["status"])
ok_diff    = sum(1 for r in rows_diff if r["seg_type"] == "달라야정상" and r["status"] == "✅ 업데이트됨(다름)")
warn_diff  = sum(1 for r in rows_diff if r["seg_type"] == "달라야정상" and "⚠️" in r["status"])
special    = sum(1 for r in rows_diff if r["seg_type"] == "특수케이스" and "— " not in r["status"])
no_25_cnt  = len(no_pair)
print(f"[검사 2] 같아야정상: 정상 {ok_same} / 문제 {err_same}")
print(f"         달라야정상: 업데이트됨 {ok_diff} / ⚠️미업데이트 {warn_diff}")
print(f"         특수케이스: {special}")
print(f"         25파일없음(26전용): {no_25_cnt}")

# 검사 3 요약
cnt_panel_ok   = sum(1 for r in rows_panel if r["status"].startswith("정상"))
cnt_panel_chk  = sum(1 for r in rows_panel if r["status"].startswith("확인필요"))
cnt_panel_na   = sum(1 for r in rows_panel if r["status"] == "해당없음")
cnt_panel_warn = sum(1 for r in rows_panel if r["status"].startswith("⚠️"))
print(f"[검사 3] 파일명↔패널명: 정상 {cnt_panel_ok} / 확인필요 {cnt_panel_chk} / 해당없음 {cnt_panel_na} / 기타⚠️ {cnt_panel_warn}")
print()
print(f"출력 폴더: {OUT_DIR}")
print(f"  _prior_check.csv  /  _26vs25_diff.csv  /  _filename_panel_check.csv")
