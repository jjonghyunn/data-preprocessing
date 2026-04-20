# RESHAPE_main_raw_v4.1.ipynb

작성일: 2026-04-20 / Jonghyun Park w/ Claude  
이전 버전: `RESHAPE_main_raw_v4.ipynb`

---

## 개요

캠페인 raw CSV(aa_exports)를 읽어 long format으로 변환 후 union CSV를 생성하는 후처리 스크립트.  
v4.1에서는 **파일 간 site 누락 문제**를 post-union dummy 삽입(FIX-10)으로 해결.

---

## 버전 이력

| 버전 | 날짜 | 주요 변경 |
|---|---|---|
| v3 | 이전 | 글로벌 마스터 기준 dummy 삽입 |
| v4 | 2026-04-17 | [FIX-9] dummy 범위를 파일 내 실제 site로 제한 |
| v4.1 | 2026-04-20 | [FIX-10] post-union dummy 추가 (파일 간 누락 보완) |

---

## FIX-10 상세: Post-union dummy

### 문제

FIX-9에서 파일 내 실제 site만 대상으로 dummy를 생성하도록 변경했으나,  
**특정 파일 자체에 없는 site**는 해당 tb_key의 metric_col dummy가 아예 생성되지 않았음.

예시 — `3_1_external_smartthings_cmp` 파일에 없는 site:
- AE_AR, IL, MX, PE, TH (5개)
- → union에서 smartthings 관련 KEY가 통째로 0개

### 해결

union 생성 후 `J11(REPORT NO.)` 기준으로 그룹핑 → 각 그룹에서  
`전체 site × 전체 metric_col` cross product → 누락 조합만 value=0으로 삽입.

```
union_df
  └─ groupby J11
       └─ 각 REPORT NO.별: all_sites × all_metric_cols
            └─ _exists 체크 → 누락 조합만 dummy(0) 삽입
```

- 기존 조합은 `_exists` 체크로 중복 삽입 방지
- 메타(Subsidiary, Country, RSID, Start_Date, End_Date)는 site별 mode 값으로 채움
- J1~J11, metric_name, PAID_NONPAID는 metric_col별 기존 값 참조

### 효과

동일 REPORT NO. 내 모든 site가 동일한 metric_col 집합을 가짐  
→ union 행수 증가, KEY 기준 vlookup/피벗 정합성 확보

---

## 실행 순서

1. `aa_exports/` 폴더에 SQL 뽑은 raw CSV 준비 (Non-prior / Prior / Last-year + FAILED 수기처리 후)
2. 셀 실행
3. `aa_exports/union_YYYYMMDD_HHMMSS.csv` 확인

---

## 주요 참조 파일

| 경로 | 용도 |
|---|---|
| `../ref/tb_column_name_mapping.csv` | metric_col → column명 매핑 |
| `../ref/currency.csv` | 환율 (site_code별 연도별) |
| `../ref/app_O_X.csv` | App 없는 site 목록 |
| `../aa_exports/*.csv` | 입력 raw CSV |
| `../aa_exports/union_*.csv` | 출력 결과 |
