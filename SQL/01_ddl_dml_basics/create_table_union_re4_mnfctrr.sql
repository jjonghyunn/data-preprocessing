-- source: create_table.sql (2024-06)
-- 두 가공 테이블(re4 / mnfctrr)을 UNION 하여 신규 통합 테이블 생성
-- sanitized for public repo
create table tb_query_whyproduct_user_id2 as
select * from tb_query_whyproduct_re4
union
select * from tb_query_whyproduct_mnfctrr
