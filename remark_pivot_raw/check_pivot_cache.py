# check_pivot_cache.py
# 2026-06-23  Jonghyun Park w/ Claude
#
# 목적: xlsx 피봇 캐시 진단 (읽기 전용 — 파일 미수정)
#   ▸ 각 피봇 캐시의 CLASSIC / OLAP 엔진 판별
#   ▸ 캐시 안 dimension 값(site code / subs / country / channel / region) 추출 + _fx 미리보기
#   실제 마스킹(파일 변환)은 remark_classic.py / remark_olap.py 가 수행.
#   이 도구는 그 전에 "어느 시트가 CLASSIC/OLAP인지 / 캐시에 어떤 값이 있고 어떻게 마스킹될지" 확인용.
#
# ▸ CLASSIC 피봇 → source_path = sheet://소스시트명
#   피봇 캐시 sharedItems 에서 dimension 값 직접 추출
#
# ▸ OLAP 피봇   → source_path = model://테이블/계층/레벨  (MDX 경로 파싱)
#   sharedItems 멤버 경로 끝의 &[값] 을 추출해 _fx 처리
#
# 출력: remark_olap.csv / remark_classic.csv 형태 (원본칼럼 | 칼럼_fx 쌍)
#       remark_prefix.csv (토큰 레전드)

import os, re, zipfile, csv, random
import xml.etree.ElementTree as ET

# ════ 사용자가 바꿔야 하는 부분 ════

# 진단할 원본 xlsx (마스킹 전 파일). 안 쓰는 쪽은 "" 로 두면 skip.
OLAP_XLSX    = r"C:\Users\user_name\Downloads\2026 campaign_name Performance Analysis.xlsx"          # OLAP 원본 → remark_olap.csv
CLASSIC_XLSX = r"C:\Users\user_name\Downloads\2026 CAMPAIGN NAME Campaign Performance Analysis.xlsx"  # Classic 원본 → remark_classic.csv
OUTPUT_DIR   = r"C:\Users\user_name\OneDrive - company_name\user_id\path\to\output"

# 리마킹 대상 dimension 키워드 (필드명 소문자 포함 여부로 판단)
# MDX 경로의 계층/레벨 이름에도 동일하게 적용
REMARK_DIMS = [
    "site_code", "site",
    "subs",
    "country",
    "channel",
    "region",
]

# CLASSIC/OLAP source prefix
CLASSIC_PREFIX = "sheet"    # sheet://소스시트명
OLAP_PREFIX    = "model"    # model://테이블/계층/레벨

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
    """알파 토큰 단위 일관 치환. 비알파 구분자 그대로. 숫자는 그대로."""
    if val is None:
        return ""
    s = str(val)
    try:
        float(s); return s
    except (ValueError, TypeError):
        pass
    return "".join(
        _mask_token(p) if re.match(r"^[A-Za-z]+$", p) else p
        for p in re.split(r"([^A-Za-z]+)", s)
    )

def is_remark_dim(name: str) -> bool:
    low = name.lower().replace("_", " ").replace("-", " ")
    return any(kw.replace("_", " ") in low for kw in REMARK_DIMS)

def parse_mdx_path(mdx: str):
    """
    '[d_country].[Country Profile].[country]'
    → ('d_country', 'Country Profile', 'country')
    """
    parts = re.findall(r"\[([^\]]+)\]", mdx)
    return tuple(parts) if parts else (mdx,)

def parse_mdx_member_value(member: str) -> str:
    """
    '[d_country].[Country Profile].[tier].&[1].&[Region].&[CODE].&[Country]'
    → 마지막 &[값] 추출 → 'Country'
    """
    vals = re.findall(r"&\[([^\]]+)\]", member)
    return vals[-1] if vals else ""

# ─── XML 유틸 ───
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
SS_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

def etag(local): return f"{{{SS_NS}}}{local}"

def read_xml(z, path):
    return ET.fromstring(z.read(path).decode("utf-8"))

# ─── 캐시 분석 ───
def analyze_caches(z, names, wb_root, rid_to_target) -> dict:
    cache_map = {}
    pc_el = wb_root.find(f"{{{SS_NS}}}pivotCaches")
    if pc_el is None:
        return cache_map

    for pc in pc_el:
        cid = pc.get("cacheId")
        rid = pc.get(RID)
        target = rid_to_target.get(rid, "")
        full = f"xl/{target}"
        if full not in names:
            continue
        def_txt = z.read(full).decode("utf-8")
        def_root = ET.fromstring(def_txt)

        is_classic = 'cacheSource type="worksheet"' in def_txt
        is_olap    = 'cacheSource type="external"'  in def_txt

        src_sheet = ""
        if is_classic:
            ws = def_root.find(f".//{{{SS_NS}}}worksheetSource")
            src_sheet = ws.get("sheet", "") if ws is not None else ""

        m = re.search(r'recordCount="(\d+)"', def_txt)
        records = int(m.group(1)) if m else 0

        ctype = "CLASSIC" if is_classic else ("OLAP" if is_olap else "?")

        dims = {}
        for cf in def_root.findall(f".//{{{SS_NS}}}cacheField"):
            fname = cf.get("name", "")
            si_el = cf.find(f"{{{SS_NS}}}sharedItems")

            if ctype == "CLASSIC":
                if not is_remark_dim(fname):
                    continue
                values = []
                if si_el is not None:
                    for child in si_el:
                        v = child.get("v") or child.get("n") or ""
                        if v:
                            values.append(v)
                key = fname
                sp  = f"{CLASSIC_PREFIX}://{src_sheet}/{fname}"

            elif ctype == "OLAP":
                parts = parse_mdx_path(fname)
                level = parts[-1] if parts else fname
                if not is_remark_dim(level):
                    continue
                values = []
                if si_el is not None:
                    for child in si_el:
                        raw_member = child.get("n") or child.get("v") or ""
                        val = parse_mdx_member_value(raw_member)
                        if val:
                            values.append(val)
                table  = parts[0] if len(parts) > 0 else "model"
                hier   = parts[1] if len(parts) > 1 else ""
                level  = parts[2] if len(parts) > 2 else parts[-1]
                key = f"{table}/{level}"
                sp  = f"{OLAP_PREFIX}://{table}/{hier}/{level}"

            else:
                continue

            uniq = sorted(set(v for v in values if v))
            if key in dims:
                dims[key]["values"] = sorted(set(dims[key]["values"] + uniq))
            else:
                dims[key] = {"source_path": sp, "values": uniq}

        cache_map[cid] = {
            "type": ctype, "records": records,
            "source_sheet": src_sheet, "dims": dims,
        }

    return cache_map

# ─── 피봇 테이블 → cacheId 매핑 ───
def pivot_to_cache_map(z, names) -> dict:
    pt_cid = {}
    for n in names:
        if "xl/pivotTables/pivotTable" in n and n.endswith(".xml"):
            try:
                txt = z.read(n).decode("utf-8")
                m = re.search(r'cacheId="(\d+)"', txt)
                if m:
                    pt_cid[os.path.basename(n)] = m.group(1)
            except Exception:
                pass
    return pt_cid

# ─── 시트 → pivot 파일 매핑 ───
def sheet_pivot_map(z, names, wb_root, rid_to_target) -> dict:
    sheet_rid_to_file = {rid: tgt for rid, tgt in rid_to_target.items()
                         if "worksheets/sheet" in tgt}
    result = {}
    sheets_el = wb_root.find(f"{{{SS_NS}}}sheets")
    if sheets_el is None:
        return result
    for s in sheets_el:
        sname = s.get("name", "")
        rid = s.get(RID)
        sfile = sheet_rid_to_file.get(rid, "")
        if not sfile:
            continue
        sbase = os.path.basename(sfile)
        rels_path = f"xl/worksheets/_rels/{sbase}.rels"
        if rels_path not in names:
            continue
        srels = read_xml(z, rels_path)
        pts = [r.get("Target", "") for r in srels if "pivotTable" in r.get("Target", "")]
        if pts:
            result[sname] = [os.path.basename(p) for p in pts]
    return result

# ─── 메인 ───
def remark_xlsx(xlsx_path: str, out_name: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\nProcessing: {os.path.basename(xlsx_path)}")

    with zipfile.ZipFile(xlsx_path, "r") as z:
        names = set(z.namelist())
        wb_root   = ET.fromstring(z.read("xl/workbook.xml").decode("utf-8"))
        rels_root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels").decode("utf-8"))
        rid_to_target = {r.get("Id"): r.get("Target", "") for r in rels_root}

        cache_map  = analyze_caches(z, names, wb_root, rid_to_target)
        pt_cid_map = pivot_to_cache_map(z, names)
        sp_map     = sheet_pivot_map(z, names, wb_root, rid_to_target)

    used_cids = set()
    for sname, pts in sp_map.items():
        for pt in pts:
            cid = pt_cid_map.get(pt)
            if cid:
                used_cids.add(cid)

    # ── 피봇 테이블 수 집계 (엔진별) ──
    pivot_engine = {"CLASSIC": 0, "OLAP": 0, "?": 0}
    for pt, cid in pt_cid_map.items():
        ctype = cache_map.get(cid, {}).get("type", "?")
        pivot_engine[ctype] = pivot_engine.get(ctype, 0) + 1
    print(f"  Pivot tables: total={len(pt_cid_map)}  "
          f"CLASSIC={pivot_engine['CLASSIC']}  OLAP={pivot_engine['OLAP']}  ?={pivot_engine['?']}")

    dim_merged: dict = {}
    for cid in used_cids:
        ci = cache_map.get(cid, {})
        ctype = ci.get("type", "?")
        for dim_key, dinfo in ci.get("dims", {}).items():
            if dim_key not in dim_merged:
                dim_merged[dim_key] = {
                    "source_path": dinfo["source_path"],
                    "type": ctype,
                    "values": set(),
                }
            dim_merged[dim_key]["values"].update(dinfo["values"])

    out_path = os.path.join(OUTPUT_DIR, out_name)
    rows_written = 0
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["source_path", "dim_key", "Value", "Value_fx", "cache_type"])
        w.writeheader()
        for dk in sorted(dim_merged):
            dinfo = dim_merged[dk]
            for val in sorted(dinfo["values"]):
                w.writerow({
                    "source_path": dinfo["source_path"],
                    "dim_key":     dk,
                    "Value":       val,
                    "Value_fx":    fx(val),
                    "cache_type":  dinfo["type"],
                })
                rows_written += 1

    print(f"  Dims found: {list(dim_merged)}")
    print(f"  Rows: {rows_written}  → {out_path}")
    return dim_merged


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # OLAP 피봇 캐시 진단
    if OLAP_XLSX and os.path.exists(OLAP_XLSX):
        olap_dims = remark_xlsx(OLAP_XLSX, "remark_olap.csv")
    else:
        print(f"\nOLAP xlsx not set/found, skipping: {OLAP_XLSX}")
        olap_dims = {}

    # Classic 피봇 캐시 진단
    if CLASSIC_XLSX and os.path.exists(CLASSIC_XLSX):
        classic_dims = remark_xlsx(CLASSIC_XLSX, "remark_classic.csv")
    else:
        print(f"\nClassic xlsx not set/found, skipping: {CLASSIC_XLSX}")
        classic_dims = {}

    # prefix 레전드 (전체 사용된 토큰)
    prefix_path = os.path.join(OUTPUT_DIR, "remark_prefix.csv")
    with open(prefix_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["Token_Original", "Token_fx"])
        w.writeheader()
        for orig in sorted(_CACHE, key=str.lower):
            w.writerow({"Token_Original": orig, "Token_fx": _CACHE[orig]})
    print(f"\nPrefix legend: {prefix_path}  ({len(_CACHE)} tokens)")

    print("\nOutput files:")
    print(f"  {OUTPUT_DIR}/remark_olap.csv    (OLAP dimension 값 _fx)")
    print(f"  {OUTPUT_DIR}/remark_classic.csv (Classic dimension 값 _fx)")
    print(f"  {OUTPUT_DIR}/remark_prefix.csv  (토큰 레전드)")


if __name__ == "__main__":
    main()
