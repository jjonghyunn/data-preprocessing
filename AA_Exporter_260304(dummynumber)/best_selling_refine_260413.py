# best_selling_refine_260413.py
# best_selling_product_cmp raw CSV → 정제 CSV (stacked_separate)
# SQL: best selling product_260212(카테고리displayname스페인어보완).sql 기준
# 각 tb_key별 최신 파일 자동 선택 후 개별 _stacked_separate.csv 생성

from pathlib import Path
import re
import pandas as pd

# ── 경로 설정 ──────────────────────────────────────────────────────
LAUNCH_DIR   = Path(__file__).parent
ROOT_DIR     = LAUNCH_DIR.parent

EXPORTS_DIR  = ROOT_DIR / "aa_exports"
CURRENCY_CSV = ROOT_DIR / "ref" / "currency.csv"

# ── 처리할 tb_key 목록: (파일명 prefix, PERIOD, 환율 날짜 컬럼) ────
# 세 번째 값은 환율 적용 연도 → currency.csv에서 해당 연도로 시작하는 컬럼 자동 선택
#   best_selling_product       → 2026 Campaign Period  → 2026 환율
#   best_selling_product_prior → 2026 Prior Period     → 2026 환율 (같은 해)
#   last_best_selling_product  → 2025 Campaign Period  → 2025 환율
TB_KEYS = [
    ("best_selling_product",       "2026 Campaign Period", "2026"),
    ("best_selling_product_prior", "2026 Prior Period",    "2026"),
    ("last_best_selling_product",  "2025 Campaign Period", "2025"),
]

# ── 타임스탬프 패턴 ────────────────────────────────────────────────
_TS_PAT = re.compile(r"_(\d{8}_\d{4})$")


# ── SITE CODE 정규화 (SQL: before_last CTE) ────────────────────────
def normalize_site_code(sc: str) -> str:
    sc = str(sc).strip().lower()
    if sc == "ku":
        return "IQ_KU"
    if sc == "uk_epp":
        return "UK"
    return sc.upper()


# ── DIVISION 분류 (SQL: cmp_n_scom CTE) ────────────────────────────
def get_division(v: str) -> str:
    u = str(v).upper().strip()

    # exceptions → ETC
    if u.startswith("LUMAFUSION") or u.startswith("ARCSITE") or u.startswith("UNSPECIFIED"):
        return "ETC"

    # MX
    if (u.startswith("SM-S") or u.startswith("SM-G") or u.startswith("SM-A") or
            u.startswith("SM-F") or u.startswith("SM-M") or u.startswith("SM-E") or
            u.startswith("SM-W") or u.startswith("SM-X") or u.startswith("SM-P") or
            u.startswith("SM-T") or u.startswith("NT") or u.startswith("NP") or
            u.startswith("SM-R") or u.startswith("SM-Q") or u.startswith("SM-L") or
            u.startswith("F-9") or u.startswith("F-A") or u.startswith("F-F7") or
            u.startswith("F-M") or u.startswith("F-S7") or u.startswith("F-S9") or
            u.startswith("F-X") or u.startswith("F-NP") or u.startswith("L325N") or
            u.startswith("L705N") or u.startswith("L330N") or u.startswith("L500N") or
            u.startswith("SM5") or u.startswith("GALAXY WATCH") or
            u.startswith("XE5") or u.startswith("XE3")):
        return "MX"

    # VD
    if (u.startswith("GQ") or u.startswith("KQ") or u.startswith("QA") or
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
            u.startswith("LS") or u.startswith("LF") or u.startswith("LT") or
            u.startswith("LU") or u.startswith("LV") or u.startswith("LC") or
            u.startswith("HW-Q") or u.startswith("HW-S") or u.startswith("HW-A") or
            u.startswith("HW-B") or u.startswith("HW-C") or u.startswith("HW-LS") or
            u.startswith("HW-T") or u.startswith("F-55") or u.startswith("F-65") or
            u.startswith("F-80") or u.startswith("F-58") or u.startswith("F-70") or
            u.startswith("F-75") or u.startswith("F-85") or u.startswith("F-LS") or
            u.startswith("F-Q") or u.startswith("F-UN") or u.startswith("F-3X") or
            u.startswith("PACKGE") or u.startswith("S2") or u.startswith("S3") or
            u.startswith("C2") or u.startswith("C3") or u.startswith("GU32") or
            u.startswith("S49") or u.startswith("S5") or u.startswith("F22") or
            u.startswith("S43") or u.startswith("GU98") or
            (u.startswith("TU") and not u.startswith("TUNE")) or
            u.startswith("U32") or u.startswith("UD8") or u.startswith("UD7") or
            u.startswith("GU85") or u.startswith("GU55") or u.startswith("S40")):
        return "VD"

    # DA
    if (u.startswith("AF") or u.startswith("AC") or u.startswith("AR") or
            u.startswith("AJ") or u.startswith("AM") or u.startswith("AW") or
            u.startswith("AX") or u.startswith("AY") or u.startswith("WW") or
            u.startswith("WA") or u.startswith("WV") or u.startswith("WD") or
            u.startswith("WF") or u.startswith("WR") or u.startswith("WH") or
            u.startswith("WT") or u.startswith("DV") or u.startswith("DF") or
            u.startswith("DJ") or u.startswith("RB") or u.startswith("RF") or
            u.startswith("RL") or u.startswith("RQ") or u.startswith("RR") or
            u.startswith("RS") or u.startswith("RT") or u.startswith("RW") or
            u.startswith("RZ") or u.startswith("RH") or u.startswith("RP") or
            u.startswith("VR") or u.startswith("VS") or u.startswith("VC") or
            u.startswith("ME") or u.startswith("MJ") or u.startswith("ML") or
            u.startswith("MM") or u.startswith("MQ") or u.startswith("MW") or
            u.startswith("NA") or u.startswith("NE") or u.startswith("NK") or
            u.startswith("NL") or u.startswith("NQ") or u.startswith("NV") or
            u.startswith("NW") or u.startswith("NX") or u.startswith("NY") or
            u.startswith("NZ") or u.startswith("MC") or u.startswith("MG") or
            (u.startswith("MO") and not u.startswith("MONITOR")) or
            u.startswith("MS") or u.startswith("DW") or u.startswith("F-AR") or
            u.startswith("F-09") or u.startswith("F-18") or u.startswith("F-2X") or
            u.startswith("F-CAC") or u.startswith("F-FJM") or u.startswith("F-W") or
            u.startswith("F-12") or u.startswith("F-NK") or u.startswith("F-RS") or
            u.startswith("RM") or u.startswith("NS") or u.startswith("SC") or
            u.startswith("AN30") or u.startswith("BRB") or u.startswith("AP") or
            u.startswith("SFN") or u.startswith("CTR") or u.startswith("BRR") or
            u.startswith("CC80") or u.startswith("RK70") or u.startswith("RK80") or
            u.startswith("VW") or u.startswith("AS30") or u.startswith("CC9") or
            u.startswith("SRF") or u.startswith("SRL") or u.startswith("SRS")):
        return "DA"

    return "ETC"


# ── CATEGORY 분류 (SQL: plus_category CTE) ─────────────────────────
def get_category(v: str) -> str:
    u = str(v).upper().strip()

    # 예외 → X
    if (u == "SM-M1000QW" or u.startswith("RS-CN") or u.startswith("LUMAFU") or
            u.startswith("ARCSITE") or u == "UNSPECIFIED" or u == "UNDEFINED" or
            u.startswith("AW-EW") or u.startswith("AC-TC") or u.startswith("NL-") or
            u.startswith("MLT") or u.startswith("VCA-") or u.startswith("DV-") or
            u.startswith("WA-TC") or u.startswith("DW-") or u.startswith("AF-") or
            u.startswith("DF-") or u.startswith("RF-TC") or u.startswith("APL-") or
            u.startswith("WF-") or u.startswith("WT-") or u.startswith("SC-WATCH") or
            u.startswith("SC1TAB") or u.startswith("WATCHES-IFIT") or u == "BUDS"):
        return "X"

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

    # ACC
    if (u.startswith("ET") or u.startswith("EF") or u.startswith("GP") or
            u.startswith("EI") or u.startswith("EE") or u.startswith("EB") or
            u.startswith("EJ") or u.startswith("EP") or u.startswith("EO") or
            u.startswith("WMN") or u.startswith("CFX") or u.startswith("MA") or
            u.startswith("RA") or u.startswith("VCA") or u.startswith("SKK") or
            u.startswith("DF-") or u.startswith("AF-")):
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
            u.startswith("SP-L") or u.startswith("TU4") or u.startswith("TU5") or
            u.startswith("TU3") or u.startswith("TU7") or u.startswith("TU8") or
            u.startswith("TU9") or u.startswith("GU") or u.startswith("TU6") or
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
            (u.startswith("MO") and not u.startswith("MONITOR")) or
            u.startswith("MS") or u.startswith("NS") or u.startswith("CC") or
            u.startswith("CTR") or u.startswith("C21RJAN") or u.startswith("NB69") or
            u.startswith("C61R") or u.startswith("SANK")):
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

    # 스페인어 displayname 오버라이드 (prefix 미매칭 시 fallthrough)
    if "MONITOR" in u:
        return "Monitor"
    if "THE FRAME" in u:
        return "TV"
    if "EXTENSIÓN DE GARANTÍA DE 12 MESES MÁS" in u:
        return ""
    if "FUNDA" in u or "SOPORTE" in u:
        return "ACC"
    if "BUDS" in u:
        return "Wearable"
    if "CONTROL REMOTO" in u:
        return "X"
    if "AIRE ACONDICIONADO" in u:
        return "AC"
    if "SMART TV" in u:
        return "TV"
    if "REFRIGERADOR" in u:
        return "REF"
    if "AURA STUDIO" in u or "JBL LIVE 770NC" in u:
        return "AUDIO"
    if "PRE PAID" in u:
        return ""
    if "PHONE STRAP" in u:
        return "ACC"
    if "GALAXY WATCH" in u:
        return "Watch"
    if "TUNE BEAM" in u:
        return "AUDIO"
    if "메모리카드" in v:
        return "X"
    if "JBL TOUR ONE" in u:
        return "AUDIO"
    if "IN EAR CORDED EARP" in u:
        return "Wearable"
    if "REMOCON-ECO" in u or "SOLARCELL REMOTE" in u:
        return "X"

    return "ETC"


# ── 최신 파일 선택 ─────────────────────────────────────────────────
def find_latest(tb_key: str) -> Path | None:
    """tb_key에 해당하는 타임스탬프 파일 중 가장 최신 1개 반환"""
    candidates = [
        f for f in EXPORTS_DIR.glob(f"{tb_key}_*.csv")
        if _TS_PAT.search(f.stem)
        and "_stacked" not in f.name
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda f: _TS_PAT.search(f.stem).group(1))


# ── 단일 파일 정제 ─────────────────────────────────────────────────
def process(raw_csv: Path, tb_key: str, period: str, cur_df: pd.DataFrame, currency_year: str) -> None:
    # currency.csv에서 해당 연도로 시작하는 컬럼 자동 선택
    date_cols = [c for c in cur_df.columns if c not in ("site_code", "currency_code")]
    year_cols = [c for c in date_cols if c.startswith(currency_year)]
    if not year_cols:
        raise ValueError(f"currency.csv에서 {currency_year}년 컬럼 없음. 사용 가능: {date_cols}")
    currency_col = year_cols[0]   # 해당 연도 컬럼이 여러 개면 첫 번째 사용

    print(f"\n▶ {tb_key}")
    print(f"  파일: {raw_csv.name}  / 환율: {currency_col}")

    cur_map = cur_df.set_index("site_code")[currency_col].astype(float).to_dict()

    df = pd.read_csv(raw_csv, encoding="utf-8-sig")
    print(f"  원본 행수: {len(df)}")

    df = df[df["status"] == "OK"].copy()
    print(f"  status=OK 후: {len(df)}")

    for col in ["value1", "value2", "value3", "value4"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["DIVISION"]  = df["value"].apply(get_division)
    df["CATEGORY"]  = df["value"].apply(get_category)
    df["SITE CODE"] = df["Site_Code"].apply(normalize_site_code)
    df["_rate"]     = df["Site_Code"].str.strip().str.lower().map(cur_map).fillna(1.0)

    final_cols = ["PERIOD", "STANDARD", "TIER", "SUBS", "COUNTRY",
                  "SITE CODE", "DIVISION", "PRODUCT", "CATEGORY", "ORDER", "REVENUE"]

    scom = df.assign(
        PERIOD=period, STANDARD="S.com", TIER="",
        SUBS=df["Subsidiary"], COUNTRY=df["Country"], PRODUCT=df["value"],
        ORDER=df["value1"], REVENUE=(df["value2"] * df["_rate"]).round(6),
    )[final_cols]

    camp = df.assign(
        PERIOD=period, STANDARD="Campaign", TIER="",
        SUBS=df["Subsidiary"], COUNTRY=df["Country"], PRODUCT=df["value"],
        ORDER=df["value3"], REVENUE=(df["value4"] * df["_rate"]).round(6),
    )[final_cols]

    result = pd.concat([scom, camp], ignore_index=True)

    out_path = EXPORTS_DIR / f"{tb_key}_stacked_separate.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig", float_format="%.6f")
    print(f"  저장: {out_path.name}  ({len(result):,}행)")


# ── 메인 ───────────────────────────────────────────────────────────
def main():
    # 환율 CSV 로드 (공통 — 날짜 컬럼 선택은 tb_key별로)
    cur_df = pd.read_csv(CURRENCY_CSV, encoding="utf-8-sig")
    cur_df["site_code"] = cur_df["site_code"].str.strip().str.lower()

    # tb_key별 최신 파일 선택 → 정제
    for tb_key, period, currency_year in TB_KEYS:
        raw_csv = find_latest(tb_key)
        if raw_csv is None:
            print(f"\n⚠ {tb_key}: 파일 없음, 스킵")
            continue
        process(raw_csv, tb_key, period, cur_df, currency_year)

    print("\n✅ 완료")


if __name__ == "__main__":
    main()
