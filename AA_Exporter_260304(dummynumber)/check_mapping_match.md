# check_mapping_match.py -- 2026 03 10 jonghyun

aa_exports 폴더의 CSV 파일들이 tb_column_name_mapping.csv와 컬럼 레벨로 정상 매핑되는지 검수합니다.

## 실행 목적
AA 추출 후, tb_column_name_mapping.csv 기준으로 실제 CSV 컬럼과 매핑이 제대로 맞는지 사전에 확인합니다.
매핑이 맞지 않으면 stack_n_currency_n_chnl_n_seaprate 노트북 실행 시 value_vars=[] 오류 또는 누락 발생.

## 검사 항목 (5가지 상태)
- ✅ 정상: 매핑 value_n ↔ CSV value 컬럼 완전 일치
- ⚠️ 매핑초과(CSV부족): tb_column_name_mapping의 value_n이 CSV보다 많음 → 매핑은 있는데 CSV에 해당 컬럼 없음
- ⚠️ CSV초과(매핑누락): CSV에 value19~20 이상 등이 있는데 tb_column_name_mapping에 없음 → 매핑 추가 필요
- ⚠️ 양쪽불일치: 매핑초과 + CSV초과 동시 발생
- 🔴 전혀불일치: matched 0개 → value_vars=[] → metric_name KeyError 원인
- ❌ 매핑없음: tb_column_name_mapping에 해당 tb 항목 자체 없음 → skip 대상

## 기존 버전(260306 이전)과의 차이
기존에는 `⚠️ 일부 누락` 1가지로만 표시되어 어느 쪽이 더 많은지 불분명했음.
- 매핑 > CSV (매핑이 더 많음) 인지
- CSV > 매핑 (CSV가 더 많음, value19~20+ 등) 인지
위 두 케이스를 명확히 분리해서 표시하도록 개선.

## 결과 저장
결과는 mapping_match_report 폴더에 저장됩니다.
_all_check.csv 파일을 보시면 됩니다.

출력 컬럼:
tb_key / file / status / matched_cnt / mapping_only_cnt / csv_only_cnt / matched / mapping_only / csv_only

- matched: 매핑과 CSV 양쪽에 있는 value_n 목록
- mapping_only: 매핑에만 있고 CSV에는 없는 value_n 목록 → CSV 컬럼 부족
- csv_only: CSV에만 있고 매핑에는 없는 value_n 목록 → tb_column_name_mapping 추가 필요

## 파일 탐색 범위
aa_exports 루트 폴더의 CSV 파일만 검사합니다.
날짜 하위폴더(260224, 260226 등) 안의 파일은 무시합니다. (동일 tb_key 중복 방지 목적)
_stacked, _long, union_ 으로 시작하는 파일은 제외 (정제 결과물이므로 검사 대상 아님).

SEARCH_SUBDIRS = True 로 변경 시 하위폴더까지 포함되나, 같은 tb_key가 날짜별로 여러 개 잡혀 중복 결과가 나올 수 있으므로 권장하지 않음.

## 조치 방법
| 상태 | 조치 |
|------|------|
| ⚠️ 매핑초과(CSV부족) | AA 추출 시 해당 value_n 컬럼이 실제로 없는지 확인. 없으면 tb_column_name_mapping에서 해당 행 제거 또는 플레이스홀더 표시 |
| ⚠️ CSV초과(매핑누락) | CSV의 csv_only 컬럼(value19~20 등)을 tb_column_name_mapping에 추가 필요 |
| 🔴 전혀불일치 | tb_column_name_mapping의 value_n 컬럼명 자체가 잘못됨. AA 추출 CSV 헤더와 비교하여 수정 필요 |
| ❌ 매핑없음 | tb_column_name_mapping에 해당 tb 행 추가 필요 (또는 의도적 skip이면 무시) |
