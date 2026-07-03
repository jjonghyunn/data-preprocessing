-- source: 이전 path 추출쿼리 / 시트2 (2023-10)
-- module/snb 파싱 + 경로 정규화 후 LAG/LEAD로 세션 내 이전/현재 경로 이동 플로우 및 종료율 산출
DECLARE startDate DATETIME DEFAULT DATETIME(2023, 10, 01, 00, 00, 00); -- 조회 날짜 시작일
DECLARE finDate DATETIME DEFAULT DATETIME(2023, 10, 31, 00, 00, 00); -- 조회 날짜 종료일
WITH INIT_MW AS(
SELECT
DISTINCT
*
FROM `cellular-client-310600.TABLE_FUNCTION.INIT_MAST_P_mw`(startDate, finDate)
)
,INIT_PC AS(
SELECT
DISTINCT
*
FROM `cellular-client-310600.TABLE_FUNCTION.INIT_MAST_P_pc`(startDate, finDate)
)
,INIT_APP AS(
SELECT
DISTINCT
*
FROM `cellular-client-310600.TABLE_FUNCTION.INIT_MAST_P_app`(startDate, finDate)
)
,INIT_ALL AS(
SELECT * FROM INIT_MW
UNION ALL
SELECT * FROM INIT_PC
UNION ALL
SELECT * FROM INIT_APP
)
,EXT_MODULE_SNB AS (
SELECT
REGEXP_EXTRACT(url, r'[\?&]module=([^&]+)') AS module,-- 모듈 추출
REGEXP_EXTRACT(url, r'[\?&]snb=([^&]+)') AS snb, --snb 추출
CASE WHEN url_original LIKE "%url=%" THEN SPLIT(SPLIT(url_original, "rl=")[SAFE_OFFSET(0)], "?")[SAFE_OFFSET(0)]
WHEN url_original LIKE "%Url=%" THEN SPLIT(SPLIT(url_original, "rl=")[SAFE_OFFSET(0)], "?")[SAFE_OFFSET(0)]
ELSE url_path
END AS new_url_path, -- url안의 url 뒷 부분 제거
*
FROM INIT_ALL
)
,EXT_PATH AS(-- 한샘몰 영역 path 단위로 뭉치기
SELECT
CASE
WHEN new_url_path LIKE "%plan/%" THEN REGEXP_EXTRACT(new_url_path, r'^(.*plan/)') -- 기획전 path 통합
WHEN new_url_path LIKE "%event/%" THEN REGEXP_EXTRACT(new_url_path, r'^(.*event/)') -- 이벤트 path 통합
WHEN new_url_path LIKE "%goods%review%" THEN REGEXP_REPLACE(new_url_path, r'\/\d+\/', '/') -- 리뷰 path 통합
WHEN (new_url_path LIKE "%goodsDetailMall%" OR new_url_path LIKE "%store.hanssem.com/goods%") AND channel = "PC"  THEN "https://store.hanssem.com/goods" -- 상품상세 신구 통합 PC
WHEN (new_url_path LIKE "%goodsDetailMall%" OR new_url_path LIKE "%store.hanssem.com/goods%") AND (channel = "MOWEB" OR channel = "MOAPP")  THEN "https://m.store.hanssem.com/goods" -- 상품상세 신구 통합 MOWEB
WHEN (new_url_path LIKE "%goodsDetailMall%" OR new_url_path LIKE "%app/gdsDetail%") AND channel = "MOAPP"  THEN "https://mall.hanssem.com/app/gdsDetail" -- 상품상세 신구 통합 MOAPP
WHEN new_url_path LIKE "%app%store%module=home%" THEN REPLACE(REPLACE(new_url_path, "?module=home", ""), "&snb=", "") -- 앱 스토어 메인 module=home 구분 제거
WHEN (new_url_path LIKE "%mall.html%" OR new_url_path LIKE "%mall\\_%html%" OR new_url_path LIKE "%/app/store%") AND module IS NOT NULL AND snb IS NOT NULL THEN CONCAT(new_url_path, '?module=', module, '&snb=', snb) -- module, snb 다 존재
WHEN (new_url_path LIKE "%mall.html%" OR new_url_path LIKE "%mall\\_%html%" OR new_url_path LIKE "%/app/store%") AND module IS NOT NULL AND snb IS NULL THEN CONCAT(new_url_path, '?module=', module) -- module 만 존재
WHEN (new_url_path LIKE "%homeidea.html%" OR new_url_path LIKE "%homeidea\\%html%") AND module IS NOT NULL AND snb IS NOT NULL THEN CONCAT(new_url_path, '?module=', module, '&snb=', snb) -- module, snb 다 존재
WHEN (new_url_path LIKE "%homeidea.html%" OR new_url_path LIKE "%homeidea\\%html%") AND module IS NOT NULL AND snb IS NULL THEN CONCAT(new_url_path, '?module=', module) -- module, snb 다 존재
WHEN new_url_path LIKE "%/m/mainA%" OR new_url_path LIKE "%/m/mainB%" THEN "https://mall.hanssem.com/m/main.html" -- 통합메인 A,B 통합
WHEN REGEXP_CONTAINS(new_url_path,r'\d+' ) THEN REGEXP_REPLACE(new_url_path, r'\d+', '') -- 번호로 분할되는 경우 일괄 번호제거하여 묶음
ELSE new_url_path END AS curr_path,
* FROM EXT_MODULE_SNB
)
,LAG_LEAD AS(-- ssnId 기준으로 이전 페이지 추출
SELECT
LAG(curr_path) OVER(PARTITION BY ssnId ORDER BY ssnId, ssn_step, ts) AS prev_path,
LEAD(curr_path) OVER(PARTITION BY ssnId ORDER BY ssnId, ssn_step, ts) AS next_path,
*
FROM EXT_PATH
)
,FILTER_URL AS(
SELECT
*
FROM LAG_LEAD
WHERE
(channel = "MOWEB"
AND ( -- MOWEB 확인하실 영역의 url_path(url의 ? 앞 부분의 키워드)을 넣어주세요
curr_path  LIKE "%mall.html%"
))
OR
(channel = "MOAPP"
AND ( -- MOAPP 확인하실 영역의 url_path(url의 ? 앞 부분의 키워드)을 넣어주세요
curr_path  LIKE "%/app/%store%"
))
OR
(channel = "PC"
AND ( -- WEB 확인하실 영역의 url_path(url의 ? 앞 부분의 키워드)을 넣어주세요
curr_path LIKE "%mall\\_%html%"
))
)
--prev
,RESULT AS(
SELECT
channel, --채널
prev_path, -- 이전 url path
curr_path, -- 현재 url path
COUNT(url) AS pageviews, -- 페이지뷰
COUNT(DISTINCT pcid) AS count_dist_pcid, -- 고유 pcid(사용자 기기) 수
COUNT(DISTINCT ssnId) AS count_dist_ssnId, -- 고유 세션 수
AVG(CASE WHEN dt < 1800000 THEN dt/1000 ELSE NULL END) AS avg_dt_seconds, -- 평균 체류 시간
COUNT(CASE WHEN ssn_step = 1 THEN url ELSE NULL END) AS count_randing, -- 랜딩 수
COUNT(CASE WHEN isSsnExp = 1 THEN url ELSE NULL END) AS exits, -- 종료 수
COUNT(CASE WHEN isSsnExp = 1 THEN url ELSE NULL END) / COUNT(url) AS exits_rate -- 종료율 = 종료 수 / 페이지뷰
FROM FILTER_URL
GROUP BY channel, prev_path, curr_path
)
SELECT * FROM RESULT
ORDER BY pageviews DESC
