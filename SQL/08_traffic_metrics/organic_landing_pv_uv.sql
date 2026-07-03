-- source: 주요화면 오가닉 기준 PV/UV / 시트1 (2023-11)
-- FIRST_VALUE로 세션 첫 유입 utm 타입을 판정해 오가닉 유입 화면별 PV·세션·유저·종료율 집계
DECLARE startDate DATETIME DEFAULT DATETIME(2023, 11, 30, 00, 00, 00);
DECLARE finDate DATETIME DEFAULT DATETIME(2023, 11, 30, 00, 00, 00);
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
-- ,INIT_APP AS(
--     SELECT
--     DISTINCT
--         *
--     FROM `cellular-client-310600.TABLE_FUNCTION.INIT_MAST_PVC_app`(startDate, finDate)
-- )
,INIT_ALL AS(
SELECT * FROM INIT_MW
UNION ALL
SELECT * FROM INIT_PC
--   UNION ALL
--   SELECT * FROM INIT_APP
)
,EXT_FIRST_UTM AS(-- 세션 첫 유입 추출
SELECT
LEFT(date, 6) AS month,
FIRST_VALUE(type) OVER (PARTITION BY ssnId ORDER BY ssnId, ts) AS first_utm_type, -- 세션 첫 스텝의 utm 타입
*
FROM INIT_ALL
)
SELECT
first_utm_type,
url,
COUNT(CASE WHEN logType = "P" THEN 1 ELSE NULL END) AS pageviews, -- 페이지뷰
COUNT(DISTINCT CASE WHEN logType = "P" THEN ssnId ELSE NULL END) AS sessions, -- 세션 수
COUNT(DISTINCT CASE WHEN logType = "P" THEN pcid ELSE NULL END) AS users, -- 유저 수
COUNT(CASE WHEN isSsnExp = 1 THEN 1 ELSE null END) AS exits, -- 종료수
COUNT(CASE WHEN isSsnExp = 1 THEN 1 ELSE null END) / NULLIF(COUNT(CASE WHEN logType = "P" THEN 1 ELSE NULL END), 0) AS exits_rate -- 종료율 = 종료수 / 페이지뷰
FROM EXT_FIRST_UTM
WHERE
first_utm_type = "organic" -- 세션 유입 utm_type = organic
AND url LIKE "%%" -- 검색할 url
GROUP BY
first_utm_type,
url
