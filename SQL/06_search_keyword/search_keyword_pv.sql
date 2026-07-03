-- source: searchKey 240205 / 시트1 (2024-02)
-- url에서 searchKey 파라미터를 추출해 검색 키워드별 클릭 PV 집계 (상위 100000건)
DECLARE startDate DATETIME DEFAULT DATETIME(2024, 02, 01, 00, 00, 00); -- 조회 시작일 (원본: 시트 셀 B2 참조)
DECLARE finDate DATETIME DEFAULT DATETIME(2024, 02, 05, 23, 59, 59); -- 조회 종료일 (원본: 시트 셀 C2 참조)
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
,searchKeyList AS(
SELECT
REPLACE(REGEXP_EXTRACT(url, r'searchKey=([^&]+)'), '+', ' ')  AS searchKey,
*
FROM INIT_ALL
)
SELECT
searchKey,
COUNT(CASE WHEN logType = "C" AND url LIKE CONCAT('%', searchKey, '%') THEN searchKey ELSE NULL END) AS PV,
FORMAT_DATETIME("%Y%m%d", startDate) AS startdate,
FORMAT_DATETIME("%Y%m%d", finDate) AS findate
FROM searchKeyList
GROUP BY
searchKey
ORDER BY
PV DESC
limit 100000
