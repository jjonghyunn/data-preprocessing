# SQL 쿼리 모음
<sub>2026-07-14  Jonghyun Park w/ Claude</sub>  

구글드라이브 `study_SQL` 아카이브에서 정리한 SQL 쿼리 모음 (BigQuery · Adobe Analytics 패널 기반).
총 **40개 쿼리 / 9개 카테고리**. 각 `.sql` 상단 주석에 원본 출처·날짜를 기록.

> 회사 식별자(도메인·스키마·캠페인명 등)는 출처 시기 구분 없이 placeholder(`company_name`, `CAMPAIGN NAME` 등)로 sanitize 처리함. `⊘` = 현직장(2024-05 이후) 출처 파일 표시.

## 01_ddl_dml_basics
기본 DDL·DML — CREATE/ALTER/UPDATE/DELETE, UNION 테이블 생성

| 파일 | 원본 출처 | 설명 |
|---|---|---|
| `create_column_add_manufacturer.sql` ⊘ | create_column.sql (2024-06) | 제조사별 지표 컬럼(company_name/Co.A/Cbrand/Google/Others)을 원본 테이블에 추가하는 ALTER TABLE |
| `create_column_date_only.sql` ⊘ | create_column2.sql (2024-08) | day 테이블에 DATE 타입 date_only 컬럼을 NULL 값으로 추가 |
| `create_table_combine_monthly.sql` ⊘ | create_combine.sql (2024-06) | 월별(2401~2405) 테이블을 UNION ALL 로 합쳐 단일 통합 테이블 생성 |
| `create_table_union_re4_mnfctrr.sql` ⊘ | create_table.sql (2024-06) | 두 가공 테이블(re4 / mnfctrr)을 UNION 하여 신규 통합 테이블 생성 |
| `delete_value_model6.sql` ⊘ | delete_value.sql (2024-07) | extra 컬럼 값이 특정 옵션인 행을 DELETE |
| `select_member_by_gender_addr.sql` | study_230808.sql (2023-08) | Member 테이블에서 성별 필터 조회 및 주소(addr)별 회원수 집계 (SQL 기초 학습) |
| `update_value_device_total.sql` ⊘ | update_value.sql (2024-06) | device 값 'All' 을 'Total' 로 일괄 UPDATE |
| `update_value_manufacturer_device.sql` ⊘ | value_column.sql (2024-06) | Manufacturers/device1 컬럼 값을 'Total' 로 UPDATE |

## 02_window_functions
윈도우 함수 — ROW_NUMBER·SUM/MAX OVER(PARTITION BY)

| 파일 | 원본 출처 | 설명 |
|---|---|---|
| `max_over_row_number_ranking.sql` ⊘ | 250404-max,row_number.sql (2025-04) | site_code별 카운트에 ROW_NUMBER 순위 부여 후 MAX() OVER 전체 최대값 계산 (윈도우 함수 학습) |
| `row_number_sum_over_partition.sql` ⊘ | orderbystudy.sql (2024-06) | ROW_NUMBER 로 파티션 내 순위 부여 + SUM() OVER 로 site_code별 누적 합 계산 (윈도우 함수 학습) |

## 03_union_pivot
UNION·Unpivot — device/제조사 컬럼 정규화, aa-panel union

| 파일 | 원본 출처 | 설명 |
|---|---|---|
| `carttoadd_per_visits_filter.sql` ⊘ | 240520_study1.sql (2024-05) | 장바구니 담기/방문 지표 테이블에서 visits 5백만 이상 행만 필터 |
| `union_device_all_pc_mobile.sql` ⊘ | union_aa-panel.sql (2024-06) | 원본 테이블의 all/pc/mobile 디바이스별 지표를 device 축으로 UNION ALL 정규화 후 테이블 생성 |
| `union_manufacturer_breakdown.sql` ⊘ | union_aa-panel2.sql (2024-06) | 제조사(company_name/Co.A/Cbrand/Google/Others)별 지표 컬럼을 Manufacturer 축으로 UNION ALL 정규화 후 테이블 생성 |
| `unpivot_os_visit_union_all.sql` ⊘ | 240610_us_div1_visit_user_id2.sql (2024-06) | OS(ios/and/others/ALL)별 방문값을 UNION ALL 로 세로 전개(unpivot)하는 쿼리 |

## 04_page_path_session
페이지 경로·세션 플로우 — 이전경로, LAG/LEAD 흐름 분석

| 파일 | 원본 출처 | 설명 |
|---|---|---|
| `home_idea_landing.sql` | 홈아이디어 랜딩(오가닉 파악) 쿼리문 231206 / 개량 버전 (2023-11) | LAG로 직전 url 유무를 판단해 홈아이디어 페이지의 랜딩(오가닉 유입) pcid/세션 수 산출 (개량본) |
| `prev_next_path_lag_lead_flow.sql` | 이전 path 추출쿼리 / 시트2 (2023-10) | module/snb 파싱 + 경로 정규화 후 LAG/LEAD로 세션 내 이전/현재 경로 이동 플로우 및 종료율 산출 |
| `prev_path_by_referrer.sql` | page_path_이전경로 / 시트1 (2023-11) | referr_path 기준 이전 페이지 → 현재 url_path 이동 조합별 PV·세션·PCID 집계 (상품상세 referrer 필터) |
| `prev_path_by_referrer_product_detail.sql` | 이전 path 추출쿼리 / 상품상세기준 (2023-11) | 상품상세를 referrer로 하는 이전→현재 페이지 이동 조합별 PV·세션·PCID 집계 |
| `session_flow_check_q1_raw.sql` | 쿼리테스트-이후세션플로우정합성용 240206 / 1퀄 (2024-01) | 세션플로우 정합성 검증 1단계: 특정 콘텐츠(seq=27410) referrer 로그 원본 조회 |
| `session_flow_check_q2_lead.sql` | 쿼리테스트-이후세션플로우정합성용 240206 / 2퀄 (2024-01) | 세션플로우 정합성 검증 2단계: LEAD로 세션 내 직후 url 추가, seq=27410 유입 로그 조회 |
| `session_flow_check_q3_filtered.sql` | 쿼리테스트-이후세션플로우정합성용 240206 / 3퀄 (2024-01) | 세션플로우 정합성 검증 3단계: LEAD 결과를 homeIdeaDetail 페이지로 필터해 세션 단위 조회 |
| `session_flow_check_q5_aggregated.sql` | 쿼리테스트-이후세션플로우정합성용 240206 / 5퀄 (2024-01) | 세션플로우 정합성 검증 5단계: 직후 url 조합별 고유 세션 수 집계 (최종 집계형) |
| `session_flow_check_q6_raw_by_url.sql` | 쿼리테스트-이후세션플로우정합성용 240206 / 6퀄-세션2915나오도록 (2024-01) | 세션플로우 정합성 검증 6단계: 특정 콘텐츠 url(seq=27410) 직접 방문 로그 원본 조회 (세션 수 대조용) |
| `session_flow_check_q7_lead_by_params.sql` | 쿼리테스트-이후세션플로우정합성용 240206 / 7퀄 (2024-01) | 세션플로우 정합성 검증 7단계: params_origin 기준 LEAD 적용 후 특정 콘텐츠 url 로그 조회 |

## 05_campaign_conversion
기획전 컨버전 — 직후페이지(1~3단계), 버튼클릭 지표

| 파일 | 원본 출처 | 설명 |
|---|---|---|
| `campaign_button_click_metrics.sql` | 기획전 버튼클릭 240122 / 시트1 (2024-01) | 기획전 종합 지표: 트래픽·이탈률·종료율 + 내비게이션 탭/매장상담/플로팅배너 버튼 클릭수 집계 |
| `campaign_conversion_next_page_1step.sql` | 기획전 컨버전페이지 240130 / 쿼리문 (2024-01) | 기획전 url_path 방문 세션의 직후(1step) 이동 url을 LEAD로 추출해 세션 수 집계 |
| `campaign_conversion_next_page_2step.sql` | 기획전 컨버전페이지 240130 / 쿼리문-2단계 (2024-01) | 기획전 방문 세션의 직후 2단계(2·3번째) 이동 url을 LEAD로 추출해 세션 수 집계 |
| `campaign_conversion_next_page_3step.sql` | 기획전 컨버전페이지 240130 / 쿼리문-3단계 (2024-01) | 기획전 방문 세션의 직후 3단계(2·3·4번째) 이동 url을 LEAD로 추출해 세션 수 집계 |
| `campaign_metrics_nav_button_clicks.sql` | 기획전 데이터(정확성 미확인)의 사본 / 시트2 (2024-01) | 기획전 종합 지표: 트래픽·이탈률·종료율 + 내비게이션 탭/매장상담/플로팅배너 등 액션 버튼 클릭수 집계 |
| `campaign_metrics_new_product_clicks.sql` | 기획전 데이터(정확성 미확인)의 사본 / 시트1 (2024-01) | 기획전 종합 지표: 트래픽·이탈률(BounceRate)·종료율(ExitRate) + 신상 배너 클릭수 집계 |
| `campaign_next_page_dual_plan.sql` | 기획전 컨버전페이지(직후페이지) 240130 / 2개조회-쿼리문 (2024-01) | PC·MO 기획전 두 개를 함께 조회해 방문 세션의 직후 이동 url을 LEAD로 추출, 세션 수 집계 |
| `campaign_next_page_single_plan.sql` | 기획전 컨버전페이지(직후페이지) 240130 / 1개조회-쿼리문 (2024-01) | 단일 기획전(PC 또는 MO 하나) 방문 세션의 직후 이동 url을 LEAD로 추출해 세션 수 집계 |

## 06_search_keyword
검색 키워드 — searchKey 클릭 PV, 검색 유입 이전경로

| 파일 | 원본 출처 | 설명 |
|---|---|---|
| `search_keyword_prev_path.sql` | 검색키워드별 이전경로 page_path 추출쿼리 / 시트1 (2023-11) | 현재/referrer/직전(LAG) 순으로 searchKey를 보간하여 검색 페이지 유입 후 도달한 url_path별 PV 집계 |
| `search_keyword_pv.sql` | searchKey 240205 / 시트1 (2024-02) | url에서 searchKey 파라미터를 추출해 검색 키워드별 클릭 PV 집계 (상위 100000건) |

## 07_product
상품 — 상품코드/명, 상품태그·정보펼치기 클릭

| 파일 | 원본 출처 | 설명 |
|---|---|---|
| `product_code_name_lookup.sql` | 상품코드,상품명-쿼리 240103 / 시트1 (2024-01) | 상품 마스터에서 판매 가능 상태의 상품코드(GdsNo)·상품명(GdsNm)을 등록일 역순으로 조회 |
| `product_info_toggle_anchor_chip_clicks.sql` | 상품정보펼치기,앵커칩 240129 / 시트1 (2024-01) | 상품상세 번호(gdsNo) 추출 후 상품정보 펼치기 토글/앵커칩 버튼 클릭수·유저·세션 집계 |
| `product_tag_click_by_content.sql` | 상품태그클릭 240205 / 시트1 (2024-02) | 홈아이디어 콘텐츠(seq)별 상품 태그(componentGds) 클릭 PV 집계 |

## 08_traffic_metrics
트래픽 지표 — organic PV/UV, 콘텐츠 seq별 기본지표

| 파일 | 원본 출처 | 설명 |
|---|---|---|
| `content_seq_basic_metrics.sql` | seq별 기본지표 240202 / 시트1 (2024-01) | 홈아이디어 콘텐츠(seq)별 기본 지표: PV·유저·세션·상담 클릭·평균 체류시간 집계 |
| `organic_landing_pv_uv.sql` | 주요화면 오가닉 기준 PV/UV / 시트1 (2023-11) | FIRST_VALUE로 세션 첫 유입 utm 타입을 판정해 오가닉 유입 화면별 PV·세션·유저·종료율 집계 |

## 09_content
콘텐츠 — 홈아이디어 본문 seq별 전치(pivot)

| 파일 | 원본 출처 | 설명 |
|---|---|---|
| `home_idea_content_pivot.sql` | 홈아이디어 콘텐츠 본문 다운-sql lab(HSA용) 230828 / 시트1 (2023-08) | 홈아이디어 콘텐츠(homeideacontent) 본문을 sort(1~99)별 컬럼으로 pivot 하고 HTML 태그 제거, 지정 seq 목록만 조회 |

---
<sub>40개 파일 · ⊘(현직장 출처) 13개</sub>
