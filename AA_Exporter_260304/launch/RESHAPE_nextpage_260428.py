# RESHAPE_nextpage_260428.py
# 2026-04-28  Jonghyun Park w/ Claude
# nextpage SQL (nextpage_260129_vdda_separate.sql) Python 포팅
#
# 두 가지 입력 모드 자동 감지:
#   (A) 단일 파일 모드: COMBINED_PREFIX 파일이 있으면 사용
#       → value1=TOTAL, value2=MX, value3=VD, value4=DA
#   (B) 분리 파일 모드: A_PREFIX + B_PREFIX 두 파일 사용
#       → A.value1=TOTAL, A.value2=MX
#       → B.value1=VD,    B.value2=DA  (컬럼명 동일, 의미만 다름)
#
# 우선순위: COMBINED 파일이 있으면 그것만 사용. 없으면 A+B 모두 필요.
# campaign_tier 조인은 제외 → TIER/SUBS/COUNTRY 빈 칼럼 출력

from pathlib import Path
import re
import pandas as pd

# ── 경로 설정 ──────────────────────────────────────────────────────
LAUNCH_DIR  = Path(__file__).parent
ROOT_DIR    = LAUNCH_DIR.parent
EXPORTS_DIR = ROOT_DIR / "aa_exports"

# ── 파일 prefix 설정 (실제 파일명 확정되면 여기만 수정) ────────────
# 단일 파일 모드용
COMBINED_PREFIX = "next_page"             # value1=TOTAL, value2=MX, value3=VD, value4=DA

# 분리 파일 모드용 (COMBINED 없을 때 fallback)
A_PREFIX = "next_page_total_mx"           # value1=TOTAL, value2=MX
B_PREFIX = "next_page_vd_da"              # value1=VD,    value2=DA

OUTPUT_NAME = "next_page_stacked_separate.csv"

# ── 타임스탬프 패턴 ────────────────────────────────────────────────
_TS_PAT = re.compile(r"_(\d{8}_\d{4})$")

# ── TOP N (SQL: rn <= 10) ──────────────────────────────────────────
TOP_N = 10


# ── SITE CODE 정규화 (SQL: part1/part2 case 절) ────────────────────
def normalize_site_code(sc: str) -> str:
    s = str(sc).strip().lower()
    if s == "uk_epp":
        return "UK"
    if s == "ku":
        return "IQ_KU"
    return s.upper()


# ── breakdown 매핑 (SQL: mapped CTE) ───────────────────────────────
def map_breakdown(site_code: str, breakdown: str) -> str:
    sc = str(site_code).strip().lower()
    bd = str(breakdown)
    bd_low = bd.lower()
    bd_no_proto = bd_low.replace("https://", "")

    if sc == "us":
        if bd_no_proto in ("www.company_name.com/us", "www.company_name.com/us/"):
            return "home"
        if "/buy/" in bd_low:
            return "product detail"
        if "/us/tvs/" in bd_low:
            return "product category detail"
        if "/all-" in bd_low:
            return "product finder"
        if "/offer/" in bd_low:
            return "offer main"
        if "/shop/featured-offers/" in bd_low:
            return "offer main"
        if "/web/account/" in bd_low:
            return "my account"

    if sc == "sec":
        if bd_low in ("revamp product finder", "revamp product detail"):
            return bd_low.replace("revamp ", "")
        if bd_low == "buying configurator":
            return "product detail"

    return bd


# ── pagetype2 (SQL: mapped CTE 두 번째 case) ───────────────────────
def get_pagetype2(site_code: str, breakdown: str) -> str | None:
    bd_low = str(breakdown).lower()
    sc = str(site_code).strip().lower()

    if bd_low in ("product category detail",):
        return "PCD"
    if bd_low in ("product detail", "revamp product detail"):
        return "PD"
    if bd_low in ("product finder", "revamp product finder"):
        return "PF"
    if bd_low == "shop detail":
        return "SD"
    if bd_low == "buying configurator" and sc == "sec":
        return "PD"
    return None


# ── 최종 CATEGORY (SQL: 마지막 SELECT) ─────────────────────────────
def get_category(page_type: str, site_code: str) -> str:
    pt = str(page_type)
    pt_low = pt.lower()
    sc = str(site_code).strip().lower()

    if pt.endswith("PD"):
        return "product detail"
    if pt.endswith("PF"):
        return "product finder"
    if pt.endswith("PCD"):
        return "product category detail"
    if pt.endswith("SD"):
        return "shop detail"
    if sc == "sec" and pt_low == "buying configurator":
        return "product detail"
    return pt.replace("revamp ", "")


# ── VALUE_TYPE (SQL: 마지막 SELECT) ────────────────────────────────
def get_value_type(page_type: str, site_code: str) -> str:
    pt = str(page_type)
    pt_low = pt.lower()
    sc = str(site_code).strip().lower()

    if pt_low in ("product category detail", "product detail", "revamp product detail",
                  "product finder", "revamp product finder", "shop detail"):
        return "both"
    if sc == "sec" and pt_low == "buying configurator":
        return "both"
    if pt.startswith("MX") or pt.startswith("VD") or pt.startswith("DA"):
        return "division"
    return "non-division"


# ── 최신 파일 1개 선택 (정확한 prefix fullmatch) ───────────────────
def find_latest(prefix: str) -> Path | None:
    """tb_key 직후가 정확히 _YYYYMMDD_HHMM 인 파일만 매칭.

    glob "{prefix}_*"는 nextpage_total_mx도 nextpage_*에 잡히므로 정규식 fullmatch 사용.
    """
    pat = re.compile(rf"^{re.escape(prefix)}_\d{{8}}_\d{{4}}$")
    candidates = [
        f for f in EXPORTS_DIR.glob(f"{prefix}_*.csv")
        if pat.match(f.stem)
        and "_stacked" not in f.name
        and "_long" not in f.name
        and not f.name.startswith("union_")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda f: _TS_PAT.search(f.stem).group(1))


def _read_ok(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    if "status" in df.columns:
        df = df[df["status"].astype(str).str.upper() == "OK"].copy()
    return df


# ── origin DataFrame 로드 (모드 자동 감지) ─────────────────────────
def load_origin() -> pd.DataFrame:
    """반환: columns = [site_code, breakdown, total, mx, vd, da]"""
    combined_path = find_latest(COMBINED_PREFIX)

    if combined_path is not None:
        # 단일 파일 모드: value1~4 = TOTAL/MX/VD/DA
        print(f"▶ COMBINED 모드: {combined_path.name}")
        df = _read_ok(combined_path)
        for col in ("value1", "value2", "value3", "value4"):
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        origin = df[["Site_Code", "value", "value1", "value2", "value3", "value4"]].rename(
            columns={"Site_Code": "site_code", "value": "breakdown",
                     "value1": "total", "value2": "mx",
                     "value3": "vd",    "value4": "da"}
        )
        origin["site_code"] = origin["site_code"].astype(str).str.strip().str.lower()
        return origin

    # 분리 파일 모드: A + B
    a_path = find_latest(A_PREFIX)
    b_path = find_latest(B_PREFIX)
    if a_path is None and b_path is None:
        raise FileNotFoundError(
            f"입력 파일 없음: COMBINED({COMBINED_PREFIX}) / A({A_PREFIX}) / B({B_PREFIX}) 모두 미발견"
        )
    if a_path is None:
        raise FileNotFoundError(f"A 파일 없음: prefix={A_PREFIX}")
    if b_path is None:
        raise FileNotFoundError(f"B 파일 없음: prefix={B_PREFIX}")

    print(f"▶ SEPARATE 모드")
    print(f"  A: {a_path.name}")
    print(f"  B: {b_path.name}")

    a_df = _read_ok(a_path)
    b_df = _read_ok(b_path)
    for col in ("value1", "value2"):
        a_df[col] = pd.to_numeric(a_df[col], errors="coerce").fillna(0)
        b_df[col] = pd.to_numeric(b_df[col], errors="coerce").fillna(0)

    a_use = a_df[["Site_Code", "value", "value1", "value2"]].rename(
        columns={"Site_Code": "site_code", "value": "breakdown",
                 "value1": "total", "value2": "mx"}
    )
    b_use = b_df[["Site_Code", "value", "value1", "value2"]].rename(
        columns={"Site_Code": "site_code", "value": "breakdown",
                 "value1": "vd", "value2": "da"}
    )
    a_use["site_code"] = a_use["site_code"].astype(str).str.strip().str.lower()
    b_use["site_code"] = b_use["site_code"].astype(str).str.strip().str.lower()

    origin = a_use.merge(b_use, on=["site_code", "breakdown"], how="left")
    origin[["vd", "da"]] = origin[["vd", "da"]].fillna(0)
    return origin


# ── 메인 정제 로직 ─────────────────────────────────────────────────
def main():
    origin = load_origin()

    # ── mapped: breakdown 재매핑 + pagetype2 ───────────────────────
    origin["origin_breakdown"] = origin["breakdown"]
    origin["breakdown"] = origin.apply(
        lambda r: map_breakdown(r["site_code"], r["origin_breakdown"]), axis=1
    )
    origin["pagetype2"] = origin.apply(
        lambda r: get_pagetype2(r["site_code"], r["breakdown"]), axis=1
    )

    # ── unpivot: TOTAL/MX/VD/DA → division 컬럼 ────────────────────
    long_parts = []
    for div, col in [("TOTAL", "total"), ("MX", "mx"), ("VD", "vd"), ("DA", "da")]:
        part = origin[["origin_breakdown", "site_code", "breakdown", "pagetype2"]].copy()
        part["division"] = div
        part["value"] = origin[col]
        long_parts.append(part)
    unpivoted = pd.concat(long_parts, ignore_index=True)

    # ── with_div2: division_pagetype2 (예: "MX PD") + breakdown != '*' ──
    with_div2 = unpivoted[unpivoted["breakdown"] != "*"].copy()
    with_div2["division_pagetype2"] = with_div2.apply(
        lambda r: f"{r['division']} {r['pagetype2']}" if pd.notna(r["pagetype2"]) else None,
        axis=1,
    )
    with_div2 = with_div2.drop_duplicates()

    # ── totals_ranked: TOTAL만, site_code별 value desc 순위 ────────
    totals = with_div2[with_div2["division"] == "TOTAL"].copy()
    totals = totals.rename(columns={"breakdown": "page_type"})
    totals["rn"] = totals.groupby("site_code")["value"].rank(method="first", ascending=False)
    totals_ranked = totals[["origin_breakdown", "site_code", "page_type", "value", "rn"]]

    # ── part1: top N 직접 ───────────────────────────────────────────
    part1 = totals_ranked[totals_ranked["rn"] <= TOP_N].copy()
    part1["site_code"] = part1["site_code"].apply(normalize_site_code)
    part1 = part1[["origin_breakdown", "site_code", "page_type", "value"]]

    # ── part2: division_pagetype2 합산 (top N에 속한 page_type만) ──
    top_keys = totals_ranked[totals_ranked["rn"] <= TOP_N][["site_code", "page_type"]]

    cand = with_div2[with_div2["division_pagetype2"].notna()].copy()
    # SQL: tr.page_type = with_div2.breakdown OR tr.page_type = with_div2.pagetype2
    match_bd = cand.merge(
        top_keys.rename(columns={"page_type": "breakdown"}),
        on=["site_code", "breakdown"], how="inner"
    )
    match_pt = cand.merge(
        top_keys.rename(columns={"page_type": "pagetype2"}),
        on=["site_code", "pagetype2"], how="inner"
    )
    cand_match = pd.concat([match_bd, match_pt], ignore_index=True).drop_duplicates(
        subset=["origin_breakdown", "site_code", "breakdown", "pagetype2",
                "division", "value", "division_pagetype2"]
    )

    part2 = (
        cand_match.groupby(["site_code", "division_pagetype2"], as_index=False)["value"].sum()
    )
    # origin_breakdown은 part2에서 first 사용 (SQL group by 외 컬럼 동작)
    first_origin = (
        cand_match.groupby(["site_code", "division_pagetype2"], as_index=False)["origin_breakdown"].first()
    )
    part2 = part2.merge(first_origin, on=["site_code", "division_pagetype2"])
    part2 = part2.rename(columns={"division_pagetype2": "page_type"})
    part2["site_code"] = part2["site_code"].apply(normalize_site_code)
    part2 = part2[["origin_breakdown", "site_code", "page_type", "value"]]

    # ── tr: part1 + part2 (part2는 'TOTAL%' 제외) ──────────────────
    part2 = part2[~part2["page_type"].str.startswith("TOTAL", na=False)]
    tr = pd.concat([part1, part2], ignore_index=True)

    # ── 최종 출력 (TIER/SUBS/COUNTRY 빈 칼럼) ──────────────────────
    tr["TIER"] = ""
    tr["SUBS"] = ""
    tr["COUNTRY"] = ""
    tr = tr.rename(columns={"site_code": "SITE CODE", "page_type": "PAGE TYPE",
                            "origin_breakdown": "Origin_page_type", "value": "VALUE"})

    tr["CATEGORY"] = tr.apply(
        lambda r: get_category(r["PAGE TYPE"], r["SITE CODE"]), axis=1
    )
    tr["VALUE_TYPE"] = tr.apply(
        lambda r: get_value_type(r["PAGE TYPE"], r["SITE CODE"]), axis=1
    )

    final_cols = ["TIER", "SUBS", "COUNTRY", "SITE CODE",
                  "CATEGORY", "PAGE TYPE", "Origin_page_type", "VALUE", "VALUE_TYPE"]

    result = tr[final_cols].drop_duplicates()
    result = result[result["VALUE"] > 0]

    out_path = EXPORTS_DIR / OUTPUT_NAME
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n저장: {out_path.name}  ({len(result):,}행)")


if __name__ == "__main__":
    main()
