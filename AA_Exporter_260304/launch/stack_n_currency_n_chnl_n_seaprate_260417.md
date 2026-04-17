# 정제코드.ipynb (POST-PROCESSING v4)
<!-- 2026-04-17  Jonghyun Park w/ Claude -->

AA Exporter로 추출한 CSV를 정제·변환하여 union 결과물을 생성하는 스크립트.  
베이스: `stack_n_currency_n_chnl_n_seaprate_(by종현과장님)v3.2.ipynb`

---

## v3.2 vs v4 비교

### 같은 것

- `is_us_table`: `us_` 또는 `last_us_` 로 시작하면 US 테이블
- `is_channel`: 매핑 CSV column명이 `_`로 끝나면 channel 테이블
- App 없는 site 0처리 (`app_O_X.csv` 기반, J5=app/android/ios 행 값 0처리)
- Revenue 환율 연도 기준: `End_Date`
- 글로벌 테이블에서 US site 행 제거 (us_ 테이블과 KEY 중복 방지)
- Union US dummy: `_missing_for_us = _non_us_mc - _us_mc` 로직
- `finalize_df`, `_apply_j_cols`, year-split, `us_mapping`, `global_paid_mapping`

---

### 다른 것

| 항목 | v3.2 | v4 |
|---|---|---|
| **dummy 삽입 기준** | `_global_sites` 전체 마스터 기준 | 파일 내 실제 존재하는 site만 |
| **`_global_sites` pre-scan** | 수집 후 `_global_sites -= _us_sites` | 제거 — `_us_sites`만 수집 |
| **`_insert_nonchannel_dummy` 시그니처** | `(df_long, tb_key, master_sites, site_meta_map)` | `(df_long, tb_key, site_meta_map)` |
| **channel dummy 기준** | `master = _global_sites or _us_sites` | `df_long["Site_Code"].unique()` |
| **`_TS_PAT` 타임스탬프 정규식** | `\d{4}` 고정 (HHMM) | `\d{4,6}` (HHMM/HHMMSS 모두 허용) |
| **pre-scan tb_key 추출 정규식** | `\d{6}` 고정 (버그 잔존) | `\d{4,6}` |
| **FIX-5 Global/US overlap 체크 로그** | 있음 | 제거 (`_global_sites` 자체가 없어짐) |
| **nextpage 분할 파일 병합** | 없음 | `_ttlmx + _vdda` → `next_page` 자동 병합 |
| **`_TB_KEY_REMAP`** | 없음 | 있음 (`6_2_..._prior` → `6_3_...`) |
| **MAPPING_CSV 파일명** | `tb_column_name_mapping.csv` | `tb_column_name_mapping_MD.csv` |
| **`report_no_mapping`** | CAMPAIGN NAME 캠페인용 (1_1~5_1) | Mothers Day 캠페인용 (0_1~6_3) |
| **dummy 로그 메시지** | `N행 삽입` | `N행 삽입 (파일 내 M개 site 기준)` |

---

### dummy 삽입 기준 변경 상세

**문제 (v3.2)**  
Pre-scan으로 캠페인 전체 파일에 등장하는 모든 나라를 `_global_sites`에 수집 →
각 테이블에 그 전체 목록 기준으로 dummy 삽입  
→ 해당 테이블에 실제 없는 나라까지 0으로 채워져 피벗 열이 밀리는 문제

```python
# v3.2 — 전체 마스터 기준
master = _us_sites if _is_us_table(tb_key) else _global_sites
df_long = _insert_nonchannel_dummy(df_long, tb_key, master, _site_meta_map)
```

**변경 (v4)**  
해당 파일의 df_long에 실제 존재하는 site만 대상으로 dummy 삽입  
non-channel / channel / union US dummy 모두 동일 원칙 적용

```python
# v4 — 파일 내 실제 site 기준
df_long = _insert_nonchannel_dummy(df_long, tb_key, _site_meta_map)

# _insert_nonchannel_dummy 내부
all_sites = list(df_long["Site_Code"].str.strip().unique())
```

---

### nextpage 분할 파일 병합 (v4 신규)

AA에서 next_page 쿼리가 두 파일(`_ttlmx`, `_vdda`)로 분리 출력되는 경우 처리 전 자동 병합.

| 분할 A | 분할 B | 병합 결과 |
|---|---|---|
| `next_page_ttlmx` | `next_page_vdda` | `next_page` |
| `last_next_page_ttlmx` | `last_next_page_vdda` | `last_next_page` |
| `us_next_page_ttlmx` | `us_next_page_vdda` | `us_next_page` |
| `us_last_next_page_ttlmx` | `us_last_next_page_vdda` | `us_last_next_page` |

---

### `_TB_KEY_REMAP` (v4 신규)

파일명과 매핑 CSV `tb`명이 다른 경우를 위한 보정 딕셔너리.

```python
_TB_KEY_REMAP = {
    "6_2_order_by_channel_scom_prior": "6_3_order_by_channel_scom_prior",
}
```

---

## 전체 처리 흐름

```
aa_exports/*.csv
    │
    ├─ tb_key별 최신 파일 선택 (_TS_PAT deduplication)
    ├─ nextpage 분할 파일 병합 (_ttlmx + _vdda → merged)   ← v4 신규
    │
    ├─ [Pre-scan] site 메타 정보 + US site 목록 수집
    │
    └─ [메인 루프] tb_key별 처리
          ├─ _TB_KEY_REMAP 적용                              ← v4 신규
          ├─ 매핑 CSV 기반 컬럼 rename
          ├─ melt → long 변환
          ├─ 글로벌 테이블에서 US site 행 제거
          ├─ currency 환율 적용 (End_Date 연도 기준)
          ├─ _apply_j_cols (J1~J7, J11 분리)
          ├─ App 없는 site App device type 0처리
          ├─ channel 테이블 → channel_frames 분리
          └─ non-channel 테이블
                ├─ year-split 합산
                ├─ 파일 내 site 기준 dummy 0 삽입           ← v4 변경
                └─ _stacked_separate.csv 저장

    ├─ [channel 후처리]
    │     ├─ US channel value 치환
    │     ├─ 파일 내 site 기준 dummy 0 삽입                 ← v4 변경
    │     ├─ PAID_NONPAID 부여
    │     └─ _stacked_separate.csv 저장
    │
    └─ union 생성
          ├─ all_frames concat
          ├─ US dummy 보완 (실제 존재 site 기준)
          └─ union_YYYYMMDD_HHMMSS.csv 저장
```

## 참조 파일 (ref/)

| 파일 | 용도 |
|---|---|
| `tb_column_name_mapping_MD.csv` | AA export value_n → column명 매핑 |
| `currency.csv` | site별 연도별 환율 (revenue 컬럼에 적용) |
| `app_O_X.csv` | App 없는 site 목록 (B열 X → app device 0처리) |
