-- md multiorder. by jonghyun park 251219

with recursive src as (
    select
        site_code,
        breakdown,
        campaign_total_multiorder_unit,
        campaign_total_multiorder,
        campaign_total_multiorder_revenue,
        scom_total_multiorder_unit,
        scom_total_multiorder,
        scom_total_multiorder_revenue,
        start_date,
        end_date
    from table_name_260211
),
split_seed as (
    select
        site_code,
        breakdown,
        1 as pos,
        trim(substring_index(breakdown, ',', 1)) as model_code,
        case
            when locate(',', breakdown) > 0 then substr(breakdown, locate(',', breakdown) + 1)
            else ''
        end as rest,
        campaign_total_multiorder_unit,
        campaign_total_multiorder,
        campaign_total_multiorder_revenue,
        scom_total_multiorder_unit,
        scom_total_multiorder,
        scom_total_multiorder_revenue,
        start_date,
        end_date
    from src
),
exploded_origin as (
    select
        site_code,
        breakdown,
        pos,
        model_code,
        rest,
        campaign_total_multiorder_unit,
        campaign_total_multiorder,
        campaign_total_multiorder_revenue,
        scom_total_multiorder_unit,
        scom_total_multiorder,
        scom_total_multiorder_revenue,
        start_date,
        end_date
    from split_seed
    -- 공백인 값 제거
        where trim(replace(model_code, ',', '')) <> ''),
exploded as( select * from exploded_origin      union all
    select
        site_code,
        breakdown,
        pos + 1,
        trim(substring_index(rest, ',', 1)),
        case
            when locate(',', rest) > 0 then substr(rest, locate(',', rest) + 1)
            else ''
        end,
        campaign_total_multiorder_unit,
        campaign_total_multiorder,
        campaign_total_multiorder_revenue,
        scom_total_multiorder_unit,
        scom_total_multiorder,
        scom_total_multiorder_revenue,
        start_date,
        end_date
    from    exploded_origin  -- DE에서 SM-L이 wearbale로 분류 안되는 현상이 있어서 강제 추가. 후 아래 언피봇에서 distinct 처리. 예: SM-F766BZKHEUB,SM-L505FZKADBT
    where rest <> ''
        and  trim(replace(trim(substring_index(rest, ',', 1)), ',', '')) <> ''
    union all
    select
        site_code,
        breakdown,
        pos + 1,
        trim(substring_index(rest, ',', 1)),
        case
            when locate(',', rest) > 0 then substr(rest, locate(',', rest) + 1)
            else ''
        end,
        campaign_total_multiorder_unit,
        campaign_total_multiorder,
        campaign_total_multiorder_revenue,
        scom_total_multiorder_unit,
        scom_total_multiorder,
        scom_total_multiorder_revenue,
        start_date,
        end_date
    from    exploded
    where rest <> ''
    -- 공백인 값 제거
    and  trim(replace(trim(substring_index(rest, ',', 1)), ',', '')) <> ''
),
unpivoted as (
    select distinct 
        site_code,
        breakdown,
        pos,
        model_code,
        'Campaign' as standard,
        campaign_total_multiorder_unit as unit,
        campaign_total_multiorder as `order`,
        campaign_total_multiorder_revenue as revenue,
        start_date,
        end_date
    from exploded
    union all
    select distinct 
        site_code,
        breakdown,
        pos,
        model_code,
        'S.com',
        scom_total_multiorder_unit,
        scom_total_multiorder,
        scom_total_multiorder_revenue,
        start_date,
        end_date
    from exploded
),
plus_category AS (

select *, case 

when upper(model_code) = 'SM-M1000QW'
or upper(model_code) like 'RS-CN%'
or upper(model_code) like 'LUMAFU%'
or upper(model_code) like 'ARCSITE%'
or upper(model_code) = 'UNSPECIFIED'
or upper(model_code) = 'UNDEFINED'
or upper(model_code) like 'AW-EW%'
or upper(model_code) like 'AC-TC%'
or upper(model_code) like 'NL-%'
or upper(model_code) like 'MLT%'
or upper(model_code) like 'VCA-%'
or upper(model_code) like 'DV-%'
or upper(model_code) like 'WA-TC%'
or upper(model_code) like 'DW-%'
or upper(model_code) like 'AF-%'
or upper(model_code) like 'DF-%'
or upper(model_code) like 'RF-TC%'
or upper(model_code) like 'APL-%'
or upper(model_code) like 'WF-%'
or upper(model_code) like 'WT-%'
or upper(model_code) like 'SC-WATCH%'
or upper(model_code) like 'SC1TAB%'
or upper(model_code) like 'WATCHES-IFIT%'
or upper(model_code) = 'BUDS' 



or upper(model_code) like '%-OFFER%' then null



when upper(model_code) like 'SM-S%'
or upper(model_code) like 'SM-G%'
or upper(model_code) like 'SM-A%'
or upper(model_code) like 'SM-F%'
or upper(model_code) like 'SM-M%'
or upper(model_code) like 'SM-E%'
or upper(model_code) like 'SM5%'
or upper(model_code) like 'SM-W%'
or upper(model_code) like 'SM-N%'
or upper(model_code) like 'SM-5%' then 'SMP'
when upper(model_code) like 'SM-X%'
or upper(model_code) like 'SM-P%'
or upper(model_code) like 'SM-T%' then 'Tablet'
when upper(model_code) like 'NT%'
or upper(model_code) like 'NP%'
or upper(model_code) like 'XE%' then 'NPC'
when upper(model_code) like 'SM-R%'
or upper(model_code) like 'SM-Q%'
or upper(model_code) like 'SM-L%'
or upper(model_code) like 'L325N%'
or upper(model_code) like 'L705N%'
or upper(model_code) like 'L330N%'
or upper(model_code) like 'L500N%'
or upper(model_code) like 'GALAXYWATCH%'
or upper(model_code) like 'SM-I%' then 'Wearable'
when upper(model_code) like 'ET%'
or upper(model_code) like 'EF%'
or (upper(model_code) like 'GP%' and upper(model_code) not like '%-OFFER%')
or upper(model_code) like 'EI%'
or upper(model_code) like 'EE%'
or upper(model_code) like 'EB%'
or upper(model_code) like 'EJ%'
or upper(model_code) like 'EP%'
or upper(model_code) like 'EO%'
or upper(model_code) like 'WMN%'
or upper(model_code) like 'CFX%'
or upper(model_code) like 'MA%'
or upper(model_code) like 'RA%'
or upper(model_code) like 'VCA%'
or upper(model_code) like 'SKK%'
-- or upper(model_code) like 'DF-%'
-- or upper(model_code) like 'AF-%' 
then 'ACC'
when upper(model_code) like 'KQ%'
or upper(model_code) like 'QA%'
or upper(model_code) like 'GQ%'
or upper(model_code) like 'QE%'
or upper(model_code) like 'QN%'
or upper(model_code) like 'TQ%'
or upper(model_code) like 'UN%'
or upper(model_code) like 'UA%'
or upper(model_code) like 'UE%'
or upper(model_code) like 'KU%'
or upper(model_code) like '43LS%'
or upper(model_code) like '50LS%'
or upper(model_code) like '65LS%'
or upper(model_code) like '43CUE%'
or upper(model_code) like '55CUE%'
or upper(model_code) like '65S%'
or upper(model_code) like 'SP-LSP%'
or upper(model_code) like 'SP-LSTP%'
or upper(model_code) like '32T%'
or upper(model_code) like '43D%'
or upper(model_code) like '43Q%'
or upper(model_code) like '43T%'
or upper(model_code) like '50D%'
or upper(model_code) like '50Q%'
or upper(model_code) like '55D%'
or upper(model_code) like '55LS%'
or upper(model_code) like '55Q%'
or upper(model_code) like '55S%'
or upper(model_code) like '65D%'
or upper(model_code) like '65Q%'
or upper(model_code) like '75D%'
or upper(model_code) like '75Q%'
or upper(model_code) like 'SP-LFF%'
or upper(model_code) like 'SP-L%'
or upper(model_code) like 'TU4%'
or upper(model_code) like 'TU5%'
or upper(model_code) like 'TU3%'
or upper(model_code) like 'TU7%'
or upper(model_code) like 'TU8%'
or upper(model_code) like 'TU9%'
or upper(model_code) like 'GU%'
or upper(model_code) like 'TU6%'
or upper(model_code) like '55U%'
or upper(model_code) like '43F%'
or upper(model_code) like '32H%'
or upper(model_code) like '65U%'
or upper(model_code) like '43U%'
or upper(model_code) like 'UD8%'
or upper(model_code) like 'UD7%'
or upper(model_code) like 'MRE1%'
or upper(model_code) like 'F-32%'
or upper(model_code) like 'LH%'
or upper(model_code) like 'HG%' then 'TV'
when upper(model_code) like 'LS%'
or upper(model_code) like 'LF%'
or upper(model_code) like 'LT%'
or upper(model_code) like 'LU%'
or upper(model_code) like 'LV%'
or upper(model_code) like 'LC%'
or upper(model_code) like 'C24%'
or upper(model_code) like 'C27%'
or upper(model_code) like 'C32%'
or upper(model_code) like 'C34%'
or upper(model_code) like 'F22%'
or upper(model_code) like 'S2%'
or upper(model_code) like 'S3%'
or upper(model_code) like 'S40%'
or upper(model_code) like 'S43%'
or upper(model_code) like 'S49%'
or upper(model_code) like 'S5%'
or upper(model_code) like 'TU2%'
or upper(model_code) like 'U32%'
or upper(model_code) like 'F24%'
or upper(model_code) like 'F27%' then 'Monitor'
when upper(model_code) like 'HW-Q%'
or upper(model_code) like 'HW-S%'
or upper(model_code) like 'HW-A%'
or upper(model_code) like 'HW-B%'
or upper(model_code) like 'HW-C%'
or upper(model_code) like 'HW-LS%'
or upper(model_code) like 'HW-T%' then 'Sound Bar'
when upper(model_code) like 'AF%'
or upper(model_code) like 'AC%'
or upper(model_code) like 'AR%'
or upper(model_code) like 'AJ%'
or upper(model_code) like 'AM%'
or upper(model_code) like 'AW%'
or upper(model_code) like 'PC1%'
or upper(model_code) like 'AN%'
or upper(model_code) like 'KFR-%' then 'AC'
when upper(model_code) like 'AX%'
or upper(model_code) like 'AY%'
or upper(model_code) like 'AP%' then 'Air Purifier'
when upper(model_code) like 'WW%'
or upper(model_code) like 'WA%'
or upper(model_code) like 'WV%'
or upper(model_code) like 'WD%'
or upper(model_code) like 'WF%'
or upper(model_code) like 'WR%'
or upper(model_code) like 'WH%'
or upper(model_code) like 'WT%' then 'Washer'
when upper(model_code) like 'DV%' then 'Dryer'
when upper(model_code) like 'DF%' then 'Air Dresser'
when upper(model_code) like 'DJ%' then 'Shoe Dresser'
when upper(model_code) like 'RF%'
or upper(model_code) like 'RB%'
or upper(model_code) like 'RL%'
or upper(model_code) like 'RQ%'
or upper(model_code) like 'RR%'
or upper(model_code) like 'RS%'
or upper(model_code) like 'RT%'
or upper(model_code) like 'RW%'
or upper(model_code) like 'RZ%'
or upper(model_code) like 'RH%'
or upper(model_code) like 'RP%'
or upper(model_code) like 'RM%'
or upper(model_code) like 'BR%'
or upper(model_code) like 'RK70%'
or upper(model_code) like 'RK80%' then 'REF'
when upper(model_code) like 'VR%'
or upper(model_code) like 'VS%'
or upper(model_code) like 'VC%'
or upper(model_code) like 'SC%'
or upper(model_code) like 'SS60K%' then 'VC'
when upper(model_code) like 'ME%'
or upper(model_code) like 'MJ%'
or upper(model_code) like 'ML%'
or upper(model_code) like 'MM%'
or upper(model_code) like 'MQ%'
or upper(model_code) like 'MW%'
or upper(model_code) like 'NA%'
or upper(model_code) like 'NE%'
or upper(model_code) like 'NK%'
or upper(model_code) like 'NL%'
or upper(model_code) like 'NQ%'
or upper(model_code) like 'NV%'
or upper(model_code) like 'NW%'
or upper(model_code) like 'NX%'
or upper(model_code) like 'NY%'
or upper(model_code) like 'NZ%'
or upper(model_code) like 'MC%'
or upper(model_code) like 'MG%'
or upper(model_code) like 'MO%'
or upper(model_code) like 'MS%'
or upper(model_code) like 'NS%'
or upper(model_code) like 'CC%'
or upper(model_code) like 'CTR%'
or upper(model_code) like 'C21RJAN%'
or upper(model_code) like 'NB69%'
or upper(model_code) like 'C61R%'
or upper(model_code) like 'SANK%' then 'Cooking'
when upper(model_code) like 'DW%' then 'DW'
when upper(model_code) like 'JBL%'
or upper(model_code) like 'HK%' then 'AUDIO'
when upper(model_code) like 'F-9%'
or upper(model_code) like 'F-55%'
or upper(model_code) like 'F-65%'
or upper(model_code) like 'F-80%'
or upper(model_code) like 'F-AR%'
or upper(model_code) like 'F-A%'
or upper(model_code) like 'F-F7%'
or upper(model_code) like 'F-M%'
or upper(model_code) like 'F-S7%'
or upper(model_code) like 'F-S9%'
or upper(model_code) like 'F-X%'
or upper(model_code) like 'F-NP%'
or upper(model_code) like 'F-58%'
or upper(model_code) like 'F-70%'
or upper(model_code) like 'F-75%'
or upper(model_code) like 'F-85%'
or upper(model_code) like 'F-LS%'
or upper(model_code) like 'F-Q%'
or upper(model_code) like 'F-UN%'
or upper(model_code) like 'F-3X%'
or upper(model_code) like 'F-09%'
or upper(model_code) like 'F-18%'
or upper(model_code) like 'F-2X%'
or upper(model_code) like 'F-CAC%'
or upper(model_code) like 'F-FJM%'
or upper(model_code) like 'F-W%'
or upper(model_code) like 'F-12%'
or upper(model_code) like 'F-NK%'
or upper(model_code) like 'F-RS%'
or upper(model_code) like 'PACKGE%' then 'BUNDLE'



else null end as CATEGORY

from unpivoted
)
,
matched as (
    select
        u.site_code,
        u.breakdown,
        u.pos,
        u.model_code,
        u.standard,
        u.unit,
        u.order,
        u.revenue,
        u.category,
        row_number() over (
            partition by u.site_code, u.breakdown, u.standard, u.pos
            order by (u.category is null), length(u.category) desc
        ) as rn
        , u.start_date,u.end_date
    from plus_category u
    -- left join prefix_map m
    --     on upper(u.model_code) like concat(m.prefix, '%')
),
final_rows as (
    select
        site_code,
        breakdown,
        pos,
        standard,
        unit,
        `order`,
        revenue,
        case when rn = 1 then category end as category
        , start_date, end_date
    from matched
),
before_last as (
    select
        case
            when g.site_code = 'ku' then 'IQ_KU'
            when g.site_code = 'uk_epp' then 'UK'
            else upper(g.site_code)
        end as site_code,
        g.breakdown as model_code,
        group_concat(g.category order by g.pos separator ',') as categories,
        -- group_concat(case when g.category <> 'ACC' then g.category end separator ',') as category_non_acc, -- AC, AC같은 케이스 없애고 싶으면 distinct 추가
        
        -- group_concat(g.category order by g.category separator ', ') as categories, 
        -- group_concat(distinct g.category order by g.category separator ',') as categories -- AC, AC같은 케이스 없애고 싶으면 distinct 추가
        group_concat(
        case when g.category <> 'ACC' then g.category end
        order by g.category
        separator ', '
        ) as category_non_acc,
        g.standard,
        max(g.unit) as unit,
        max(g.order) as `order`,
        max(g.revenue) as revenue
        , g.start_date, g.end_date
    from final_rows g
    group by
        g.site_code,
        g.breakdown,
        g.standard
)
select
'Prior Period (S.com Only)' as `PERIOD`,
    t.tier as `TIER`,
    t.subs as `SUBS`,
    t.country as `COUNTRY`,
    lst.site_code as `SITE CODE`,
    lst.standard as `STANDARD`,
    lst.model_code as `MODEL CODE`,
    lst.unit as `UNIT`,
    lst.order as `ORDER`,
    cast(lst.revenue * c.`2026-02-09` as decimal(20,6)) as `REVENUE`,
    lst.category_non_acc as `CATEGORY`,
    lst.revenue as `REVENUE ORIGIN`,
    lst.categories as `CATEGORIES ORIGIN`
    ,lst.start_date as `START DATE`, lst.end_date as `END DATE`
from before_last lst
left join campaign_tier_260128 t
    on lst.site_code = t.site_code
left join currency_260209 c
    on lst.site_code = c.site_code
    where lst.unit > 0 
    and lst.standard = 'S.com'
;

-- vrs로 바뀌며서 6곳은 이미 USD라서 환율 1로 적용.

select * from currency_260209 where site_code in ('de','uk','es','be','nl','pt');
