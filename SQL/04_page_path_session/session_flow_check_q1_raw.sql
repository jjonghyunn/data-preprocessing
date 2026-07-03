-- source: 쿼리테스트-이후세션플로우정합성용 240206 / 1퀄 (2024-01)
-- 세션플로우 정합성 검증 1단계: 특정 콘텐츠(seq=27410) referrer 로그 원본 조회
DECLARE startDate DATETIME DEFAULT DATETIME(2024, 01, 01, 00, 00, 00); -- 조회 시작일
DECLARE finDate DATETIME DEFAULT DATETIME(2024, 02, 05, 23, 59, 59); -- 조회 종료일
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
REGEXP_REPLACE(url_path, r'\d', '') AS url_path_dnum, -- url_path에서 숫자 제거(상품상세, 기획전 등 뭉치기 위해)
*
FROM
INIT_ALL
)
SELECT
*
FROM A
where referr_original LIKE "%seq=27410%"
limit 10000
