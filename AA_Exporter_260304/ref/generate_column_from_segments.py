# generate_column_from_segments.py
# 2026-05-12  Jonghyun Park w/ Claude
"""
extract_panel_tables_json_v2.0 가 생성한 매핑 CSV 의 (tb / segments / metric / panel / period)
컬럼만 보고 union KEY 형식의 column 값을 algorithmic 하게 재구성.

union KEY 8 토큰 표준 포맷:
    {section}_{scope}_{year}_{context}_{device}_{measure}_{login}_{item}

components:
  · section  — tb 의 1_1 / 0_1 / 4_2 등 numeric prefix
  · scope    — 0_1 카테고리는 da/mx/vd, 그 외는 all
  · year     — 2025 (period=last) / 2026 (campaign or prior)
  · context  — tb 토큰 cmp/scom 우선, 4_x 는 segments 의 campaign segment 보고 결정 (+_prior 변형)
  · device   — pc / mobile / app / android / ios / web / total (segments 의 device segment 토큰)
               · 'Excluded APP' 만 있고 device 토큰 없음 → 'web'
  · measure  — visit-base section (1_1/0_1/0_2/1_2/2_1/2_3/4_1) → 항상 'visit'
               order-base section (4_2/4_3/5_x) → metric 따라 'order'/'revenue'
               그 외 → metric 단수형 (entry/bounce/pageview 등)
  · login    — 같은 tb 안에 logged in/out segment 있는 row 가 하나라도 있으면 그 tb 전체가
               logged-cross-tab. row 의 segments 보고 'login' / 'logout' / 'total'
               그 외 모든 tb → 'null'
  · item     — section 별 다양한 룰 (아래 참조)

ITEM 자리 룰 (section 별):
  · visit-base 일반 (1_1/0_2/0_1 등): metric 단수형 (visit / uniquevisitor / pageview / ...)
    · No Data segment 가 있는 row → '{metric}_nodata' (C열 unique key 보장)
  · 2_1: Internal_* segment 의 union 축약 슬러그 (internal_gnb / internal_pf 등)
  · 2_3 (homepage KV/GNB to cmp):
    · Internal_* 있음 → '<internal_뒤_슬러그>_tocmp' (home_kv_tocmp 등)
    · 없음 → 'home{metric}' (homevisit)
  · 4_2: 'Campaign Page > PD Visit (All Products)' → 'main_then_pd_all' 류 cell 별칭
  · 4_3: default 'scom_and_order_all' (+ '_rev' if revenue) / Unit>=2 → 'scom_multiorder'
  · 5_1/5_2/5_3 cross-sell: '<line>_{multiorder|order|cmporder}'
    · line: total / mx / vd / da / mx_vd 등 (excluded 패턴 + individual MX/VD/DA Order segments 로 결정)
    · campaign segment 있음 → line='campaign'
    · 그 외 → line='scom' (default)
    · tb 이름에 'multi_order' 토큰 → 항상 multiorder
    · 그 외 (5_2 등): Unit>=2 있음 → multiorder, 없음 → order
    · context=cmp + line=campaign → 중복 회피로 'cmporder' 만
  · 6_0: '6_0_<scope>_<year>_<context>_<internal_slug>_<metric>' (7 토큰 특수)
  · 6_1~6_4 (marketingchannel dimension): trailing '_' (item 자리 빈 채로)
  · special tb (best_selling / multi_purchase / next_page): 'nodata_<tb>_<value_n>' placeholder

출력: `<NEW>_built.csv` (column 자동 채움)
       FILLED_CSV 존재 시 'match_filled' (일치/불일치/미해석) + 'diff_field' (불일치 시 어느 필드)
       두 컬럼 추가 → spreadsheet 분석 편의.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

# 입력 — extract_panel_tables_json_v2.0.py 가 생성한 신버전 매핑 CSV (segments + metric 컬럼 포함)
NEW_CSV = Path(r"C:\path\to\your\ref\tb_column_name_mapping_YYMMDD_HHMM.csv")
# (선택) similarity 기반 채움 결과 — 있으면 'match_filled' / 'diff_field' 컬럼 추가
FILLED_CSV = NEW_CSV.with_name(NEW_CSV.stem + "_filled.csv")
# 출력 — column 자동 채움 + 비교 컬럼
OUT_CSV = NEW_CSV.with_name(NEW_CSV.stem + "_built.csv")


# ─── tb prefix 분해 ────────────────────────────────────────────────
def _strip_tb_prefixes(tb: str) -> tuple[str, bool, bool, bool]:
    """tb 에서 us_/last_ prefix 와 _prior suffix 떼고 core 만 반환.
    returns (core_tb, is_us, is_last, is_prior).
    """
    s = tb
    is_us = s.startswith("us_")
    if is_us:
        s = s[3:]
    is_last = s.startswith("last_")
    if is_last:
        s = s[5:]
    is_prior = s.endswith("_prior")
    if is_prior:
        s = s[:-6]
    return s, is_us, is_last, is_prior


# ─── segments / metric 토큰 분석 ────────────────────────────────────
_DEVICE_KEYWORDS = [
    # (segments 안의 부분 문자열, device 슬러그) — 우선순위 순서
    ("android", "android"),
    ("ios", "ios"),
    ("mobile user", "mobile"),
    ("pc user", "pc"),
    ("app user", "app"),
    ("[global] app only", "app"),
]


def _detect_device(segments: str) -> str:
    """segments 에서 device 자리 슬러그 추출.

    device 토큰 없으면:
      · '[Global] Excluded APP' 등 'excluded app' 시그널이 있으면 → 'web'
        (mobile/pc 디바이스인데 app 트래픽만 제외한 web 전용 집계 의미)
      · 그 외엔 'total' (집계)
    """
    sg = segments.lower()
    for kw, dev in _DEVICE_KEYWORDS:
        if kw in sg:
            return dev
    if "excluded app" in sg:
        return "web"
    return "total"


# reportlet 의 base type 이 항상 'visit' 인 section — entry/bounce metric 이라도 measure=visit.
# 그 외 section (2_2 / 6_x / 4_x 등 channel/cross-tab 형) 는 metric 따라 entry/bounce/order/revenue.
# visit-base reportlet — TYPE 자리 = 'visit' (metric 무관, ITEM 자리에 metric 단수형 박힘)
# union 분석: 1_1/1_2/0_1/0_2/2_1/2_3 + 4_1/4_3 도 visit metric 일 때 measure=visit 컨벤션
_VISIT_BASE_SECTIONS = {"0_1", "0_2", "1_1", "1_2", "2_1", "2_3", "4_1"}
# order-base reportlet — metric=Revenue 면 measure=revenue, 그 외 measure=order
_ORDER_BASE_SECTIONS = {"4_2", "4_3", "5_1", "5_2", "5_3"}
# cross-sell section — item = '<line>_multiorder' (line = mx/vd/da/scom/campaign)
_CROSS_SELL_SECTIONS = {"5_1", "5_2", "5_3"}


def _detect_cross_sell_line(segments: str) -> str:
    """5_x cross-sell item 의 line prefix 결정.

    1) OR-exclude (한 라인만 살아남음):
       · vd,da Excluded → 'mx'
       · mx,da Excluded → 'vd'
       · mx,vd Excluded → 'da'
    2) individual `[Global] MX/VD/DA Order` segments 가 함께 있는 경우 → 살아남는 라인 조합
       예: 'MX & VD & DA Order (Exclude)' + 'MX Order' + 'VD Order'
           → mx & vd 가 살아남음 → 'mx_vd'
    3) campaign segment 있음 → 'campaign'
    4) 그 외 → 'scom'"""
    sg = segments.lower()
    # 1) OR-exclude (한 라인만 살아남음) — 우선 처리
    if "vd or da order (exclude)" in sg or "vd or da order(exclude)" in sg:
        return "mx"
    if "mx or da order (exclude)" in sg or "mx or da order(exclude)" in sg:
        return "vd"
    if "mx or vd order (exclude)" in sg or "mx or vd order(exclude)" in sg:
        return "da"
    # 2) individual MX/VD/DA Order segments 토큰 검사 (`[Global] MX Order` 형식, OR 없음)
    has_mx = bool(re.search(r"\[global\]\s+mx\s+order(?:\s*$|;)", sg))
    has_vd = bool(re.search(r"\[global\]\s+vd\s+order(?:\s*$|;)", sg))
    has_da = bool(re.search(r"\[global\]\s+da\s+order(?:\s*$|;)", sg))
    survived = [l for l, h in [("mx", has_mx), ("vd", has_vd), ("da", has_da)] if h]
    if len(survived) >= 2:
        return "_".join(survived)         # 'mx_vd' / 'mx_vd_da' 등
    if len(survived) == 1:
        return survived[0]                # 단일 라인
    # 'MX & VD & DA Order (Exclude)' 만 있고 individual 없는 경우 → total
    if "mx & vd & da order (exclude)" in sg or "mx vd da order (exclude)" in sg:
        return "total"
    # 3) 캠페인 segment
    if re.search(r"\[\d{2}\s+\w+\]\s*all\s*sites[_\s]+campaign", sg):
        return "campaign"
    return "scom"


def _detect_cross_sell_item(segments: str, metric: str, context: str, tb_core: str = "") -> str:
    """5_x cross-sell 의 item 자리. line + suffix.

    suffix 룰 (multiorder vs order):
      · tb 이름에 'multi_order' 토큰 (예: 5_1_*_multi_order_cross_sell) → 항상 multiorder
        (Unit>=2 segment 없어도 reportlet 자체가 multi-order 분석)
      · 또는 segments 에 'Unit >= 2' 있음 → multiorder
      · 그 외 → order (5_2 류)
      · context=cmp (5_3) → cmporder (multiorder/order 대신)

    line: total / mx / vd / da / mx_vd 등 (_detect_cross_sell_line)"""
    line = _detect_cross_sell_line(segments)
    sg = segments.lower()
    has_unit = "unit >= 2" in sg or "unit>=2" in sg or "unit >=2" in sg
    is_multi_tb = "multi_order" in tb_core.lower() or "multiorder" in tb_core.lower()
    if context.startswith("cmp"):
        if line == "campaign":
            return "cmporder"
        return f"{line}_cmporder"
    suffix = "multiorder" if (has_unit or is_multi_tb) else "order"
    return f"{line}_{suffix}"


def _detect_measure(segments: str, section: str, metric: str) -> str:
    """union KEY 의 TYPE 자리 (= measure). visit / order / revenue / entry / bounce.

    section 별 룰:
      · visit-base reportlet (1_1 / 1_2 / 0_1 / 0_2 / 2_1 / 2_3 / 4_1 / 4_3): 항상 'visit'
        (entry/bounce metric 이라도 measure=visit)
      · 4_2: order-base. metric=Revenue → revenue, 그 외 → order (Visit metric 이라도)
      · 그 외 (2_2 / 6_x): metric 단수형 그대로
    """
    if section in _VISIT_BASE_SECTIONS:
        return "visit"
    m = _metric_singular(metric)
    if section in _ORDER_BASE_SECTIONS:
        return "revenue" if m == "revenue" else "order"
    if m in ("order", "revenue", "entry", "bounce", "pageview", "visit", "visitor", "uniquevisitor"):
        return m
    return m or "visit"


# metric 표시 이름 → 단수형 compact (union ITEM 자리 컨벤션)
_METRIC_SINGULAR_MAP = {
    "visits":              "visit",
    "visitors":            "visitor",
    "uniquevisitors":      "visitor",            # 'Unique Visitors' → visitor (uniquevisitor 표기 단순화)
    "uniquevisitor":       "visitor",
    "nonbouncedvisits":    "nonbouncedvisit",
    "nonbouncedvisit":     "nonbouncedvisit",
    "appnonbouncedvisits": "nonbouncedvisit",   # "App Non bounced visits" 도 동일 normalize
    "appbounces":          "bounce",            # "App Bounces" → bounce (App prefix 제거)
    "appbounce":           "bounce",
    "apppageviews":        "pageview",          # "App Page Views" → pageview
    "apppageview":         "pageview",
    "appvisits":           "visit",
    "appvisit":            "visit",
    "appuniquevisitors":   "visitor",
    "appuniquevisitor":    "visitor",
    "appentries":          "entry",
    "appentry":            "entry",
    "pageviews":           "pageview",
    "pageview":            "pageview",
    "entries":             "entry",
    "entry":               "entry",
    "bounces":             "bounce",
    "bounce":              "bounce",
    "orders":              "order",
    "order":               "order",
    "revenues":            "revenue",
    "revenue":             "revenue",
    "cidtraffic":          "cidtraffic",
    "homevisit":           "homevisit",
    "homevisits":          "homevisit",
    "timespentpervisit":   "timespentpervisit",
    "totalrevenue":        "revenue",            # "Total Revenue" → revenue
    "totalorder":          "order",              # "Total Order" → order
    "totalorders":         "order",
    "totalrevenueevent":   "revenue",            # 괄호 빠뜨린 케이스 안전망
}


def _metric_singular(metric: str) -> str:
    """metric 표시 이름 → 단수형 compact (union ITEM 자리 컨벤션).
    룰: (1) 괄호 안 내용 제거 → (2) 영숫자 외 모두 제거 → lowercase →
        (3) _METRIC_SINGULAR_MAP 우선 → (4) 끝의 s 제거 (복수형 → 단수형).

    예) 'Order (purchase event)'   → 'order'   (괄호 제거 후 'order')
        'Total Revenue (event)'    → 'revenue' (괄호 제거 후 'totalrevenue' → map 'revenue')
        'Time Spent per Visit (Seconds)' → 'timespentpervisit'
        'App Bounces'              → 'bounce'
        'Unique Visitors'          → 'uniquevisitor'."""
    s = re.sub(r"\([^)]*\)", "", metric or "")   # 괄호 안 내용 제거
    compact = re.sub(r"[^a-z]", "", s.lower())
    if not compact:
        return ""
    if compact in _METRIC_SINGULAR_MAP:
        return _METRIC_SINGULAR_MAP[compact]
    if compact.endswith("s") and not compact.endswith("ss"):
        return compact[:-1]
    return compact


# 본인 회사의 baseline segment prefix 들 — segments 추출 시 무시할 그룹들.
# 예: [Global], [BIZ], [YOUR_TEAM], [24 1st] 등. 본인 컨벤션에 맞게 추가/수정.
_GLOBAL_SEG_RE = re.compile(r"^\[(global|biz|your_team|24[\s_]+1st)\]", re.IGNORECASE)
_CAMPAIGN_PREFIX_RE = re.compile(r"^\[\d{2}\s+\w+\]\s*(?:all\s*sites[_\s]+)?(.+)", re.IGNORECASE)
_DEVICE_SEG_RE = re.compile(
    r"(pc user|mobile user|app user|android|ios|app only|web user)", re.IGNORECASE
)


def _slugify(s: str) -> str:
    """segment 이름 등을 underscore slug 로 변환.
    의미 보존 변환:
      · '>'  → '_then_'  (예: 'Visit > Order' → 'visit_then_order')
      · '&'  → '_and_'   (예: 'Visit & Order' → 'visit_and_order')
    그 외 영숫자 외 모두 underscore 로."""
    s = s.lower()
    s = re.sub(r"\s*>\s*", " then ", s)
    s = re.sub(r"\s*&\s*", " and ", s)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def _extract_meaningful_seg_slug(segments: str) -> str:
    """segments 에서 device / global baseline 이 아닌 '의미 있는' segment 슬러그 추출.
    예: '[YY ABBR] ALL SITES_Internal_GNB' → 'internal_gnb'
         'Internal_Home GNB (Shop)'      → 'internal_home_gnb_shop'
    없으면 '' 반환."""
    for seg in segments.split(";"):
        seg = seg.strip()
        if not seg:
            continue
        # device-only segment skip
        if _DEVICE_SEG_RE.search(seg):
            continue
        # global baseline skip
        if _GLOBAL_SEG_RE.match(seg):
            continue
        # 캠페인 prefix 떼고 핵심만
        m = _CAMPAIGN_PREFIX_RE.match(seg)
        if m:
            return _slugify(m.group(1))
        return _slugify(seg)
    return ""


def _detect_login(segments: str, section: str, tb_has_logged: bool = False) -> str:
    """union LOGIN/NON 자리.
    · 같은 tb 안에 logged segment (logged in/out) 가 있는 row 가 하나라도 있으면 그 tb 전체가
      logged-cross-tab — 모든 row 의 login 자리에 total/login/logout 박힘.
      - 'logged in' → 'login'
      - 'logged out' → 'logout'
      - 그 외 (All Visits row, 또는 logged segment 없는 row) → 'total'
    · logged segment 가 전혀 없는 tb → 모든 row 의 login = 'null'
      (1_1 / 0_1 / 5_x / 6_x 같은 reportlet 류)
    """
    if not tb_has_logged:
        return "null"
    sg = segments.lower()
    if "logged in" in sg or "loggedin" in sg:
        return "login"
    if "logged out" in sg or "loggedout" in sg:
        return "logout"
    return "total"


# 1_1 / 0_1 류 — item 자리에 `uniquevisitor` (장형) 유지하는 section.
# 4_1 / 4_3 류 cell-aliased section 은 `visitor` (단축형).
_LONG_VISITOR_SECTIONS = {"0_1", "0_2", "1_1", "1_2", "2_1", "2_3"}


def _build_4_2_item_alias(segments: str, metric: str) -> str:
    """4_2 의 cell 별칭 item 생성.
    예) '[YY ABBR] ALL SITES_Campaign Page > PD Visit (All Products)' → 'main_then_pd_all'
        '[YY ABBR] ALL SITES_Campaign Page & Add to Cart Visit (All Products)' → 'main_and_atc_all'
        '[YY ABBR] ALL SITES_Campaign Page Visit & Order (Brand Name)' → 'main_and_brandname_and_order_all'
        (일반화 어려운 케이스는 best-effort)"""
    # 의미있는 첫 segment 추출
    for seg in segments.split(";"):
        seg = seg.strip()
        if not seg:
            continue
        s_lower = seg.lower()
        if _DEVICE_SEG_RE.search(seg):
            continue
        if _GLOBAL_SEG_RE.match(seg):
            continue
        if "logged" in s_lower or "all visits" in s_lower or "all_visits" in s_lower:
            continue
        if "no data" in s_lower or "unit" in s_lower or "site code" in s_lower:
            continue
        m = _CAMPAIGN_PREFIX_RE.match(seg)
        if not m:
            continue
        core = m.group(1).lower()
        # 괄호 안 내용 추출 → suffix
        paren_match = re.search(r"\(([^)]+)\)", core)
        paren_slug = "_all"   # default
        if paren_match:
            p = paren_match.group(1).strip().lower()
            tokens = re.split(r"[^a-z]+", p)
            tokens = [t for t in tokens if t and t not in ("products", "purchase")]
            if tokens:
                first = tokens[0]
                if first == "all":
                    paren_slug = "_all"
                elif first == "delayed":
                    paren_slug = "_all"   # filled 컨벤션: Delayed Purchase → _all
                else:
                    # brand 명 (Brand Name / Trade In Up / 등) — 전체 합쳐서 slug
                    paren_slug = "_" + "".join(tokens)
            core = core[:paren_match.start()] + core[paren_match.end():]
        # 변환: "Campaign Page" / "Campaign Content" → "main"
        core = re.sub(r"campaign\s*(?:page|content)", "main", core)
        # `>` / `&` → then / and
        core = re.sub(r"\s*>\s*", " then ", core)
        core = re.sub(r"\s*&\s*", " and ", core)
        # 핵심 토큰 단축
        core = re.sub(r"\badd\s*to\s*cart\b", "atc", core)
        core = re.sub(r"\bvisit\b", "", core)
        core = re.sub(r"\bclick\b", "", core)
        # underscore 정리
        slug = re.sub(r"[^a-z0-9]+", "_", core).strip("_")
        if not slug:
            return ""
        # paren brand 가 있는 경우 main_<brand>_and_order_<all> 형태 처리:
        # 위 룰로 core 가 "main_and_order" (Campaign Page Visit & Order) + paren=_brandname
        # union 컨벤션: main_and_brandname_and_order_all → brand 가 'order' 앞에 끼어듦
        if paren_slug not in ("_all",) and "_and_order" in slug:
            slug = slug.replace("_and_order", f"{paren_slug}_and_order")
            paren_slug = "_all"
        return slug + paren_slug
    return ""


def _detect_item(segments: str, metric: str, section: str, context: str = "scom", tb_core: str = "") -> str:
    """union ITEM 자리.

    1) 4_2: segments 의 'Campaign Page > PD Visit (All Products)' 같은 reportlet 셀 별칭
       → 'main_then_pd_all' 형태로 변환
    2) internal_/home_ segment → 축약형 (internal_gnb 등)
    3) 그 외 → metric 단수형 (section 별 uniquevisitor/visitor 분기)
    """
    if section == "4_2":
        alias = _build_4_2_item_alias(segments, metric)
        if alias:
            # metric=Revenue 일 때 filled 는 '_rev' suffix 추가하는 컨벤션
            m_singular = _metric_singular(metric)
            if m_singular == "revenue" and not alias.endswith("_rev"):
                alias = alias + "_rev"
            elif m_singular == "visitor" and not alias.endswith("_visitor"):
                alias = alias + "_visitor"
            return alias
    if section == "4_3":
        # 4_3 의 Unit>=2 케이스 → cross-sell 변환 (scom_multiorder)
        sg = segments.lower()
        if "unit >= 2" in sg or "unit>=2" in sg or "unit >=2" in sg:
            return "scom_multiorder"
        m_singular = _metric_singular(metric)
        return "scom_and_order_all_rev" if m_singular == "revenue" else "scom_and_order_all"
    if section in _CROSS_SELL_SECTIONS:
        # 5_x cross-sell: <line>_{multiorder|order|cmporder}
        return _detect_cross_sell_item(segments, metric, context, tb_core)
    if section == "2_3":
        # 2_3 (homepage KV/GNB clicks to cmp):
        #   · segments 에 Internal_* segment → '<internal_뒤_슬러그>_tocmp'
        #     예: 'Internal_Home KV' → 'home_kv_tocmp'
        #         'Internal_Home GNB (Shop)' → 'home_gnb_tocmp'  (괄호 제거)
        #   · 없음 → 'home{metric}' (underscore 없이 붙여서, 예: 'homevisit')
        for seg in segments.split(";"):
            seg_strip = seg.strip()
            m = re.search(r"internal_(.+)", seg_strip, re.IGNORECASE)
            if m:
                core = m.group(1)
                core = re.sub(r"\s*\([^)]*\)", "", core).strip()    # 괄호 제거
                inner_slug = re.sub(r"[^a-z0-9]+", "_", core.lower()).strip("_")
                if inner_slug:
                    return f"{inner_slug}_tocmp"
        # internal 없음 — homevisit 류 (단어 붙여씀)
        return f"home{_metric_singular(metric)}"
    seg_slug = _extract_meaningful_seg_slug(segments)
    if seg_slug and seg_slug.startswith(("internal_", "home_")):
        # union 컨벤션 축약형으로 매핑 (internal_pf_page_banner → internal_pf 등)
        return _INTERNAL_SLUG_MAP.get(seg_slug, seg_slug)
    m = _metric_singular(metric)
    # 1_1 / 0_1 류는 'uniquevisitor' 장형 유지
    if section in _LONG_VISITOR_SECTIONS and m == "visitor":
        m = "uniquevisitor"
    # segments 에 'No Data' segment 가 있으면 item 끝에 '_nodata' suffix —
    # 같은 metric 의 일반 row 와 column 중복 방지 (C열 unique key 보장)
    sg = segments.lower()
    if "no data" in sg or "nodata" in sg:
        return f"{m}_nodata"
    return m


# dimension-driven section — JSON 추출 시 row dimension 에 marketingchannel 같은 variable 이
# 박혀있어서, raw 단계에서 item 자리는 비어있고 union RESHAPE 후처리 단계 (RESHAPE_main_raw_v4.2)
# 에서 채널 값이 채워지는 흐름. 따라서 generator 는 item 자리 비우고 trailing `_` 로 끝나는 형태로 생성.
_CHANNEL_DIMENSION_SECTIONS = {
    "2_2",                        # 2_2 external traffic by channel (dimension=marketingchannel)
    "6_1", "6_2", "6_3", "6_4",   # external/internal channel, cid revisit
}
# 6_0 은 internal segment slug 가 ITEM 자리에 직접 들어가는 별도 패턴 — 일단 미해석 처리
_UNRESOLVED_SECTIONS = {
    "6_0",
}


# ─── column 값을 union 컬럼 component 별로 parse ──────────────────
# 포맷: <section>_<scope>_<year>_<context>_<device>_<measure>_<login>_<item>
#  · section = X_Y (앞 2 토큰)
#  · context = cmp / scom / scom_prior / cmp_prior  (1 또는 2 토큰)
#  · item    = 마지막 남은 모든 토큰 (slug 일 수 있음, 예: 'internal_gnb', 'main_then_pd_all')
_COMPONENT_FIELDS = ["section", "scope", "year", "context", "device", "measure", "login", "item"]


def _parse_column(col: str) -> dict | None:
    """column 값을 union 컴포넌트 dict 로 분해. 형식 안 맞으면 None."""
    if not col:
        return None
    parts = col.split("_")
    if len(parts) < 8:
        return None
    out: dict = {}
    out["section"] = "_".join(parts[0:2])   # X_Y
    out["scope"]   = parts[2]
    out["year"]    = parts[3]
    i = 4
    # context: 1 or 2 tokens (scom_prior 면 2)
    if i + 1 < len(parts) and parts[i] in ("cmp", "scom") and parts[i + 1] == "prior":
        out["context"] = f"{parts[i]}_prior"
        i += 2
    else:
        out["context"] = parts[i]
        i += 1
    out["device"]  = parts[i] if i < len(parts) else ""
    i += 1
    out["measure"] = parts[i] if i < len(parts) else ""
    i += 1
    out["login"]   = parts[i] if i < len(parts) else ""
    i += 1
    out["item"]    = "_".join(parts[i:]) if i < len(parts) else ""
    return out


def diff_fields(built: str, filled: str) -> str:
    """built / filled 두 column 값을 component 별 비교 → 다른 필드 이름 ',' join.
    parse 실패 시 'parse_fail'. 같으면 빈 문자열."""
    if built == filled:
        return ""
    bp = _parse_column(built)
    fp = _parse_column(filled)
    if not bp or not fp:
        return "parse_fail"
    diffs = [k for k in _COMPONENT_FIELDS if bp.get(k, "") != fp.get(k, "")]
    return ",".join(diffs) if diffs else ""
# special tb (segments 외 정보로만 결정) — 공란 처리
_SPECIAL_TB_KEYWORDS = ("best_selling", "bestselling", "next_page", "nextpage", "multi_purchase")


# ─── metric compact ────────────────────────────────────────────────
def _metric_compact(metric: str) -> str:
    """metric 표시 이름 → compact lowercase (영숫자만)."""
    return re.sub(r"[^a-z]", "", (metric or "").lower())


# ─── tb 안의 scope (0_1 카테고리만) ────────────────────────────────
def _detect_scope_from_tb(tb_core: str, section: str) -> str:
    if section != "0_1":
        return "all"
    # tb_core 안에 _da_ / _mx_ / _vd_ 포함되어있는지
    parts = tb_core.split("_")
    for s in ("da", "mx", "vd"):
        if s in parts:
            return s
    return "all"


def _detect_context(tb_core: str, is_prior: bool, segments: str = "", section: str = "") -> str:
    """context 자리 결정.
    · 4_x: segments 의 캠페인 segment 우선 (tb 이름에 cmp/scom 둘 다 있는 경우 흔함)
      - '[XX YYY] ALL SITES_Campaign...' 있음 → 'cmp'
      - 없고 tb 에 scom 토큰 → 'scom'
      - 없고 tb 에 cmp 토큰 → 'cmp'
      - 둘 다 없음 → 'scom'
    · 그 외 section: tb 의 scom/cmp 토큰 → 'scom'/'cmp', default 'cmp'
    """
    parts = set(tb_core.split("_"))
    has_cmp  = "cmp" in parts
    has_scom = "scom" in parts
    has_campaign_seg = bool(re.search(
        r"\[\d{2}\s+\w+\]\s*all\s*sites[_\s]+campaign", segments, re.IGNORECASE,
    ))
    if section.startswith("4_"):
        if has_campaign_seg:
            ctx = "cmp"
        elif has_scom:
            ctx = "scom"
        elif has_cmp:
            ctx = "cmp"
        else:
            ctx = "scom"
    elif has_scom:
        ctx = "scom"
    elif has_cmp:
        ctx = "cmp"
    else:
        ctx = "cmp"
    if is_prior:
        ctx += "_prior"
    return ctx


# ─── special tb (next_page / multi_purchase / best_selling / 6_0) ──
# 6_0 의 internal segment slug — union ITEM 자리는 축약형 사용.
_INTERNAL_SLUG_MAP = {
    "internal_gnb":              "internal_gnb",
    "internal_gnb_l0":           "internal_gnb_l0",
    "internal_gnb_l1":           "internal_gnb_l1",
    "internal_home_gnb":         "internal_gnb",
    "internal_home_gnb_shop":    "internal_gnb",
    "internal_home_kv":          "internal_kv",
    "internal_kv":               "internal_kv",
    "internal_my_page_banner":   "internal_mypage",
    "internal_my_page":          "internal_mypage",
    "internal_offer_banner":     "internal_offerpage",
    "internal_offerpage":        "internal_offerpage",
    "internal_pf_page_banner":   "internal_pf",
    "internal_pf":               "internal_pf",
    "internal_rewards_banner":   "internal_rewardspage",
    "internal_rewardspage":      "internal_rewardspage",
    "internal_rmsm_page_banner": "internal_rmsm",
    "internal_rmsm":             "internal_rmsm",
}


def _value_n_int(value_n: str) -> int | None:
    """'value1' → 1, 'valueN' → N. 형식 안 맞으면 None."""
    try:
        return int(value_n.replace("value", ""))
    except (ValueError, AttributeError):
        return None


def _build_best_selling_column(tb_core: str, value_n: str) -> str | None:
    """best_selling_products / us_best_selling — value_n 별 매핑.
    pattern: <scope>_total_best_selling_<metric>
      v1-2: scom    / v3-4: campaign / v5-6: ranking
      odd=order, even=revenue"""
    if "best_selling" not in tb_core and "bestselling" not in tb_core:
        return None
    n = _value_n_int(value_n)
    if n is None: return None
    if   n <= 2: scope = "scom"
    elif n <= 4: scope = "campaign"
    elif n <= 6: scope = "ranking"
    else:        return None
    metric = "order" if n % 2 == 1 else "revenue"
    return f"{scope}_total_best_selling_{metric}"


def _build_multi_purchase_column(tb_core: str, value_n: str, is_prior: bool) -> str | None:
    """multi_purchase / multi_purchase_prior — value_n 별 매핑.
    pattern: <scope>(_prior)_total_multiorder<suffix>
      v1-3: campaign / v4-6: scom
      v1,4 → _unit / v2,5 → '' / v3,6 → _revenue"""
    if not tb_core.startswith("multi_purchase") and "multi_purchase" not in tb_core:
        return None
    n = _value_n_int(value_n)
    if n is None: return None
    if   n <= 3: scope = "campaign"
    elif n <= 6: scope = "scom"
    else:        return None
    suffix_map = {1: "_unit", 2: "", 3: "_revenue", 4: "_unit", 5: "", 6: "_revenue"}
    suffix = suffix_map.get(n, "")
    prior_part = "_prior" if is_prior else ""
    return f"{scope}{prior_part}_total_multiorder{suffix}"


def _build_next_page_column(tb_core: str, value_n: str) -> str | None:
    """next_page_total_mx / next_page_vd_da / us_next_page / nextpage — tb 이름 + value_n."""
    if not (tb_core.startswith("next_page") or tb_core.startswith("nextpage")):
        return None
    n = _value_n_int(value_n)
    if n is None: return None
    if tb_core.startswith("nextpage"):
        return "campaign_total_next_p6_all" if n == 1 else None
    if "vd_da" in tb_core:
        kind = {1: "vd", 2: "da"}.get(n)
    elif "total_mx" in tb_core or "next_page_total" in tb_core:
        kind = {1: "all", 2: "mx"}.get(n)
    else:
        kind = "all" if n == 1 else None
    return f"campaign_total_next_p6_{kind}" if kind else None


def _build_6_0_column(segments: str, metric: str, year: str, context: str) -> str | None:
    """6_0 의 column: 6_0_all_<year>_<context>_<internal_slug>_<metric_singular>.
    segments 의 Internal_* segment 슬러그를 union 축약형 (internal_gnb/internal_pf 등) 으로 매핑.

    segment 가 'Internal_GNB & Order' 같이 '_and_order' / '_then_order' 같은 suffix 가 있어도
    internal_slug 자리는 'internal_gnb' 만 두고 metric 자리는 metric 단수형 (visit/order/revenue).
    """
    slug = _extract_meaningful_seg_slug(segments)
    if not slug:
        return None
    # & Order / > Order 같은 추가 part 제거 — metric 자리에서 어차피 표시됨
    slug = re.sub(r"_(and|then)_order$", "", slug)
    slug = re.sub(r"_(and|then)_visit$", "", slug)
    slug = _INTERNAL_SLUG_MAP.get(slug, slug)
    if not slug.startswith("internal_"):
        return None
    m = _metric_singular(metric) or "visit"
    return f"6_0_all_{year}_{context}_{slug}_{m}"


_SPECIAL_TB_KEYWORDS = ("best_selling", "bestselling", "next_page", "nextpage", "multi_purchase")


def _build_special_column(tb_core: str, segments: str, metric: str, is_prior: bool, value_n: str) -> str | None:
    """special tb (best_selling / multi_purchase / next_page) — C 열은 정제 시 RESHAPE 단계에서
    별도 채움. column 자체는 'nodata_<tb>_<value_n>' placeholder (C열 고유 키 보장)."""
    tb_lower = tb_core.lower()
    if any(kw in tb_lower for kw in _SPECIAL_TB_KEYWORDS):
        return f"nodata_{tb_core}_{value_n}"
    return None


# ─── 메인 generator ────────────────────────────────────────────────
def generate_column(tb: str, segments: str, metric: str, panel: str, period: str,
                    value_n: str = "", tb_has_logged: bool = False) -> str:
    tb_core, is_us, is_last, is_prior_tb = _strip_tb_prefixes(tb)
    is_prior = is_prior_tb or (period == "prior")
    year = "2025" if is_last or period == "last" else "2026"

    # special tb (best_selling / next_page / multi_purchase) — value_n 별 매핑
    special = _build_special_column(tb_core, segments, metric, is_prior, value_n)
    if special is not None:
        return special

    # section 추출
    sec_match = re.match(r"^(\d+_\d+)_(.+)", tb_core)
    if not sec_match:
        return ""

    section = sec_match.group(1)
    rest    = sec_match.group(2)

    # 6_0: internal segment slug + metric 패턴 (별도 처리)
    if section == "6_0":
        context = _detect_context(rest, is_prior, segments, section)
        return _build_6_0_column(segments, metric, year, context) or ""

    scope   = _detect_scope_from_tb(rest, section)
    context = _detect_context(rest, is_prior, segments, section)
    device  = _detect_device(segments)
    measure = _detect_measure(segments, section, metric)
    login   = _detect_login(segments, section, tb_has_logged)

    # 6_1~6_4: marketingchannel dimension → ITEM 자리 비우고 trailing _
    if section in _CHANNEL_DIMENSION_SECTIONS:
        return f"{section}_{scope}_{year}_{context}_{device}_{measure}_{login}_"

    item = _detect_item(segments, metric, section, context, tb_core)
    if not item:
        item = "unknown"

    return f"{section}_{scope}_{year}_{context}_{device}_{measure}_{login}_{item}"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    rows = list(csv.DictReader(open(NEW_CSV, encoding="utf-8-sig")))
    print(f"INPUT: {len(rows)} rows  ({NEW_CSV.name})")

    # filled CSV 가 있으면 (tb, value_n) → column 매핑으로 로드 (비교용)
    filled_map: dict[tuple[str, str], str] = {}
    if FILLED_CSV.exists():
        for fr in csv.DictReader(open(FILLED_CSV, encoding="utf-8-sig")):
            filled_map[(fr["tb"], fr["value_n"])] = fr.get("column", "")
        print(f"FILLED: {len(filled_map)} rows  ({FILLED_CSV.name}) — 비교 모드")
    else:
        print(f"FILLED CSV 없음 ({FILLED_CSV.name}) — 비교 컬럼 생략")

    # tb 별 logged segment 존재 flag 미리 계산 (login 자리 결정용)
    # 같은 tb 안에 logged in/out 가 있는 row 가 하나라도 있으면 그 tb 전체가 logged-cross-tab
    tb_has_logged: dict[str, bool] = {}
    for r in rows:
        sg = (r.get("segments") or "").lower()
        if "logged in" in sg or "logged out" in sg or "loggedin" in sg or "loggedout" in sg:
            tb_has_logged[r["tb"]] = True

    out_rows: list[dict] = []
    n_generated = 0
    n_unknown = 0
    n_match = 0
    n_diff = 0
    n_compare_skip = 0
    for r in rows:
        col = generate_column(
            r["tb"], r.get("segments", ""), r.get("metric", ""),
            r.get("panel", ""), r.get("period", ""), r.get("value_n", ""),
            tb_has_logged.get(r["tb"], False),
        )
        if col:
            n_generated += 1
        else:
            n_unknown += 1

        new_row = {**r, "column": col}
        if filled_map:
            f_col = filled_map.get((r["tb"], r["value_n"]), "")
            if not col:
                new_row["match_filled"] = "미해석"
                new_row["diff_field"]   = ""
                n_compare_skip += 1
            elif not f_col:
                new_row["match_filled"] = "비교불가"
                new_row["diff_field"]   = ""
                n_compare_skip += 1
            elif col == f_col:
                new_row["match_filled"] = "일치"
                new_row["diff_field"]   = ""
                n_match += 1
            else:
                # component 별 어느 필드가 다른지 표시
                diff = diff_fields(col, f_col)
                new_row["match_filled"] = "불일치"
                new_row["diff_field"]   = diff
                n_diff += 1
        out_rows.append(new_row)

    fieldnames = list(rows[0].keys())
    if filled_map:
        fieldnames = fieldnames + ["match_filled", "diff_field"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in out_rows:
            w.writerow(r)

    print(f"\n생성    : {n_generated}")
    print(f"미해석  : {n_unknown}")
    if filled_map:
        print(f"일치    : {n_match}")
        print(f"불일치  : {n_diff}")
        print(f"비교스킵: {n_compare_skip}  (built 가 미해석이거나 filled 가 빈 값)")
    print(f"출력    : {OUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
