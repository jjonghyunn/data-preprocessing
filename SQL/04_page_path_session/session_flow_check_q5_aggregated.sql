-- source: 쿼리테스트-이후세션플로우정합성용 240206 / 5퀄 (2024-01)
-- 세션플로우 정합성 검증 5단계: 직후 url 조합별 고유 세션 수 집계 (최종 집계형)
DECLARE startDate DATETIME DEFAULT DATETIME(2024, 01, 01, 00, 00, 00); -- 조회 시작일
DECLARE finDate DATETIME DEFAULT DATETIME(2024, 01, 31, 23, 59, 59); -- 조회 종료일
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
select
FORMAT_DATETIME("%Y%m%d", startDate) AS startdate,
FORMAT_DATETIME("%Y%m%d", finDate) AS findate,
channel,
url_path_dnum,
ssn_lead_url,
COUNT(DISTINCT ssnId) AS count_ssnId
from B
where url_path_dnum like "%homeIdeaDetail.do%"
GROUP BY channel, url_path_dnum, ssn_lead_url
ORDER BY channel, count_ssnId DESC;
