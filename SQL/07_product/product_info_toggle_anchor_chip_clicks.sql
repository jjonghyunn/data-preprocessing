-- source: 상품정보펼치기,앵커칩 240129 / 시트1 (2024-01)
-- 상품상세 번호(gdsNo) 추출 후 상품정보 펼치기 토글/앵커칩 버튼 클릭수·유저·세션 집계
DECLARE startDate DATETIME DEFAULT DATETIME(2024, 01, 01, 00, 00, 00); -- 조회 시작일
DECLARE finDate DATETIME DEFAULT DATETIME(2024, 01, 31, 23, 59, 59); -- 조회 종료일 (원본: 시트에서 today()-1 자동 계산)
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
,EXT_GDSNO AS(
SELECT
CASE WHEN channel = "MOWEB" AND url LIKE "%store.company_name.com/goods/%" THEN REGEXP_EXTRACT(url, r'goods/(\d+)') -- 신규(10/19 이후) 상품상세 번호 추출 MOWEB
WHEN channel = "PC" AND url LIKE "%store.company_name.com/goods/%" THEN REGEXP_EXTRACT(url, r'goods/(\d+)') -- 신규(10/19 이후) 상품상세 번호 추출 PC
WHEN channel = "MOAPP" AND url LIKE "%gdsDetail%" THEN REGEXP_EXTRACT(url, r'gdsNo=(\d+)')-- 신규(10/19 이후) 상품상세 번호 추출 MOAPP NATIVE
WHEN url LIKE "%goodsDetailMall%" THEN REGEXP_EXTRACT(url, r'gdsNo=(\d+)') -- 구(10/19 이전) 상품상세 번호 추출
ELSE NULL END AS gdsNo,
*
FROM INIT_ALL
)
SELECT
FORMAT_DATETIME("%Y%m%d", startDate) AS startdate, -- 검색 시작일
FORMAT_DATETIME("%Y%m%d", finDate) AS findate, -- 검색 종료일
channel,
gdsNo,
COUNT(CASE WHEN url LIKE "%goods_info_toggle_button%" OR url LIKE "%goods_info_expand_toggle_button%" THEN 1 ELSE NULL END) AS info_toggle_click,
COUNT(DISTINCT CASE WHEN url LIKE "%goods_info_toggle_button%" OR url LIKE "%goods_info_expand_toggle_button%" THEN pcid ELSE NULL END) AS info_toggle_users,
COUNT(DISTINCT CASE WHEN url LIKE "%goods_info_toggle_button%" OR url LIKE "%goods_info_expand_toggle_button%" THEN ssnId ELSE NULL END) AS info_toggle_sessions,
COUNT(CASE WHEN url LIKE "%goods_info_chip_button%" THEN 1 ELSE NULL END) AS anchor_chip_click,
COUNT(DISTINCT CASE WHEN url LIKE "%goods_info_chip_button%" THEN pcid ELSE NULL END) AS anchor_chip_users,
COUNT(DISTINCT CASE WHEN url LIKE "%goods_info_chip_button%" THEN ssnId ELSE NULL END) AS anchor_chip_sessions
FROM EXT_GDSNO
WHERE logType = "C"
GROUP BY
channel,
gdsNo
ORDER BY
info_toggle_click DESC
