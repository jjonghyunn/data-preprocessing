# RESHAPE_main_raw_v4.3.ipynb

작성일: 2026-05-13 / Jonghyun Park w/ Claude  
이전 버전: `RESHAPE_main_raw_v4.2.ipynb`

---

## 개요

캠페인 raw CSV(aa_exports)를 읽어 long format으로 변환 후 union CSV를 생성하는 후처리 스크립트.  
v4.3에서는 **v2.0 dash-form column** (`1-1_all_2026_cmp_pc_visit_null_uniquevisitor` 형식) 도 v4.2의 underscore-form (`1_1_all_2026_...`) 과 동일하게 분해할 수 있도록 `split_metric_col` / `_find_report_key` 정규화 로직 추가 (FIX-12).

---

## 버전 이력

| 버전 | 날짜 | 주요 변경 |
|---|---|---|
| v3 | 이전 | 글로벌 마스터 기준 dummy 삽입 |
| v4 | 2026-04-17 | [FIX-9] dummy 범위를 파일 내 실제 site로 제한 |
| v4.1 | 2026-04-20 | [FIX-10] post-union dummy 추가 (파일 간 누락 보완) |
| v4.2 | 2026-04-23 | [FIX-11] 추출 0행 fallback dummy 추가 |
| v4.3 | 2026-05-13 | [FIX-12] v2.0 dash-form column 지원 |

---

## FIX-12 상세: v2.0 dash-form column 지원

### 배경

`generate_column_from_segments_v2.0.py` (dash-join 컨벤션) 으로 생성된 매핑 CSV 는 column 값이 다음 형식:

```
1-1_all_2026_cmp_pc_visit_null_uniquevisitor       (section 이 '1-1' 한 토큰)
4-2_all_2026_cmp_mobile_revenue_login_main-then-pd-all-rev
5-1_all_2026_scom_pc_order_null_mx-vd-multiorder
6-0_all_2026_scom_total_visit_null_internal-gnb-l0
```

v4.2 의 `split_metric_col` 은 section 이 `\d{1,2}_\d{1,2}` 두 토큰 (`1` `_` `1`) 으로 들어온다고 가정 — dash-form 인 `1-1` 한 토큰이 들어오면 `_split_by_number_pattern` 매칭 실패로 분해가 망가지고 `report_no_mapping` lookup 도 실패 (J11 빈 값).

### 해결

#### 1) `split_metric_col` 진입부에 dash→underscore 정규화 1줄 추가

```python
s = re.sub(r'^(\d{1,2})-(\d{1,2})_', r'\1_\2_', str(val))
parts = s.split('_')
```

첫 토큰의 `X-Y_` 만 `X_Y_` 로 치환. 이후 multi-word slug 내부의 `-` (예: `main-then-pd-all-rev`) 는 그대로 유지되어 마지막 토큰 (`metric_name`) 슬롯에 한 덩어리로 들어감.

#### 2) `_find_report_key` — dash-form 매칭 + lookup 정규화

```python
def _find_report_key(values):
    for v in values:
        if isinstance(v, str) and re.fullmatch(r"\d+[-_]\d+", v):
            return v.replace("-", "_")
    return ''
```

### 효과

| input column | J2 | J4 (DATE) | J7 | J11 | metric_name |
|---|---|---|---|---|---|
| `1-1_all_2026_cmp_pc_visit_null_uniquevisitor` | `1_1` | `2026_cmp` | `null` | `1_1. Basic Traffic` | `uniquevisitor` |
| `4-2_all_2026_cmp_mobile_revenue_login_main-then-pd-all-rev` | `4_2` | `2026_cmp` | `login` | `4_2. Order Conversion ...` | `main-then-pd-all-rev` |
| `5-1_all_2026_scom_pc_order_null_mx-vd-multiorder` | `5_1` | `2026_scom` | `null` | `5_1. S.com Cross Sell ...` | `mx-vd-multiorder` |
| `6-0_all_2026_scom_total_visit_null_internal-gnb-l0` | `6_0` | `2026_scom` | `null` | (6_0 미등록) | `internal-gnb-l0` |
| `2-2_all_2026_scom_pc_visit_null_` (channel trail) | `2_2` | `2026_scom` | `null` | `2_2. Traffic by Channel (External)` | `` |

v1 underscore-form (`1_1_all_2026_...`) 도 그대로 호환 — 정규화 패턴은 첫 토큰의 `X-Y_` 만 매칭하므로 underscore-form 은 영향 없음.

### 다운스트림 주의사항

- `metric_name` 슬롯에 v2.0 식 `main-then-pd-all-rev`, `mx-vd-multiorder` 같은 dash 결합 slug 가 들어감. v1 식 `main_then_pd_all_rev`, `mx_vd_multiorder` 와 동일 의미이나 문자열 비교 시 다름.
- `J4` (DATE) 의 prior 표시: v1 `2026_scom_prior` → v2.0 `2026_scom-prior` 형식. `endswith("prior")` / `"prior" in J4` 등 substring 검사는 둘 다 통과하나, 토큰 단위 split 시 다름.

---

## 실행 순서

1. `aa_exports/` 폴더에 SQL 뽑은 raw CSV 준비 (Non-prior / Prior / Last-year + FAILED 수기처리 후)
2. `../ref/tb_column_name_mapping.csv` 의 `column` 컬럼이 v1 underscore-form 인지 v2.0 dash-form 인지 무관하게 작동
3. 셀 실행
4. `aa_exports/union_YYYYMMDD_HHMMSS.csv` 확인

---

## 주요 참조 파일

| 경로 | 용도 |
|---|---|
| `../ref/tb_column_name_mapping.csv` | metric_col → column명 매핑 (v1 또는 v2.0 form 어느 쪽이든 OK) |
| `../ref/currency.csv` | 환율 (site_code별 연도별) |
| `../ref/app_O_X.csv` | App 없는 site 목록 |
| `../aa_exports/*.csv` | 입력 raw CSV |
| `../aa_exports/union_*.csv` | 출력 결과 |
