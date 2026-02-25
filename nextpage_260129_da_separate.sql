with 
origin as (
  select org.site_code, org.breakdown, total, mx, vd, od.da
  from 26_nyny_nextpage_excl_da org
  left join 26_nyny_nextpage_only_da od 
  on org.site_code = od.site_code and org.breakdown = od.breakdown
),
mapped as (
  select
  breakdown as origin_breakdown,
    site_code,
    case 
          /* Site Home */
      when site_code = 'us' and replace(lower(breakdown),'https://','') in ('www.samsung.com/us','www.samsung.com/us/')
        then 'home'
      /* Product Detail: /buy/     */
      when site_code = 'us' and lower(breakdown) like '%/buy/%' then 'product detail'
      when site_code = 'us' and lower(breakdown) like '%/us/tvs/' then 'product category detail'
      /* Product Finder: all-xxx */
      when site_code = 'us' and lower(breakdown) like '%/all-%'
        then 'product finder'
      /* Offer Main */
      when site_code = 'us' and lower(breakdown) like '%/offer/%'
        then 'offer main'
      when site_code = 'us' and lower(breakdown) like '%/shop/featured-offers/%' 
      then 'offer main'
      /* My Account */
      when site_code = 'us' and lower(breakdown) like '%/web/account/%'
        then 'my account'
      when site_code = 'sec' and lower(breakdown) in ('revamp product finder','revamp product detail')
        then replace(lower(breakdown),'revamp ','')
      when site_code = 'sec' and lower(breakdown) in ('buying configurator')
        then 'product detail'
      else breakdown end as 
    breakdown,
    case
      when lower(breakdown) in ('product category detail') then 'PCD'
      when lower(Breakdown) in ('product detail','revamp product detail') then 'PD'
      when lower(breakdown) in ('product finder','revamp product finder') then 'PF'
      when lower(breakdown) = 'shop detail' then 'SD'
      when lower(breakdown) = 'buying configurator' and site_code = 'sec' then 'PD'
      else null
    end as pagetype2,
    total, mx, vd, da
  from origin
),
unpivoted as (
  select origin_breakdown, site_code, breakdown, pagetype2, 'TOTAL' as division, total as value from mapped
  union all
  select origin_breakdown, site_code, breakdown, pagetype2, 'MX'    as division, mx    as value from mapped
  union all
  select origin_breakdown, site_code, breakdown, pagetype2, 'VD'    as division, vd    as value from mapped
  union all
  select origin_breakdown, site_code, breakdown, pagetype2, 'DA'    as division, da    as value from mapped
),
with_div2 as (
  select distinct
  origin_breakdown, 
    site_code,
    breakdown,
    pagetype2,
    division,
    value,
    case
      when pagetype2 is null then null
      else concat(division, ' ', pagetype2)
    end as division_pagetype2
  from unpivoted
  where breakdown not in ('*')
),
totals_ranked as (
  select
  origin_breakdown,
   
    site_code,
    breakdown as page_type,
    value,
    row_number() over (partition by site_code order by value desc) as rn
  from with_div2
  where division = 'TOTAL'
  -- ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
  -- ★★★★★★★★★★★★★★ 걸러야할 데이터 여기서 정제하기 ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
  -- ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
  -- and lower(breakdown) not in ('error','*')
),
part1 as (
  select origin_breakdown,  case when site_code = 'uk_epp' then 'UK'  when site_code='ku' then 'IQ_KU' else upper(site_code) end as site_code, page_type, 
   value
  from totals_ranked
  where rn <= 10
),
part2 as (
  select origin_breakdown, 
    case when site_code = 'uk_epp' then 'UK'  when site_code='ku' then 'IQ_KU' else upper(site_code) end as site_code,
    division_pagetype2 as page_type,
    sum(value) as 
    value
  from with_div2
  where division_pagetype2 is not null
    and exists (
      select 1
      from totals_ranked tr
      where tr.site_code = with_div2.site_code
        and tr.rn <= 10
        and (
          tr.page_type = with_div2.breakdown
          or tr.page_type = with_div2.pagetype2
        )
    )
  group by site_code, division_pagetype2
),
tr as (
  select part1.origin_breakdown, t.tier as `TIER`, t.subs as `SUBS`, t.country as `COUNTRY`, part1.site_code as `SITE CODE`, page_type as `PAGE TYPE`, value as `VALUE`
  from part1 left join campaign_tier_260128 t on part1.site_code = t.site_code
  union all
  select part2.origin_breakdown, t.tier, t.subs, t.country, part2.site_code, page_type,  value
  from part2 left join campaign_tier_260128 t on part2.site_code = t.site_code
  where page_type not like 'TOTAL%'
)
select distinct
  `TIER`, `SUBS`, `COUNTRY`, `SITE CODE`,
  case
      when `PAGE TYPE` like '%PD'  then 'product detail'
      when `PAGE TYPE` like '%PF'  then 'product finder'
      when `PAGE TYPE` like '%PCD' then 'product category detail'
      when `PAGE TYPE` like '%SD'  then 'shop detail'
      when  `SITE CODE` = 'sec' and `PAGE TYPE` in ('buying configurator')  then 'product detail'
      else replace(`PAGE TYPE`,'revamp ','')
  end as `CATEGORY`,
  `PAGE TYPE`
  , origin_breakdown  as Origin_page_type,
  `VALUE`
  ,
  case  
  when `PAGE TYPE` in ('product category detail','product detail','revamp product detail','product finder','revamp product finder','shop detail') 
  then 'both'
  when `SITE CODE` = 'sec' and `PAGE TYPE` in ('buying configurator') 
  then 'both'
  when `PAGE TYPE` like 'MX%' or `PAGE TYPE` like 'VD%' or `PAGE TYPE` like 'DA%' 
  then 'division'
  else 'non-division' end as `VALUE_TYPE`
from tr
where `VALUE` > 0
-- SEC  pd 페이지의 all page track 이 buying configurator  이기 때문에 next page 시트 등에 해당 페이지를 pd 로 합산해줘야 함.
-- US는 덜 변환된 케이스가 있어서 수기 변환 필요.
;
