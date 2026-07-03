-- source: 검색키워드별 이전경로 page_path 추출쿼리 / 시트1 (2023-11)
-- 현재/referrer/직전(LAG) 순으로 searchKey를 보간하여 검색 페이지 유입 후 도달한 url_path별 PV 집계
DECLARE startDate DATETIME DEFAULT DATETIME(2023, 11, 30, 00, 00, 00); --기간 시작일
DECLARE finDate DATETIME DEFAULT DATETIME(2023, 11, 30, 00, 00, 00);  --기간 종료일
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
,LOG_P AS(
SELECT
REGEXP_REPLACE(url_path, r'\d', '') AS url_path_dnum, -- url_path에서 숫자 제거(상품상세, 기획전 등 뭉치기 위해)
* FROM INIT_ALL
WHERE logType = "P"
)
,SEARCH_KEY AS(
SELECT
REPLACE(REGEXP_EXTRACT(url_original, r'searchKey=([^&]+)'), '+', ' ')  AS current_searchKey,
REPLACE(REGEXP_EXTRACT(referr, r'searchKey=([^&]+)'), '+', ' ')  AS referr_searchKey,
*
FROM LOG_P
)
,LAG_LOG AS(
    SELECT
    LAG(url_original, 1) OVER (PARTITION BY ssnId ORDER BY ssnId, ts) AS lagged_url,
    url_original,
    LAG(current_searchKey, 1) OVER (PARTITION BY ssnId ORDER BY ssnId, ts) AS lag_searchKey,
    * EXCEPT(url_original)
    FROM SEARCH_KEY
)
,SKEY_FILLED AS(
    SELECT
    CASE WHEN current_searchKey IS NOT NULL THEN current_searchKey -- 1순위 현재 url 검색키
    WHEN current_searchKey IS NULL AND referr_searchKey IS NOT NULL THEN referr_searchKey -- 2순위 referr 검색키
    WHEN current_searchKey IS NULL AND referr_searchKey IS NULL THEN lag_searchKey -- 3순위 이전 url 검색키
    ELSE NULL
    END AS searchKey,
    *
    FROM LAG_LOG
)
SELECT
channel, -- 채널
url_path_dnum, -- url_path
searchKey, -- 검색 키워드
COUNT(*) AS counter -- 페이지뷰
FROM SKEY_FILLED
WHERE searchKey IS NOT NULL
AND lagged_url LIKE "%/search%" -- 이전 페이지가 검색 페이지
AND url_original NOT LIKE "%/search%" -- 현재 페이지는 검색 페이지 X
GROUP BY channel, url_path_dnum, searchKey
ORDER BY counter DESC
