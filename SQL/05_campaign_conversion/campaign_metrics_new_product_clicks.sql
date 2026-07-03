-- source: 기획전 데이터(정확성 미확인)의 사본 / 시트1 (2024-01)
-- 기획전 종합 지표: 트래픽·이탈률(BounceRate)·종료율(ExitRate) + 신상 배너 클릭수 집계
DECLARE startDate DATETIME DEFAULT DATETIME(2024, 01, 15, 00, 00, 00); -- 시작일
DECLARE finDate DATETIME DEFAULT DATETIME(2024, 01, 21, 23, 59, 00); -- 종료일
DECLARE planNo_PC STRING DEFAULT "17215"; -- PC 기획전 번호
DECLARE planNo_MO STRING DEFAULT "17216"; -- MO 기획전 번호
WITH INIT_MW AS(
SELECT * FROM `ds_mw_daily.*`
WHERE _TABLE_SUFFIX
BETWEEN FORMAT_DATE('%Y%m%d', startDate)
AND FORMAT_DATE('%Y%m%d',finDate)
)
,INIT_PC AS(
SELECT * FROM `ds_pc_daily.*`
WHERE _TABLE_SUFFIX
BETWEEN FORMAT_DATE('%Y%m%d', startDate)
AND FORMAT_DATE('%Y%m%d',finDate)
)
,INIT_APP AS(
SELECT * FROM `ds_app_daily.*`
WHERE _TABLE_SUFFIX
BETWEEN FORMAT_DATE('%Y%m%d', startDate)
AND FORMAT_DATE('%Y%m%d',finDate)
)
,INIT_ALL AS(
SELECT * FROM INIT_MW
UNION ALL
SELECT * FROM INIT_PC
UNION ALL
SELECT * FROM INIT_APP
)
,INIT AS(
SELECT
MAX (ssn_step) OVER(PARTITION BY CONCAT(channel, ssnId) ORDER BY ts DESC) AS last_step,
*
FROM INIT_ALL
)
-- 기본 지표
SELECT
channel,
date,
COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) THEN 1 ELSE NULL END) AS traffics_actions,
COUNT(CASE WHEN logType = "P" AND (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) THEN 1 ELSE NULL END) AS traffics,
CASE WHEN COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND ssn_step = 1 THEN 1 ELSE NULL END) != 0 THEN
COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND ssn_step = 1 AND last_step = 1  THEN 1 ELSE NULL END) /
COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND ssn_step = 1 THEN 1 ELSE NULL END)
ELSE 0
END AS BounceRate,
CASE WHEN COUNT(CASE WHEN url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%") THEN 1 ELSE NULL END) != 0 THEN
COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND ssn_step = last_step   THEN 1 ELSE NULL END) /
COUNT(CASE WHEN url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%") THEN 1 ELSE NULL END)
ELSE 0
END AS ExitRate
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=신상1%" THEN 1 ELSE NULL END) AS new1
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=신상2%" THEN 1 ELSE NULL END) AS new2
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=신상3%" THEN 1 ELSE NULL END) AS new3
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=신상4%" THEN 1 ELSE NULL END) AS new4
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=pc딜기획전%" THEN 1 ELSE NULL END) AS new5
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=딜기획전mo%" THEN 1 ELSE NULL END) AS new6
FROM INIT
GROUP BY channel, date
ORDER BY channel, date ASC
