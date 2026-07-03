-- source: 상품태그클릭 240205 / 시트1 (2024-02)
-- 홈아이디어 콘텐츠(seq)별 상품 태그(componentGds) 클릭 PV 집계
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
,A AS(
SELECT
REPLACE(REGEXP_EXTRACT(url, r'componentGds([^&]+)'), '+', ' ')  AS componentGds,
CASE WHEN channel = "MOWEB" AND url LIKE "%homeIdeaDetail%" THEN REGEXP_EXTRACT(url, r'seq=(\d+)')
WHEN channel = "PC" AND url LIKE "%homeIdeaDetail%" THEN REGEXP_EXTRACT(url, r'seq=(\d+)')
WHEN channel = "MOAPP" AND url LIKE "%homeIdeaDetail%" THEN REGEXP_EXTRACT(url, r'seq=(\d+)')
ELSE NULL END AS seq,
*
FROM INIT_ALL
)
SELECT
seq,
componentGds,
COUNT(CASE WHEN logType = "C" AND url LIKE CONCAT('%', componentGds, '%') THEN componentGds ELSE NULL END) AS gdsPV,
FORMAT_DATETIME("%Y%m%d", startDate) AS startdate,
FORMAT_DATETIME("%Y%m%d", finDate) AS findate
FROM A
GROUP BY
seq,
componentGds
ORDER BY
gdsPV DESC
