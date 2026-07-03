-- source: orderbystudy.sql (2024-06)
-- ROW_NUMBER 로 파티션 내 순위 부여 + SUM() OVER 로 site_code별 누적 합 계산 (윈도우 함수 학습)
-- sanitized for public repo
with A as(
SELECT *
,row_number() over (partition by site_code, device, start_date order by hhp desc) as rn
FROM global_table3_query_2401_2405

order by rn)
,B as(
select *
,SUM(hhp/2) OVER (PARTITION BY start_date, site_code) AS total_hhp
from A
)


select *
-- 검증용 site_code,country,region,device,os,start_date,breakdown,channel2,`group`,hhp,rn,total_hhp
from B

-- 검증용 where site_code in ('in','cn','ae') and start_date in ('2024-01-01','2024-02-01')
ORDER BY start_date, device asc
, total_hhp desc
