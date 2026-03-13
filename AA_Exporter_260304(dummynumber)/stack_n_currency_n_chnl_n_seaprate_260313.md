# API 정제 코드 -- 2026 03 13 jonghyun
* 아래 6개 주피터파일로 api추출.
01.26ny_campaign_period.ipynb
02.25ny_last_campaign_period.ipynb
03.26ny_prior_period.ipynb
04.us_26ny_campaign_period.ipynb
05.us_25ny_last_campaign_period.ipynb
06.us_26ny_prior_period.ipynb

* 이 프로젝트 US는 AA Report Suite 따로 있음.

보조작업 파일 1:
이 과정에서 failed가 어떤 파일마다 한번에 있는지 보면 편하다는 생각에 check_failed_status_260313.py도 추가 했습니다.
(돌리면 어떤 csv파일에 몇건의 failed가 있는지 확인 가능. UK 등 VRS가 이런 문제가 있었는데요, 수기로 AA들어가서 넣는 경우를 고려하고 만들었습니다.)
US 파일의 경우 FAILED 여부와 별개로 OK 데이터 행이 0개인 경우도 별도로 경고합니다.

* 추출 후 작업
1. VRS site 등 빠진 site의 value#값까지 csv에서 채운다.
2. stack_n_currency_n_chnl_n_seaprate_260313.ipynb 파일을 실행한다.
3. aa_exports폴더 내 union_{연월일}_{시분초}.csv파일을 확인한다.

* 추출 후 작업 흐름
1. 고객 전달 엑셀 양식처럼 value#를 1줄(1개 칼럼)로 만드는 파일을 생성하고 파일명_stacked_separate.csv (뒤 날짜,시간은 제거됨)
2. us 채널을 글로벌 채널로 정제한 뒤 (US는 RS가 달라서 channel명도 다르게 쌓이는 상태.)
3. 피봇 때 같은 채널 개수가 되도록 더미 채널을 전체 추가한 후 (나라마다 channel 개수가 다름)
4. union_날짜_시간.csv파일을 생성해서 전달 엑셀 양식 raw와 같은 칼럼명,순서로 뽑아내는 걸 만들었습니다.
   (테이블별로 수정할일 생길까봐 각각도 만듦.)
   4-1. union만드는 과정에서 ITEM칼럼에 visit이나 home_gnb_tocmp 등 과 같은 값이 잘 안 나오던 점과 추출되었던 bestselling이나 multi-order 등도 union시킨 케이스를 다시 제외시키는 점까지 개선했습니다.

* 260313 변경사항
- aa_exports 내 같은 tb_key의 CSV 파일이 여러 개인 경우, 파일명의 날짜_시간 기준으로 가장 최신 파일만 처리하도록 수정
  → 이전: 동일 tb_key 파일이 여러 개면 전부 처리 (덮어쓰기로 결과 불확실)
  → 이후: tb_key별 최신 1개만 선택 후 처리

* 260306 변경사항
- `value_vars`가 완전히 비어있을 때(매핑 value_n이 실제 CSV 컬럼과 전혀 안 맞는 경우) 에러 대신 skip 처리하고 결과 요약에 별도 보고하도록 수정
  → `⚠️ 매핑컬럼 불일치 skip` 항목으로 출력됨
  → 원인: tb_column_name_mapping.csv의 value_n이 '이번에 없음' 등 플레이스홀더인 경우 발생
- `finalize_df()` 함수 신규 적용: channel 파일 및 union 최종 저장 시 컬럼명 rename + 순서 고정
  → 이전: `df_long.to_csv(...)` 직접 저장 → 이후: `finalize_df(df_long).to_csv(...)`
- union 생성 시 US dummy 행 자동 삽입 로직 추가
  → non-US에 `_app/_android/_ios` metric_col이 존재하는데 US에 없는 경우 → US에 해당 metric_col 0행 자동 삽입

* 출력 컬럼 구조 (finalize_df 기준)
TIER, SUBS, COUNTRY, SITE CODE, REPORT NO., DIVISION, DATE, DEVICE TYPE, TYPE, LOGIN/NON, PAID/NONPAID, ITEM, VALUE, KEY, 공란1, 공란2, 공란3, 공란4, value_origin, start_date, end_date
- KEY = SITE CODE(소문자) + "_" + metric_col

보조작업 파일 2:
ipynb_json_usage_mapper.py
json파일 따온 걸 api추출용 주피터파일(위 6개)에서 다 사용한게 맞는지 확인하는 코드입니다. (json열심히 따놓고 누락된 게 있는지 확인용)
결과는 json_usage_report폴더에 저장됩니다.
_all_check.csv파일을 보시면 됩니다.
(json폴더 + tb_column_name_mapping.csv 합집합 기준 3방향 검수)

보조작업 파일 3:
check_mapping_match_260313.py
aa_exports 폴더의 CSV 파일들이 tb_column_name_mapping.csv와 컬럼 레벨로 정상 매핑되는지 검수합니다.
같은 tb_key 파일이 여러 개인 경우 최신 파일 기준으로 검사합니다.
- ✅ 정상: 매핑 컬럼 완전 일치
- ⚠️ 매핑초과(api 추출 된 CSV부족): 매핑에 있는 컬럼 일부가 CSV에 없음
- ⚠️ CSV초과(tb_column_name매핑누락): CSV에 있는 value 컬럼이 매핑에 없음
- ⚠️ 양쪽불일치: 매핑초과 + CSV초과 동시 발생
- 🔴 전혀불일치: value_vars=[] → metric_name KeyError 원인
- ❌ 매핑없음: skip 대상
