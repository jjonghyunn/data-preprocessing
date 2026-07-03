-- source: seq별 기본지표 240202 / 시트1 (2024-01)
-- 홈아이디어 콘텐츠(seq)별 기본 지표: PV·유저·세션·상담 클릭·평균 체류시간 집계
DECLARE startDate DATETIME DEFAULT DATETIME(2024, 01, 01, 00, 00, 00); -- 조회 시작일
DECLARE finDate DATETIME DEFAULT DATETIME(2024, 01, 31, 23, 59, 59); -- 조회 종료일
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
,ext_seq AS(
SELECT
CASE WHEN channel = "MOWEB" AND url LIKE "%homeIdeaDetail%" AND (url LIKE "%contentsTypeCd=V%" OR url LIKE "%contentsTypeCd=C%") THEN REGEXP_EXTRACT(url, r'seq=(\d+)')
WHEN channel = "PC" AND url LIKE "%homeIdeaDetail%" AND (url LIKE "%contentsTypeCd=V%" OR url LIKE "%contentsTypeCd=C%") THEN REGEXP_EXTRACT(url, r'seq=(\d+)')
WHEN channel = "MOAPP" AND url LIKE "%homeIdeaDetail%" AND (url LIKE "%contentsTypeCd=V%" OR url LIKE "%contentsTypeCd=C%") THEN REGEXP_EXTRACT(url, r'seq=(\d+)')
ELSE NULL END AS seq,
*
FROM INIT_ALL
)
SELECT
channel,
seq,
COUNT(CASE WHEN logType = "P" THEN 1 ELSE NULL END) AS pageviews,
COUNT(DISTINCT CASE WHEN logType = "P" THEN pcid ELSE NULL END) AS users,
COUNT(DISTINCT CASE WHEN logType = "P" THEN ssnId ELSE NULL END) AS sessions,
COUNT(CASE WHEN logType = "C" AND url LIKE "%gotoCounsel%" THEN 1 ELSE NULL END) AS goToCounsel_click,
-- exit 요청
AVG(CASE WHEN dt < (60*30*1000) THEN dt/1000 ELSE NULL END) AS avg_dt -- 오류로 확인. 정합성확인요청
FROM ext_seq
GROUP BY
channel,
seq
ORDER BY
pageviews DESC
