-- source: page_path_이전경로 / 시트1 (2023-11)
-- referr_path 기준 이전 페이지 → 현재 url_path 이동 조합별 PV·세션·PCID 집계 (상품상세 referrer 필터)
DECLARE startDate DATETIME DEFAULT DATETIME(2023, 11, 01, 00, 00, 00); -- 조회 시작일
DECLARE finDate DATETIME DEFAULT DATETIME(2023, 11, 30, 00, 00, 00); -- 조회 종료일
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
--   UNION ALL
--   SELECT * FROM INIT_APP
)
,DNUM AS(
SELECT
REGEXP_REPLACE(url_path, r'\d', '') AS url_path, -- url_path에서 숫자 제거(상품상세, 기획전 등 뭉치기 위해)
REGEXP_REPLACE(referr_path, r'\d', '') AS referr_path, -- reffer_path에서 숫자 제거(상품상세, 기획전 등 뭉치기 위해)
* EXCEPT(url_path, referr_path) FROM INIT_ALL
WHERE logType = "P"
)
SELECT
channel,-- 채널
referr_path, -- referrer의 path -- 이전 페이지
url_path, -- url의 path
COUNT(*) AS counter, -- 페이지뷰
COUNT(DISTINCT ssnId) AS ssnIds, -- 세션 수
COUNT(DISTINCT pcid) AS pcids -- PCID 수
FROM DNUM
WHERE referr_path LIKE "%store.hanssem.com/goods%" -- 상품상세 조회 url 검색해주세요
GROUP BY channel, referr_path, url_path
ORDER BY channel, counter DESC
