# generate_column_from_segments_v2.0.py
# 2026-05-13  Jonghyun Park w/ Claude
#
# v2.0 변경 — 8 토큰 정확히 보장:
#   · section = X-Y (예: '1-1', '4-2', '6-0')
#   · 모든 multi-word slug 내부는 '-' 결합 (예: 'internal-gnb-l0', 'main-then-pd-all')
#   · 최종 column 은 '_' 7개 (8 토큰) — col.split('_') 시 항상 8개 토큰
#   · 6_0 도 8 토큰 표준 따름 (item 자리에 internal slug)
# v1 (단일 '_' 컨벤션) 은 동일 폴더의 generate_column_from_segments.py 참조.
"""
구버전 매핑 CSV 를 참조하지 않고, 신버전 매핑 CSV 의 (tb / segments / metric / panel / period)
컬럼만 보고 column 값을 ALGORITHMIC 하게 재구성하는 generator.

비교 목적: similarity 기반 매핑 (_fill_column_by_similarity.py) 결과와 비교해서
column 명명 규칙이 얼마나 일관적인지, 어디서 규칙이 어긋나는지 파악.

column 값 일반 포맷:
    {section}_{scope}_{year}_{context}_{device}_{measure}_{extra}_{metric}

components:
  · section      — tb 의 1_1 / 0_1 / 4_2 등 numeric prefix
  · scope        — 0_1 카테고리는 da/mx/vd, 그 외는 all
  · year         — 2025 (period=last) / 2026 (campaign or prior)
  · context      — cmp / scom (+ _prior 변형)
  · device       — pc / mobile / app / android / ios / web / total (segments 에서 유추)
  · measure      — visit / visitor / entry / order (segments 에서 유추)
  · extra        — 추가 segment 슬러그 (internal_gnb 등) 또는 'null'
  · metric       — metric 컬럼의 compact lowercase

special tbs (다른 포맷):
  · next_page_*      → campaign_total_next_p6_<all|vd>
  · multi_purchase   → campaign_total_multiorder_unit (prior 면 campaign_prior_*)
  · best_selling_*   → scom_total_best_selling_<metric>

출력: `<NEW>_generated.csv` (column 컬럼 자동 채움)
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

NEW_CSV = Path(r"C:\path\to\your\ref\tb_column_name_mapping_YYMMDD_HHMM.csv")
# similarity 기반 채움 결과 — 출력 CSV 마지막 컬럼 'match_filled' 에 일치/불일치 표시
FILLED_CSV = NEW_CSV.with_name(NEW_CSV.stem + "_filled.csv")
OUT_CSV = NEW_CSV.with_name(NEW_CSV.stem + "_built_v2.csv")


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
        return "-".join(survived)         # 'mx-vd' / 'mx-vd-da' 등
    if len(survived) == 1:
        return survived[0]
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
        return f"{line}-cmporder"
    suffix = "multiorder" if (has_unit or is_multi_tb) else "order"
    return f"{line}-{suffix}"


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


_GLOBAL_SEG_RE = re.compile(r"^\[(global|biz|your_team|24[\s_]+1st)\]", re.IGNORECASE)
_CAMPAIGN_PREFIX_RE = re.compile(r"^\[\d{2}\s+\w+\]\s*(?:all\s*sites[_\s]+)?(.+)", re.IGNORECASE)
_DEVICE_SEG_RE = re.compile(
    r"(pc user|mobile user|app user|android|ios|app only|web user)", re.IGNORECASE
)


def _slugify(s: str) -> str:
    """segment 이름 등을 dash slug 로 변환 (v2.0: 토큰 내부 결합은 '-').
    의미 보존 변환:
      · '>'  → '-then-'  (예: 'Visit > Order' → 'visit-then-order')
      · '&'  → '-and-'
    그 외 영숫자 외 모두 dash 로."""
    s = s.lower()
    s = re.sub(r"\s*>\s*", " then ", s)
    s = re.sub(r"\s*&\s*", " and ", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
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
    예) '[YY ABBR] ALL SITES_Campaign Page > PD Visit (All Products)' → 'main-then-pd-all'
        '[YY ABBR] ALL SITES_Campaign Page & Add to Cart Visit (All Products)' → 'main-and-atc-all'
        '[YY ABBR] ALL SITES_Campaign Page Visit > Order (Brand Name)' → 'main-and-brandname-and-order-all'
        (v2.0: 슬러그 내부 결합 '-' / 일반화 어려운 케이스는 best-effort)"""
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
        paren_slug = "-all"   # default
        if paren_match:
            p = paren_match.group(1).strip().lower()
            tokens = re.split(r"[^a-z]+", p)
            tokens = [t for t in tokens if t and t not in ("products", "purchase")]
            if tokens:
                first = tokens[0]
                if first == "all":
                    paren_slug = "-all"
                elif first == "delayed":
                    paren_slug = "-all"
                else:
                    paren_slug = "-" + "".join(tokens)
            core = core[:paren_match.start()] + core[paren_match.end():]
        core = re.sub(r"campaign\s*(?:page|content)", "main", core)
        core = re.sub(r"\s*>\s*", " then ", core)
        core = re.sub(r"\s*&\s*", " and ", core)
        core = re.sub(r"\badd\s*to\s*cart\b", "atc", core)
        core = re.sub(r"\bvisit\b", "", core)
        core = re.sub(r"\bclick\b", "", core)
        slug = re.sub(r"[^a-z0-9]+", "-", core).strip("-")
        if not slug:
            return ""
        if paren_slug != "-all" and "-and-order" in slug:
            slug = slug.replace("-and-order", f"{paren_slug}-and-order")
            paren_slug = "-all"
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
            # metric=Revenue 일 때 filled 는 '-rev' suffix 추가하는 컨벤션 (v2.0: dash)
            m_singular = _metric_singular(metric)
            if m_singular == "revenue" and not alias.endswith("-rev"):
                alias = alias + "-rev"
            elif m_singular == "visitor" and not alias.endswith("-visitor"):
                alias = alias + "-visitor"
            return alias
    if section == "4_3":
        sg = segments.lower()
        if "unit >= 2" in sg or "unit>=2" in sg or "unit >=2" in sg:
            return "scom-multiorder"
        m_singular = _metric_singular(metric)
        return "scom-and-order-all-rev" if m_singular == "revenue" else "scom-and-order-all"
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
                core = re.sub(r"\s*\([^)]*\)", "", core).strip()
                inner_slug = re.sub(r"[^a-z0-9]+", "-", core.lower()).strip("-")
                if inner_slug:
                    return f"{inner_slug}-tocmp"
        return f"home{_metric_singular(metric)}"
    seg_slug = _extract_meaningful_seg_slug(segments)
    if seg_slug and seg_slug.startswith(("internal-", "home-")):
        return _INTERNAL_SLUG_MAP.get(seg_slug, seg_slug)
    m = _metric_singular(metric)
    if section in _LONG_VISITOR_SECTIONS and m == "visitor":
        m = "uniquevisitor"
    sg = segments.lower()
    if "no data" in sg or "nodata" in sg:
        return f"{m}-nodata"
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
    """column 값을 union 컴포넌트 dict 로 분해 (v2.0: 정확히 8 토큰).
    형식 안 맞으면 None.

    v2.0 컨벤션: 모든 내부 결합은 '-' → split('_') 으로 항상 8 토큰.
      · section 은 'X-Y' (예: '1-1', '6-0')
      · context 는 'scom' / 'cmp' / 'scom-prior' / 'cmp-prior' (1 토큰)
      · item 은 마지막 1 토큰 (multi-word 라도 내부 '-' 결합)
    """
    if not col:
        return None
    parts = col.split("_")
    if len(parts) != 8:
        return None
    return {
        "section": parts[0],
        "scope":   parts[1],
        "year":    parts[2],
        "context": parts[3],
        "device":  parts[4],
        "measure": parts[5],
        "login":   parts[6],
        "item":    parts[7],
    }


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
        ctx += "-prior"   # v2.0: 토큰 내부 결합은 '-' (split 시 8 토큰 보장)
    return ctx


# ─── special tb (next_page / multi_purchase / best_selling / 6_0) ──
# 6_0 의 internal segment slug — union ITEM 자리는 축약형 사용.
_INTERNAL_SLUG_MAP = {
    # v2.0: _slugify 가 '-' 슬러그 생성 → keys 도 '-' 슬러그
    "internal-gnb":              "internal-gnb",
    "internal-gnb-l0":           "internal-gnb-l0",
    "internal-gnb-l1":           "internal-gnb-l1",
    "internal-home-gnb":         "internal-gnb",
    "internal-home-gnb-shop":    "internal-gnb",
    "internal-home-kv":          "internal-kv",
    "internal-kv":               "internal-kv",
    "internal-my-page-banner":   "internal-mypage",
    "internal-my-page":          "internal-mypage",
    "internal-offer-banner":     "internal-offerpage",
    "internal-offerpage":        "internal-offerpage",
    "internal-pf-page-banner":   "internal-pf",
    "internal-pf":               "internal-pf",
    "internal-rewards-banner":   "internal-rewardspage",
    "internal-rewardspage":      "internal-rewardspage",
    "internal-rmsm-page-banner": "internal-rmsm",
    "internal-rmsm":             "internal-rmsm",
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
    slug = re.sub(r"-(and|then)-order$", "", slug)
    slug = re.sub(r"-(and|then)-visit$", "", slug)
    slug = _INTERNAL_SLUG_MAP.get(slug, slug)
    if not slug.startswith("internal-"):
        return None
    m = _metric_singular(metric) or "visit"
    # v2.0: 8 토큰 표준 — 6-0_all_<year>_<context>_total_<metric>_null_<internal-slug>
    return f"6-0_all_{year}_{context}_total_{m}_null_{slug}"


_SPECIAL_TB_KEYWORDS = ("best_selling", "bestselling", "next_page", "nextpage", "multi_purchase")


def _build_special_column(tb_core: str, segments: str, metric: str, is_prior: bool, value_n: str) -> str | None:
    """special tb (best_selling / multi_purchase / next_page) — C 열은 정제 시 RESHAPE 단계에서
    별도 채움. column 자체는 'nodata_<tb>_<value_n>' placeholder (C열 고유 키 보장)."""
    tb_lower = tb_core.lower()
    if any(kw in tb_lower for kw in _SPECIAL_TB_KEYWORDS):
        # v2.0: 단일 dash-slug placeholder (8 토큰 룰 예외 — special tb 식별 + unique key 보장)
        tb_slug = tb_core.replace("_", "-")
        return f"nodata-{tb_slug}-{value_n}"
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
    # v2.0: section 의 '_' → '-' (split('_') 시 정확히 8 토큰 보장)
    sec_dash = section.replace("_", "-")

    # 6_1~6_4: marketingchannel dimension → ITEM 자리 비우고 trailing _
    if section in _CHANNEL_DIMENSION_SECTIONS:
        return f"{sec_dash}_{scope}_{year}_{context}_{device}_{measure}_{login}_"

    item = _detect_item(segments, metric, section, context, tb_core)
    if not item:
        item = "unknown"

    return f"{sec_dash}_{scope}_{year}_{context}_{device}_{measure}_{login}_{item}"


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
