-- source: 쿼리테스트-이후세션플로우정합성용 240206 / 2퀄 (2024-01)
-- 세션플로우 정합성 검증 2단계: LEAD로 세션 내 직후 url 추가, seq=27410 유입 로그 조회
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
,B AS(select lead(url_path_dnum,1, NULL) over (partition by ssnId order by ts_datetime) as ssn_lead_url, * from A where referr_original like "%seq=27410%")
select * from B limit 10000
