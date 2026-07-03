-- source: union_aa-panel.sql (2024-06)
-- 원본 테이블의 all/pc/mobile 디바이스별 지표를 device 축으로 UNION ALL 정규화 후 테이블 생성
-- sanitized for public repo
CREATE TABLE tb_query_whyproduct_re4 AS
WITH
tb_all AS (
    SELECT
    site_code,
        start_date as month,
        start_date as year,
        dimension as marketingchannel,
        device1 AS device,
        `Manufacturers`as`Manufacturer`,
        all_visit AS visit,
        all_entry AS entry,
        all_bounce AS bounce,
        all_timespent AS timespent,
        all_order AS `order`

    FROM tb_origin_whyproduct_re2
),
tb_pc AS (
    SELECT
     site_code,
        start_date as month,
        start_date as year,
        dimension as marketingchannel,
        device3 AS device,
        `Manufacturers`as`Manufacturer`,
        pc_visit AS visit,
        pc_entry AS entry,
        pc_bounce AS bounce,
        pc_timespent AS timespent,
        pc_order AS `order`
    FROM tb_origin_whyproduct_re2
),
tb_mobile AS (
    SELECT
        site_code,
        start_date as month,
        start_date as year,
        dimension as marketingchannel,
        device2 AS device,
        `Manufacturers`as`Manufacturer`,
        mobile_visit AS visit,
        mobile_entry AS entry,
        mobile_bounce AS bounce,
        mobile_timespent AS timespent,
        mobile_order AS `order`
    FROM tb_origin_whyproduct_re2
)
SELECT * FROM tb_all
UNION ALL
SELECT * FROM tb_pc
UNION ALL
SELECT * FROM tb_mobile;
