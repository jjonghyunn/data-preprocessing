-- source: union_aa-panel2.sql (2024-06)
-- 제조사(company_name/Co.A/Cbrand/Google/Others)별 지표 컬럼을 Manufacturer 축으로 UNION ALL 정규화 후 테이블 생성
-- sanitized for public repo
CREATE TABLE tb_query_whyproduct_mnfctrr AS
WITH
tb1 AS (
    SELECT
    site_code,

        start_date as month,
        start_date as year,
        dimension as marketingchannel,
        device AS device,
        `company_name` as `Manufacturer`,
        brandA_visit AS visit,
        brandA_entry AS entry,
        brandA_bounce AS bounce,
        brandA_timespent AS timespent,
        brandA_order AS `order`

    FROM tb_origin_whyproduct_mnfctrr
),
tb2 AS (
    SELECT
     site_code,

    start_date as month,
        start_date as year,
                        dimension as marketingchannel,
                        device AS device,
                        `Co.A` as `Manufacturer`,
        apple_visit AS visit,
        apple_entry AS entry,
        apple_bounce AS bounce,
        apple_timespent AS timespent,
        apple_order AS `order`

    FROM tb_origin_whyproduct_mnfctrr
),
tb3 AS (
    SELECT
     site_code,

    start_date as month,
        start_date as year,
                        dimension as marketingchannel,
                        device AS device,
                        `Cbrand` as `Manufacturer`,
        C_visit AS visit,
        C_entry AS entry,
        C_bounce AS bounce,
        C_timespent AS timespent,
        C_order AS `order`

    FROM tb_origin_whyproduct_mnfctrr
),
tb4 AS (
    SELECT
     site_code,

    start_date as month,
        start_date as year,
                        dimension as marketingchannel,
                        device AS device,
                        `Google` as `Manufacturer`,
        google_visit AS visit,
        google_entry AS entry,
        google_bounce AS bounce,
        google_timespent AS timespent,
        google_order AS `order`

    FROM tb_origin_whyproduct_mnfctrr
),
tb5 AS (
    SELECT
     site_code,

    start_date as month,
        start_date as year,
                        dimension as marketingchannel,
                        device AS device,
                        `Others` as `Manufacturer`,
        others_visit AS visit,
        others_entry AS entry,
        others_bounce AS bounce,
        others_timespent AS timespent,
        others_order AS `order`

    FROM tb_origin_whyproduct_mnfctrr
)

SELECT * FROM tb1
UNION ALL
SELECT * FROM tb2
UNION ALL
SELECT * FROM tb3
UNION ALL
SELECT * FROM tb4
UNION ALL
SELECT * FROM tb5
