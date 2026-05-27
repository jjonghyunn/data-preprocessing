# RESHAPE_multipurchase_260428.py
# 2026-04-28  Jonghyun Park w/ Claude
# multipurchase SQL (multipurchase_260212 ... (offer예외추가).sql) Python 포팅
#
# 3개 기간 동시 처리 (last는 prefix 패턴만 가정):
#   - this year:   value1~3 = campaign_total_multiorder_(unit/order/revenue)
#                  value4~6 = scom_total_multiorder_(unit/order/revenue)
#   - prior:       value1~3 = campaign_prior_total_multiorder_(unit/order/revenue)
#                  value4~6 = scom_prior_total_multiorder_(unit/order/revenue)
#   - last:        last_* prefix 가정, 구조는 this year와 동일
#
# 출력:
#   - 3개 분리:  {prefix}_stacked_separate.csv
#   - 1개 통합:  multipurchase_stacked_separate_union.csv
#
# campaign_tier 조인 제외 → TIER/SUBS/COUNTRY 빈 칼럼

from pathlib import Path
import re
import pandas as pd

# ── 경로 설정 ──────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent       # launch/multipurchase/
LAUNCH_DIR   = SCRIPT_DIR.parent           # launch/
ROOT_DIR     = LAUNCH_DIR.parent           # AA_Exporter_260304/
EXPORTS_DIR  = ROOT_DIR / "aa_exports"
CURRENCY_CSV = ROOT_DIR / "ref" / "currency.csv"

# ── 처리 대상: (prefix, PERIOD 라벨, 환율 연도, 출력 STANDARD 리스트) ──
# STANDARD 리스트 변경 가이드:
#   - 기본: this year/last year는 ["S.com", "Campaign"], prior는 ["S.com"]
#   - prior에도 Campaign이 필요하면: ["S.com", "Campaign"]로 바꾸고 PERIOD 라벨에서 "(S.com Only)" 제거
#   - S.com만 필요하면: ["S.com"]로 바꾸고 PERIOD 라벨 끝에 " (S.com Only)" 추가
TB_KEYS = [
    ("multi_purchase",        "Campaign Period",                        "2026", ["S.com", "Campaign"]),
    ("multi_purchase_prior",  "Prior Period (S.com Only)",              "2026", ["S.com"]),
    ("last_multi_purchase",   "Last Year Campaign Period",              "2025", ["S.com", "Campaign"]),
]

OUTPUT_UNION_NAME = "multi_purchase_stacked_separate_union.csv"

# ── 타임스탬프 패턴 (HHMM 4자리 또는 HHMMSS 6자리 모두 지원) ───────
_TS_PAT = re.compile(r"_(\d{8})_(\d{4,6})$")


def _ts_sort_key(path: Path) -> str:
    """타임스탬프 정렬 키. HHMM은 6자리로 zero-pad해서 HHMMSS와 섞여도 정상 정렬.
       예) 1234 → 123400  (HH:MM:SS = 12:34:00 가정)
    """
    m = _TS_PAT.search(path.stem)
    return m.group(1) + m.group(2).ljust(6, "0")


# ── SITE CODE 정규화 (SQL: before_last CTE) ────────────────────────
def normalize_site_code(sc: str) -> str:
    s = str(sc).strip().lower()
    if s == "ku":
        return "IQ_KU"
    if s == "uk_epp":
        return "UK"
    return s.upper()


# ── 카테고리 분류 (SQL: plus_category CTE) ─────────────────────────
# best_selling과 거의 동일하지만 차이점:
#   1) 예외(SM-M1000QW 등) → "X"가 아니라 None 반환
#   2) "-OFFER" 포함 시 None (SQL: `like '%-OFFER%' then null`)
#   3) 스페인어 displayname fallthrough 없음
def get_category(v):
    if pd.isna(v):
        return None
    u = str(v).upper().strip()
    if not u:
        return None

    # 예외 → null (SQL: then null)
    if (u == "SM-M1000QW" or u.startswith("RS-CN") or u.startswith("LUMAFU") or
            u.startswith("ARCSITE") or u == "UNSPECIFIED" or u == "UNDEFINED" or
            u.startswith("AW-EW") or u.startswith("AC-TC") or u.startswith("NL-") or
            u.startswith("MLT") or u.startswith("VCA-") or u.startswith("DV-") or
            u.startswith("WA-TC") or u.startswith("DW-") or u.startswith("AF-") or
            u.startswith("DF-") or u.startswith("RF-TC") or u.startswith("APL-") or
            u.startswith("WF-") or u.startswith("WT-") or u.startswith("SC-WATCH") or
            u.startswith("SC1TAB") or u.startswith("WATCHES-IFIT") or u == "BUDS"):
        return None

    # -OFFER% 예외 → null (multipurchase 전용 추가 예외)
    if "-OFFER" in u:
        return None

    # SMP
    if (u.startswith("SM-S") or u.startswith("SM-G") or u.startswith("SM-A") or
            u.startswith("SM-F") or u.startswith("SM-M") or u.startswith("SM-E") or
            u.startswith("SM5") or u.startswith("SM-W") or u.startswith("SM-N") or
            u.startswith("SM-5")):
        return "SMP"

    # Tablet
    if u.startswith("SM-X") or u.startswith("SM-P") or u.startswith("SM-T"):
        return "Tablet"

    # NPC
    if u.startswith("NT") or u.startswith("NP") or u.startswith("XE"):
        return "NPC"

    # Wearable
    if (u.startswith("SM-R") or u.startswith("SM-Q") or u.startswith("SM-L") or
            u.startswith("L325N") or u.startswith("L705N") or u.startswith("L330N") or
            u.startswith("L500N") or u.startswith("GALAXYWATCH") or u.startswith("SM-I")):
        return "Wearable"

    # ACC (GP%의 -OFFER 예외는 위에서 이미 처리됨)
    if (u.startswith("ET") or u.startswith("EF") or u.startswith("GP") or
            u.startswith("EI") or u.startswith("EE") or u.startswith("EB") or
            u.startswith("EJ") or u.startswith("EP") or u.startswith("EO") or
            u.startswith("WMN") or u.startswith("CFX") or u.startswith("MA") or
            u.startswith("RA") or u.startswith("VCA") or u.startswith("SKK")):
        return "ACC"

    # TV
    if (u.startswith("KQ") or u.startswith("QA") or u.startswith("GQ") or
            u.startswith("QE") or u.startswith("QN") or u.startswith("TQ") or
            u.startswith("UN") or u.startswith("UA") or u.startswith("UE") or
            u.startswith("KU") or u.startswith("43LS") or u.startswith("50LS") or
            u.startswith("65LS") or u.startswith("43CUE") or u.startswith("55CUE") or
            u.startswith("65S") or u.startswith("SP-LSP") or u.startswith("SP-LSTP") or
            u.startswith("32T") or u.startswith("43D") or u.startswith("43Q") or
            u.startswith("43T") or u.startswith("50D") or u.startswith("50Q") or
            u.startswith("55D") or u.startswith("55LS") or u.startswith("55Q") or
            u.startswith("55S") or u.startswith("65D") or u.startswith("65Q") or
            u.startswith("75D") or u.startswith("75Q") or u.startswith("SP-LFF") or
            u.startswith("SP-L") or u.startswith("TU3") or u.startswith("TU4") or
            u.startswith("TU5") or u.startswith("TU6") or u.startswith("TU7") or
            u.startswith("TU8") or u.startswith("TU9") or u.startswith("GU") or
            u.startswith("55U") or u.startswith("43F") or u.startswith("32H") or
            u.startswith("65U") or u.startswith("43U") or u.startswith("UD8") or
            u.startswith("UD7") or u.startswith("MRE1") or u.startswith("F-32") or
            u.startswith("LH") or u.startswith("HG")):
        return "TV"

    # Monitor
    if (u.startswith("LS") or u.startswith("LF") or u.startswith("LT") or
            u.startswith("LU") or u.startswith("LV") or u.startswith("LC") or
            u.startswith("C24") or u.startswith("C27") or u.startswith("C32") or
            u.startswith("C34") or u.startswith("F22") or u.startswith("S2") or
            u.startswith("S3") or u.startswith("S40") or u.startswith("S43") or
            u.startswith("S49") or u.startswith("S5") or u.startswith("TU2") or
            u.startswith("U32") or u.startswith("F24") or u.startswith("F27")):
        return "Monitor"

    # Sound Bar
    if (u.startswith("HW-Q") or u.startswith("HW-S") or u.startswith("HW-A") or
            u.startswith("HW-B") or u.startswith("HW-C") or u.startswith("HW-LS") or
            u.startswith("HW-T")):
        return "Sound Bar"

    # AC
    if (u.startswith("AF") or u.startswith("AC") or u.startswith("AR") or
            u.startswith("AJ") or u.startswith("AM") or u.startswith("AW") or
            u.startswith("PC1") or u.startswith("AN") or u.startswith("KFR-")):
        return "AC"

    # Air Purifier
    if u.startswith("AX") or u.startswith("AY") or u.startswith("AP"):
        return "Air Purifier"

    # Washer
    if (u.startswith("WW") or u.startswith("WA") or u.startswith("WV") or
            u.startswith("WD") or u.startswith("WF") or u.startswith("WR") or
            u.startswith("WH") or u.startswith("WT")):
        return "Washer"

    if u.startswith("DV"):
        return "Dryer"
    if u.startswith("DF"):
        return "Air Dresser"
    if u.startswith("DJ"):
        return "Shoe Dresser"

    # REF
    if (u.startswith("RF") or u.startswith("RB") or u.startswith("RL") or
            u.startswith("RQ") or u.startswith("RR") or u.startswith("RS") or
            u.startswith("RT") or u.startswith("RW") or u.startswith("RZ") or
            u.startswith("RH") or u.startswith("RP") or u.startswith("RM") or
            u.startswith("BR") or u.startswith("RK70") or u.startswith("RK80")):
        return "REF"

    # VC
    if (u.startswith("VR") or u.startswith("VS") or u.startswith("VC") or
            u.startswith("SC") or u.startswith("SS60K")):
        return "VC"

    # Cooking
    if (u.startswith("ME") or u.startswith("MJ") or u.startswith("ML") or
            u.startswith("MM") or u.startswith("MQ") or u.startswith("MW") or
            u.startswith("NA") or u.startswith("NE") or u.startswith("NK") or
            u.startswith("NL") or u.startswith("NQ") or u.startswith("NV") or
            u.startswith("NW") or u.startswith("NX") or u.startswith("NY") or
            u.startswith("NZ") or u.startswith("MC") or u.startswith("MG") or
            u.startswith("MO") or u.startswith("MS") or u.startswith("NS") or
            u.startswith("CC") or u.startswith("CTR") or u.startswith("C21RJAN") or
            u.startswith("NB69") or u.startswith("C61R") or u.startswith("SANK")):
        return "Cooking"

    if u.startswith("DW"):
        return "DW"

    # AUDIO
    if u.startswith("JBL") or u.startswith("HK"):
        return "AUDIO"

    # BUNDLE
    if (u.startswith("F-9") or u.startswith("F-55") or u.startswith("F-65") or
            u.startswith("F-80") or u.startswith("F-AR") or u.startswith("F-A") or
            u.startswith("F-F7") or u.startswith("F-M") or u.startswith("F-S7") or
            u.startswith("F-S9") or u.startswith("F-X") or u.startswith("F-NP") or
            u.startswith("F-58") or u.startswith("F-70") or u.startswith("F-75") or
            u.startswith("F-85") or u.startswith("F-LS") or u.startswith("F-Q") or
            u.startswith("F-UN") or u.startswith("F-3X") or u.startswith("F-09") or
            u.startswith("F-18") or u.startswith("F-2X") or u.startswith("F-CAC") or
            u.startswith("F-FJM") or u.startswith("F-W") or u.startswith("F-12") or
            u.startswith("F-NK") or u.startswith("F-RS") or u.startswith("PACKGE")):
        return "BUNDLE"

    return None  # SQL: else null


# ── breakdown(value) → 카테고리 집계 ──────────────────────────────
# SQL의 split_seed/exploded/group_concat 부분을 한 함수로 압축.
# breakdown이 "SM-F766B,SM-L505F" 같은 쉼표 구분 문자열이라고 가정.
def aggregate_categories(breakdown: str) -> tuple[str, str]:
    """반환: (CATEGORIES ORIGIN, CATEGORY)
       CATEGORIES ORIGIN: pos 순서대로 ',' 조인 (null 카테고리 제외 — SQL group_concat 동작)
       CATEGORY:          ACC 제외 + 카테고리명 알파벳순 ', ' 조인
    """
    if pd.isna(breakdown):
        return ("", "")
    parts = [p.strip() for p in str(breakdown).split(",")]
    parts = [p for p in parts if p]   # 공백 제거 (SQL: trim(replace ...) <> '')
    cats_in_pos_order = [get_category(p) for p in parts]
    non_null_in_pos = [c for c in cats_in_pos_order if c is not None]
    # SQL의 group_concat ORDER BY는 MySQL utf8_general_ci(case-insensitive) 정렬과
    # 동일하게 맞추기 위해 key=str.lower 사용. (예: "Tablet" < "TV")
    non_acc_sorted  = sorted((c for c in non_null_in_pos if c != "ACC"), key=str.lower)
    return (",".join(non_null_in_pos), ", ".join(non_acc_sorted))


# ── 최신 파일 1개 선택 ─────────────────────────────────────────────
def find_latest(prefix: str) -> Path | None:
    """prefix 직후가 정확히 _YYYYMMDD_HHMM 인 파일만 매칭.

    multi_purchase가 multi_purchase_prior까지 잡지 않도록 정규식 fullmatch.
    """
    pat = re.compile(rf"^{re.escape(prefix)}_\d{{8}}_\d{{4,6}}$")
    candidates = [
        f for f in EXPORTS_DIR.glob(f"{prefix}_*.csv")
        if pat.match(f.stem)
        and "_stacked" not in f.name
        and "_long" not in f.name
        and not f.name.startswith("union_")
    ]
    if not candidates:
        return None
    return max(candidates, key=_ts_sort_key)


# ── 단일 파일 정제 ─────────────────────────────────────────────────
def process(raw_csv: Path, prefix: str, period_label: str,
            cur_df: pd.DataFrame, currency_year: str,
            standards: list[str]) -> pd.DataFrame:
    # currency.csv 연도 컬럼 자동 선택
    date_cols = [c for c in cur_df.columns if c not in ("site_code", "currency_code")]
    year_cols = [c for c in date_cols if c.startswith(currency_year)]
    if not year_cols:
        raise ValueError(f"currency.csv에서 {currency_year}년 컬럼 없음. 사용 가능: {date_cols}")
    currency_col = year_cols[0]

    print(f"\n▶ {prefix}")
    print(f"  파일: {raw_csv.name}  / 환율: {currency_col}  / STANDARD: {standards}")

    cur_map = cur_df.set_index("site_code")[currency_col].astype(float).to_dict()

    df = pd.read_csv(raw_csv, encoding="utf-8-sig")
    print(f"  원본 행수: {len(df)}")

    if "status" in df.columns:
        df = df[df["status"].astype(str).str.upper() == "OK"].copy()
        print(f"  status=OK 후: {len(df)}")

    # value1~6 숫자화
    for col in ("value1", "value2", "value3", "value4", "value5", "value6"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # breakdown(value) → CATEGORIES_ORIGIN, CATEGORY
    cats = df["value"].apply(aggregate_categories)
    df["_CATEGORIES_ORIGIN"] = cats.str[0]
    df["_CATEGORY"]          = cats.str[1]

    # SITE CODE 정규화 + 환율
    df["_SITE_CODE"] = df["Site_Code"].apply(normalize_site_code)
    df["_rate"]      = df["Site_Code"].astype(str).str.strip().str.lower().map(cur_map).fillna(1.0)

    # Campaign + S.com 행 생성 (value1~3 = Campaign, value4~6 = S.com)
    base = dict(
        PERIOD=period_label, TIER="", SUBS="", COUNTRY="",
        SUBS_=df.get("Subsidiary", ""), COUNTRY_=df.get("Country", ""),
    )
    common_cols = {
        "SITE CODE":         df["_SITE_CODE"],
        "MODEL CODE":        df["value"],
        "CATEGORY":          df["_CATEGORY"],
        "CATEGORIES ORIGIN": df["_CATEGORIES_ORIGIN"],
        "START DATE":        df.get("Start_Date", ""),
        "END DATE":          df.get("End_Date", ""),
    }

    camp = df.assign(
        STANDARD="Campaign",
        UNIT=df["value1"], **{"ORDER": df["value2"]},
        REVENUE=(df["value3"] * df["_rate"]).round(6),
        **{"REVENUE ORIGIN": df["value3"]},
        **common_cols, **base,
    )
    scom = df.assign(
        STANDARD="S.com",
        UNIT=df["value4"], **{"ORDER": df["value5"]},
        REVENUE=(df["value6"] * df["_rate"]).round(6),
        **{"REVENUE ORIGIN": df["value6"]},
        **common_cols, **base,
    )

    final_cols = ["PERIOD", "TIER", "SUBS", "COUNTRY", "SITE CODE",
                  "STANDARD", "MODEL CODE", "UNIT", "ORDER", "REVENUE",
                  "CATEGORY", "REVENUE ORIGIN", "CATEGORIES ORIGIN",
                  "START DATE", "END DATE"]

    result = pd.concat([camp[final_cols], scom[final_cols]], ignore_index=True)

    # SQL: where lst.unit > 0 and standard = 'S.com'
    before = len(result)
    result = result[result["UNIT"] > 0]
    print(f"  UNIT=0 제거: {before - len(result):,}행 → {len(result):,}행")

    before = len(result)
    result = result[result["STANDARD"].isin(standards)]
    print(f"  STANDARD 필터({standards}): {before - len(result):,}행 제거 → {len(result):,}행")

    # 분리 출력
    out_path = EXPORTS_DIR / f"{prefix}_stacked_separate.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig", float_format="%.6f")
    print(f"  저장: {out_path.name}  ({len(result):,}행)")

    return result


# ── 메인 ───────────────────────────────────────────────────────────
def main():
    cur_df = pd.read_csv(CURRENCY_CSV, encoding="utf-8-sig")
    cur_df["site_code"] = cur_df["site_code"].str.strip().str.lower()

    union_parts = []
    for prefix, period_label, currency_year, standards in TB_KEYS:
        raw_csv = find_latest(prefix)
        if raw_csv is None:
            print(f"\n⚠ {prefix}: 파일 없음, 스킵")
            continue
        part = process(raw_csv, prefix, period_label, cur_df, currency_year, standards)
        union_parts.append(part)

    # 통합 출력
    if union_parts:
        union = pd.concat(union_parts, ignore_index=True)
        out_union = EXPORTS_DIR / OUTPUT_UNION_NAME
        union.to_csv(out_union, index=False, encoding="utf-8-sig", float_format="%.6f")
        print(f"\n▶ UNION 저장: {out_union.name}  ({len(union):,}행)")

    print("\n✅ 완료")


if __name__ == "__main__":
    main()
