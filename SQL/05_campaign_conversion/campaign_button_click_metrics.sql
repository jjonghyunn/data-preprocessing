-- source: 기획전 버튼클릭 240122 / 시트1 (2024-01)
-- 기획전 종합 지표: 트래픽·이탈률·종료율 + 내비게이션 탭/매장상담/플로팅배너 버튼 클릭수 집계
DECLARE startDate DATETIME DEFAULT DATETIME(2024, 01, 15, 00, 00, 00); -- 시작일
DECLARE finDate DATETIME DEFAULT DATETIME(2024, 01, 21, 23, 59, 00); -- 종료일
DECLARE planNo_PC STRING DEFAULT "17202"; -- PC 기획전 번호
DECLARE planNo_MO STRING DEFAULT "17182"; -- MO 기획전 번호
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
--기본 지표
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
--GTM 세팅 액션 지표 예시  -- GTM에 세팅한 파라미터(actionParams) 입력
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=내비게이션탭_한샘 신학기 혜택%" THEN 1 ELSE NULL END) AS navi_1
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=내비게이션탭_신학기 혜택%" THEN 1 ELSE NULL END) AS navi_2
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=내비게이션탭_김나영 Pick%" THEN 1 ELSE NULL END) AS navi_3
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=내비게이션탭_BEST 책상 특가%" THEN 1 ELSE NULL END) AS navi_4
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=내비게이션탭_릴레이 타임 특가%" THEN 1 ELSE NULL END) AS navi_5
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=내비게이션탭_패키지 특가%" THEN 1 ELSE NULL END) AS navi_6
, COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=내비게이션탭_랭킹 TOP 10%" THEN 1 ELSE NULL END) AS navi_7
,COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=매장상담상단버튼%" THEN 1 ELSE NULL END) AS Openrun2
,COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=매장상담하단버튼%" THEN 1 ELSE NULL END) AS Openrun3
,COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=플로팅배너%" THEN 1 ELSE NULL END) AS Openrun4
,COUNT(CASE WHEN (url LIKE CONCAT("%plan%", planNo_PC, "%") OR url LIKE CONCAT("%plan%", planNo_MO, "%")) AND url LIKE"%click=1222쿠폰버튼%" THEN 1 ELSE NULL END) AS Openrun5
FROM INIT
GROUP BY channel, date
ORDER BY channel, date ASC
