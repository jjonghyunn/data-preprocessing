-- source: 쿼리테스트-이후세션플로우정합성용 240206 / 6퀄-세션2915나오도록 (2024-01)
-- 세션플로우 정합성 검증 6단계: 특정 콘텐츠 url(seq=27410) 직접 방문 로그 원본 조회 (세션 수 대조용)
declare startDate datetime default datetime(2024, 01, 01, 00, 00, 00);
declare finDate datetime default datetime(2024, 01, 31, 23, 59, 59);
with
INIT_MW AS(select distinct * from `cellular-client-310600.TABLE_FUNCTION.INIT_MAST_PVC_mw`(startDate, finDate)
)
,INIT_PC AS(select distinct * from `cellular-client-310600.TABLE_FUNCTION.INIT_MAST_PVC_pc`(startDate, finDate)
)
,INIT_APP AS(select distinct * from `cellular-client-310600.TABLE_FUNCTION.INIT_MAST_PVC_app`(startDate, finDate)
)
,INIT_ALL AS(select * from INIT_MW UNION all
select * from INIT_PC UNION all
select * from INIT_APP)
,A AS(select regexp_replace(url_path,r'\d','') AS url_path_dnum, * from INIT_ALL)
select url_path_dnum, url, ssnId, logType from A
where url like "%homeIdeaDetail.do?seq=27410%"
limit 10000
