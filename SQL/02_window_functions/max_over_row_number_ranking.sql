-- source: 250404-max,row_number.sql (2025-04)
-- site_code별 카운트에 ROW_NUMBER 순위 부여 후 MAX() OVER 전체 최대값 계산 (윈도우 함수 학습)
-- sanitized for public repo
with a as(
SELECT distinct start_date, site_code,
count(site_code) as cnt_sitecode
FROM act.edge_sustain_mb
group by site_code),

row_num as(
select *,
ROW_NUMBER() OVER (ORDER BY cnt_sitecode DESC) as rn
from a
),

x as (select *, "-" as rn from a
union
select *
from row_num where rn = '1')

SELECT *,
MAX(cnt_sitecode) over () AS max_cnt_sitecode
FROM x
GROUP BY site_code,rn
order by rn desc, cnt_sitecode desc
