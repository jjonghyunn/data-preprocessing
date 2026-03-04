# data-preprocessing
preprocessing data

## **AA_Exporter_260304(dummynumber)**
* 보안을 위해 추출된 value#칼럼들의 숫자값들은 모두 dummy화 했습니다.

아래 3개 주피터파일로 api추출.
           26ny_campaign_period.ipynb
           26ny_prior_period.ipynb
           25ny_last_campaign_period.ipynb
(현재 작업 중이던 프로젝트 최종업데이트 us가 없어서 다 돌릴 경우 us용 주피터파일까지 3개정도 더 만들 수 있을 거 같습니다. 그러면 총 6개.) * 이 프로젝트 US는 AA Report Suite 따로 있음.
* 보조작업 파일 1:
   이 과정에서 failed가 어떤 파일마다 한번에 있는지 보면 편하다는 생각에 check_failed_status.py도 추가 했습니다. 
   (돌리면 어떤 csv파일에 몇건의 failed가 있는지 확인 가능. UK 등 VRS가 이런 문제가 있었는데요, 
   수기로 AA들어가서 넣는 경우를 고려하고 만들었습니다.)

* 추출 후 작업
1. VRS site 등 빠진 site의 value#값까지 csv에서 채운다. 
2. stack_n_currency_n_chnl_n_seaprate_260304.ipynb 파일을 실행한다.
3. aa_exports폴더 내 union_{연월일}_{시분초}.csv파일을 확인한다.

* 추출 후 작업 흐름
1. 고객 전달 엑셀 양식처럼 value#를 1줄(1개 칼럼)로 만드는 파일을 생성하고 파일명_stacked_separate.csv (뒤 날짜,시간은 제거됨)
2. us 채널을 글로벌 채널로 정제한 뒤 (US는 RS가 달라서 channel명도 다르게 쌓이는 상태.)
3. 피봇 때 같은 채널 개수가 되도록 더미 채널을 전체 추가한 후 (나라마다 channel 개수가 다름)
4. union_날짜_시간.csv파일을 생성해서 전달 엑셀 양식 raw와 같은 칼럼명,순서로 뽑아내는 걸 만들었습니다. (테이블별로 수정할일 생길까봐 각각도 만듦.)
4-1. union만드는 과정에서 ITEM칼럼에 visit이나 home_gnb_tocmp 등 과 같은 값이 잘 안 나오던 점과 
추출되었던 bestselling이나 multi-order 등도 union시킨 케이스를 다시 제외시키는 점까지 개선했습니다.

* 보조작업 파일 2:
ipynb_json_usage_mapper.py
json파일 따온 걸 api추출용 주피터파일(위3개)에서 다 사용한게 맞는지 확인하는 코드입니다. (json열심히 따놓고 누락된 게 있는지 확인용)
결과는 json_usage_report폴더에 저장됩니다. _all_json_mapping.csv파일을 보시면 되겠습니다.
