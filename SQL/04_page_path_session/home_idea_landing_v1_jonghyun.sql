-- source: 홈아이디어 랜딩(오가닉 파악) 쿼리문 231206 / 종현개량 (2023-11)
-- LAG로 직전 url 유무를 판단해 홈아이디어 페이지의 랜딩(오가닉 유입) pcid/세션 수 산출 (개량본)
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
UNION ALL
SELECT * FROM INIT_APP
)
,A AS(
SELECT
LAG(url_path, 1, NULL) OVER (PARTITION BY pcid ORDER BY pcid, ts) AS lag_pcid, -- pcid 기준 바로 직전 url 추출
LAG(url_path, 1, NULL) OVER (PARTITION BY ssnId ORDER BY ssnId, ts) AS lag_ssnId -- 세션 기준 바로 직전 url 추출
, *
FROM INIT_MW  -- 채널변경필요시 여기서 MW을 PC로 변경
)
SELECT
channel,
COUNT(DISTINCT pcid) AS pcid_exists, -- 검색한 URL을 방문한 pcid의 수
COUNT(DISTINCT ssnId) AS ssnId_exists, -- 검색한 URL을 방문한 ssnId의 수
COUNT(DISTINCT CASE WHEN lag_pcid IS NULL THEN pcid ELSE NULL END) AS pcid_lands, -- 검색한 URL 이 pcid의 랜딩인 경우 고유 pcid 수
COUNT(DISTINCT CASE WHEN lag_ssnId IS NULL THEN ssnId ELSE NULL END) AS ssnId_lands -- 검색한 URL 이 pcid의 랜딩인 경우 고유 ssnId 수
FROM A
WHERE url_path LIKE "%https://mall.hanssem.com/%" -- 검색할 URL_path 값
AND (url_path LIKE "%homeIdea%" OR url_path LIKE "%homeidea%") -- "homeIdea" 또는 "homeidea"가 포함된 URL
AND url NOT LIKE "%Admin=Y%" -- 제외할 URL 값
GROUP BY channel
ORDER BY channel DESC
