# generate_column_from_segments.py

`extract_panel_tables_json_v2.0.py` 가 생성한 매핑 CSV 의 빈 `column` 컬럼을, 같은 row 의 `tb / segments / metric / panel / period` 만 보고 **algorithmic 하게 재구성** 하는 generator. union KEY 형식의 column 값을 자동으로 생성.

기준 문서 업데이트일: 2026-05-12

---

## 입력 / 출력

| 변수 | 의미 |
|---|---|
| `NEW_CSV` | extract v2.0 출력 매핑 CSV (`segments` + `metric` 컬럼 포함) |
| `FILLED_CSV` *(선택)* | similarity 기반 채움 결과 — 있으면 `match_filled` + `diff_field` 비교 컬럼 자동 추가 |
| `OUT_CSV` | `<NEW>_built.csv` — column 자동 채움 |

스크립트 상단의 `NEW_CSV` 만 본인 경로로 바꿔서 실행.

```bash
python generate_column_from_segments.py
```

---

## column 값 8 토큰 표준 포맷

```
{section}_{scope}_{year}_{context}_{device}_{measure}_{login}_{item}
```

| 토큰 | 의미 | 결정 룰 |
|---|---|---|
| `section` | reportlet 번호 | tb 의 `X_Y` numeric prefix |
| `scope` | data type | 0_1 은 da/mx/vd, 그 외 all |
| `year` | 연도 | period=last → 2025 / 그 외 → 2026 |
| `context` | reportlet 컨텍스트 | tb 토큰 cmp/scom 우선. 4_x 는 segments 의 campaign segment 보고 cmp/scom |
| `device` | 디바이스 | segments 의 PC/Mobile/App/Android/iOS User. `Excluded APP` 만 있으면 web |
| `measure` | reportlet base type | visit-base (1_1/0_1/0_2/1_2/2_1/2_3/4_1) → 항상 visit. order-base (4_2/4_3/5_x) → metric 따라 order/revenue. 그 외 → metric 단수형 |
| `login` | login/logout/total | 같은 tb 안에 logged in/out segment 가 있으면 logged-cross-tab → row 별 login/logout/total. 그 외 모든 tb → null |
| `item` | 셀 별칭 | section 별 다양 (아래 표) |

---

## ITEM 자리 룰 (section 별)

| section | 룰 |
|---|---|
| 1_1 / 0_2 / 0_1 / 1_2 등 visit-base | metric 단수형 (visit / uniquevisitor / pageview / entry / bounce / pageview ...) |
| (모든 section 공통) | segments 에 `No Data` 있는 row → `{metric}_nodata` (C열 unique key 보장) |
| 2_1 | Internal_* segment 의 union 축약 슬러그 (`internal_gnb` / `internal_pf` / `internal_kv` 등) |
| 2_3 (homepage KV/GNB to cmp) | · Internal_* 있음 → `<internal_뒤_슬러그>_tocmp` (예: `home_kv_tocmp`)<br>· 없음 → `home{metric}` (`homevisit` 등) |
| 4_2 | `Campaign Page > PD Visit (All Products)` → `main_then_pd_all` 류 cell 별칭 |
| 4_3 | default `scom_and_order_all` (+`_rev` if revenue). segments 에 `Unit >= 2` 있음 → `scom_multiorder` |
| 5_1 / 5_2 / 5_3 cross-sell | `<line>_{multiorder\|order\|cmporder}` (아래 cross-sell 룰 참조) |
| 6_0 | 7-토큰 특수: `6_0_<scope>_<year>_<context>_<internal_slug>_<metric>` |
| 6_1~6_4 (marketingchannel dimension) | trailing `_` (item 자리 빈 채로 — RESHAPE 단계에서 채널값 채움) |
| best_selling / multi_purchase / next_page | placeholder `nodata_<tb>_<value_n>` (C열 unique key 보장) |

---

## Cross-sell (5_x) line 결정 룰

`segments` 의 OR-exclude 와 individual `[Global] MX/VD/DA Order` 토큰 보고 살아남는 라인 결정:

| segments 패턴 | line |
|---|---|
| `vd or da Order (Exclude)` 있음 | `mx` |
| `mx or da Order (Exclude)` 있음 | `vd` |
| `mx or vd Order (Exclude)` 있음 | `da` |
| `[Global] MX Order` + `[Global] VD Order` (individual 2개 이상) | `mx_vd` 등 살아남는 라인 조합 |
| `MX & VD & DA Order (Exclude)` 만 있고 individual 없음 | `total` |
| campaign segment 있음 | `campaign` |
| 그 외 | `scom` (default) |

**suffix:**
- `context=cmp` (5_3) → `cmporder` (campaign + cmporder 중복 회피)
- tb 이름에 `multi_order` 토큰 또는 `Unit >= 2` segment → `multiorder`
- 그 외 (5_2) → `order`

---

## 비교 컬럼 (`FILLED_CSV` 있을 때 자동 추가)

| 컬럼 | 값 |
|---|---|
| `match_filled` | `일치` / `불일치` / `미해석` / `비교불가` |
| `diff_field` | 불일치 시 어느 토큰 (`section`, `device`, `item`, `measure,item` 등 콤마 join) |

spreadsheet 에서 `match_filled` 필터링 + `diff_field` 정렬로 패턴별 분류 가능.

---

## 사용자 환경에 맞게 수정할 부분

| 항목 | 위치 |
|---|---|
| 경로 | `NEW_CSV`, `FILLED_CSV` |
| baseline segment prefix (`[Global]` / `[YOUR_TEAM]` 등) | `_GLOBAL_SEG_RE` |
| Internal_* segment 축약 매핑 | `_INTERNAL_SLUG_MAP` |
| metric 단/복수 normalize 매핑 | `_METRIC_SINGULAR_MAP` |
| section list (visit-base / order-base / cross-sell / channel-dimension) | `_VISIT_BASE_SECTIONS` / `_ORDER_BASE_SECTIONS` / `_CROSS_SELL_SECTIONS` / `_CHANNEL_DIMENSION_SECTIONS` |
| reportlet cell 별칭 패턴 (Campaign Page → main 등) | `_build_4_2_item_alias` |

---

## 자매 도구

- `extract_panel_tables_json_v2.0.py` (상위 폴더) — Workspace project 의 panel × reportlet → JSON + 매핑 CSV 자동 생성 (segments + metric 컬럼 포함)
- `fill_column_by_similarity.py` (다른 repo: AA-Segments-Maker-by-API/column_filler) — 이전 시즌의 column 컬럼 정리본을 reference 로 similarity 기반 채움. 본 generator 와 결합해서 비교 가능 (`FILLED_CSV` 지정 시 자동 비교).
