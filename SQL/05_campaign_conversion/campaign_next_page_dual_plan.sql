-- source: 기획전 컨버전페이지(직후페이지) 240130 / 2개조회-쿼리문 (2024-01)
-- PC·MO 기획전 두 개를 함께 조회해 방문 세션의 직후 이동 url을 LEAD로 추출, 세션 수 집계
DECLARE startDate DATETIME DEFAULT DATETIME(2024, 01, 01, 00, 00, 00); -- 조회 시작일
DECLARE finDate DATETIME DEFAULT DATETIME(2024, 01, 31, 23, 59, 59); -- 조회 종료일 (원본: 시트에서 today()-1 자동 계산)
WITH INIT_MW AS(
SELECT
DISTINCT
*
FROM `cellular-client-310600.TABLE_FUNCTION.INIT_MAST_PVC_mw`(startDate, finDate)
)
,INIT_PC AS(
SELECT
DISTINCT
*
FROM `cellular-client-310600.TABLE_FUNCTION.INIT_MAST_PVC_pc`(startDate, finDate)
)
,INIT_APP AS(
SELECT
DISTINCT
*
FROM `cellular-client-310600.TABLE_FUNCTION.INIT_MAST_PVC_app`(startDate, finDate)
)
,INIT_ALL AS(
SELECT * FROM INIT_MW
UNION ALL
SELECT * FROM INIT_PC
UNION ALL
SELECT * FROM INIT_APP
)
,A AS(
SELECT
REGEXP_REPLACE(url_path, r'\d', '') AS url_path_dnum, -- url_path에서 숫자 제거(상품상세, 기획전 등 뭉치기 위해)
*
FROM
INIT_ALL -- 채널변경필요시 여기서 MW PC ALL 중 입력
)
,B AS(
SELECT
-- LAG(url_path_dnum, 1, NULL) OVER (PARTITION BY pcid ORDER BY pcid, ts) AS pcid_lag_url, -- pcid 기준 바로 직전 url 추출
LEAD(url_path_dnum, 1, NULL) OVER (PARTITION BY ssnId ORDER BY ssnId, ts) AS ssn_lead_url -- 세션 기준 바로 이후 url 추출
, *
FROM A
)
SELECT
FORMAT_DATETIME("%Y%m%d", startDate) AS startdate, -- 검색 시작일
FORMAT_DATETIME("%Y%m%d", finDate) AS findate, -- 검색 종료일
channel,--채널
url_path_dnum, -- 검색한 현재 url_path
ssn_lead_url, -- 세션 단위 직후  url_path
COUNT(DISTINCT ssnId) AS count_ssnId -- 세션 수
FROM B
WHERE REGEXP_CONTAINS(url_path,'(mall.hanssem.com/m/mplan/{MO_PLAN_NO}|mall.hanssem.com/plan/{PC_PLAN_NO})') -- 검색할 URL_path 값 (기획전 번호 입력)
AND NOT REGEXP_CONTAINS(url,'(isAdmin=Y)') -- 제외할 URL 값(파라미터 포함)추가 시 |를 OR이라 생각하시고 붙여서 넣어주세요
GROUP BY channel, url_path_dnum, ssn_lead_url
ORDER BY channel, count_ssnId DESC
