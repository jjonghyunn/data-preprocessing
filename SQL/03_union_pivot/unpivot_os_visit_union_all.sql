-- source: 240610_us_div1_visit_user_id2.sql (2024-06)
-- OS(ios/and/others/ALL)별 방문값을 UNION ALL 로 세로 전개(unpivot)하는 쿼리
-- sanitized for public repo
WITH A AS (
    SELECT
        *,
        case when 'visit_ios' is not null then "ios" else null end AS OS1,
        case when 'visit_and' is not null then "and" else null end AS OS2,
        visit_mo -( COALESCE(visit_ios, 0) + COALESCE(visit_and, 0) ) AS visit_others,
        case when 'visit_others' is not null then "others" else null end AS OS3,
        case when 'visit_mo' is not null then "ALL" else null end AS OS4
    FROM act.us_div1_visit
)

SELECT
    site_code,
    breakdown,
    visit,
    visit_mo,
    OS1 AS OS,
    visit_ios AS visit_value

FROM A
WHERE visit_ios IS NOT NULL

UNION ALL

SELECT
    site_code,
    breakdown,
    visit,
    visit_mo,
    OS2 AS OS,
    visit_and AS visit_value

FROM A
WHERE visit_and IS NOT NULL

UNION ALL

SELECT
    site_code,
    breakdown,
    visit,
    visit_mo,
    OS3 AS OS,
    visit_others AS visit_value

FROM A

UNION ALL

SELECT distinct
    site_code,
    breakdown,
    visit,
    visit_mo,
    OS4 AS OS,
    visit_mo AS visit_value
FROM A

WHERE visit_others IS NOT NULL;
