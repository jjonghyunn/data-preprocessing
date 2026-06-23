# remark_olap.py
# 2026-06-23  Jonghyun Park w/ Claude
#
# ▣ OLAP(파워피봇 데이터 모델) 피봇용 리마킹 도구
#   OLAP 피봇 xlsx 는 openpyxl 로 저장 시 깨지므로 xlsx 를 직접 못 건드린다.
#   대신 데이터 모델의 소스인 data/ 폴더의 dim/fact CSV 를 리마킹해서
#   data_fx/ 로 출력 → Excel 에서 데이터 모델 소스를 data_fx/ 로 다시 로드.
#   (Classic 피봇 xlsx 는 remark_classic.py 로 셀 직접 치환)
#
# remark_pivot.py 와 동일 SEED=<REMARK_SEED> cipher (토큰 일관성 유지)
#
# 리마킹 방식: 지정 컬럼의 값을 _fx 로 in-place 교체 (컬럼명 유지, 값만 치환)
# 숫자·날짜 컬럼은 그대로. 알파 토큰만 치환(비알파 구분자 유지).

import os, re, csv, random
from pathlib import Path

# ════ 사용자가 바꿔야 하는 부분 ════

INPUT_DIR  = r"C:\Users\user_name\Downloads\data"
OUTPUT_DIR = r"C:\Users\user_name\Downloads\data_fx"

# ─── dim 테이블 리마킹 컬럼 ───
# 키 = 파일명, 값 = 리마킹 대상 컬럼 리스트
DIM_REMARK = {
    "d_country.csv":  ["sitecode", "region", "subs", "country"],
    "d_channel.csv":  ["site", "channel_source", "channel_unified"],
    "d_device.csv":   [],       # Total/Web/PC 등 — 일반 용어, 불필요
    "d_schedule.csv": ["sitecode"],
}

# ─── fact 테이블 리마킹 컬럼 ───
# 키 = 파일명 패턴(startswith), 값 = 리마킹 대상 컬럼 리스트
FACT_REMARK = {
    "basic_traffic":  ["sitecode",
                    #    "SegmentName", "SegmentId"
                    ],
    "external":       ["sitecode", "variables/marketingchannel"],
    "internal":       ["sitecode", "channel",
                    #    "SegmentName", "SegmentId"
                       ],
    "adhoc":          ["sitecode",
                    #    "SegmentName", "SegmentId"
                       ],
    "order":          ["sitecode",
                    #    "SegmentName", "SegmentId"
                       ],
    "shop_traffic":   ["sitecode",
                    #    "SegmentName", "SegmentId",
                       "division"],
    "best_selling":   ["sitecode", "division",
                    #    "category",
                    #    "variables/product"
                       ],
    "nextpage":       ["sitecode", "division",
                    #    "variables/prop6"
                       ],
    "cross_sell":     ["sitecode",
                    #    "SegmentName", "SegmentId",
                    #    "div_1", "div_2", "div_3"
                       ],
    "multi_purchase": ["sitecode",
                    #    "category",
                    #    "variables/evar41"
                       ],
}

# ════ 내부 사용 ════

SEED = <REMARK_SEED>

def _make_cipher(seed=SEED):
    rng = random.Random(seed)
    lower = list("abcdefghijklmnopqrstuvwxyz")
    shuffled = lower[:]
    while any(shuffled[i] == lower[i] for i in range(len(lower))):
        rng.shuffle(shuffled)
    return {c: s for c, s in zip(lower, shuffled)}

_LOWER_MAP = _make_cipher()
_UPPER_MAP  = {c.upper(): v.upper() for c, v in _LOWER_MAP.items()}
_CHAR_MAP   = {**_LOWER_MAP, **_UPPER_MAP}
_CACHE: dict = {}

def _mask_token(tok: str) -> str:
    if tok not in _CACHE:
        _CACHE[tok] = "".join(_CHAR_MAP.get(c, c) for c in tok)
    return _CACHE[tok]

def fx(val) -> str:
    if val is None or val == "":
        return val
    s = str(val)
    try:
        float(s)
        return s
    except (ValueError, TypeError):
        pass
    return "".join(
        _mask_token(p) if re.match(r"^[A-Za-z]+$", p) else p
        for p in re.split(r"([^A-Za-z]+)", s)
    )

def remark_csv(src: Path, dst: Path, remark_cols: list):
    if not remark_cols:
        # 리마킹 불필요 — 원본 그대로 복사
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        return 0

    rows_processed = 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "r", encoding="utf-8-sig", newline="") as fin, \
         open(dst, "w", encoding="utf-8-sig", newline="") as fout:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames or []
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            for col in remark_cols:
                if col in row:
                    row[col] = fx(row[col])
            writer.writerow(row)
            rows_processed += 1
    return rows_processed

def get_fact_remark_cols(fname: str) -> list:
    for pattern, cols in FACT_REMARK.items():
        if fname.startswith(pattern):
            return cols
    return []

def main():
    in_root  = Path(INPUT_DIR)
    out_root = Path(OUTPUT_DIR)
    out_root.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    total_files = 0

    # ── dim 테이블 ──
    print("── dim ──")
    dim_in  = in_root  / "dim"
    dim_out = out_root / "dim"
    for f in sorted(dim_in.iterdir()):
        if f.suffix.lower() != ".csv":
            # xlsx 등 비-CSV는 그대로 복사
            (dim_out / f.name).parent.mkdir(parents=True, exist_ok=True)
            (dim_out / f.name).write_bytes(f.read_bytes())
            print(f"  {f.name}  (copy as-is)")
            continue
        cols = DIM_REMARK.get(f.name, [])
        dst  = dim_out / f.name
        rows = remark_csv(f, dst, cols)
        print(f"  {f.name}  remark={cols}  rows={rows}")
        total_rows  += rows
        total_files += 1

    # ── fact 테이블 ──
    print("\n── fact ──")
    fact_in  = in_root  / "fact"
    fact_out = out_root / "fact"
    for f in sorted(fact_in.iterdir()):
        if f.suffix.lower() != ".csv":
            continue
        cols = get_fact_remark_cols(f.name)
        dst  = fact_out / f.name
        rows = remark_csv(f, dst, cols)
        print(f"  {f.name}  remark={cols}  rows={rows}")
        total_rows  += rows
        total_files += 1

    # ── 레전드 CSV ──
    legend_path = out_root / "remark_prefix.csv"
    with open(legend_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["Token_Original", "Token_fx"])
        w.writeheader()
        for orig in sorted(_CACHE, key=str.lower):
            w.writerow({"Token_Original": orig, "Token_fx": _CACHE[orig]})
    print(f"\nLegend: {legend_path}  ({len(_CACHE)} tokens)")
    print(f"\nDone. {total_files} files, {total_rows:,} rows → {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
