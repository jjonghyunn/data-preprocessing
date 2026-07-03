-- source: create_combine.sql (2024-06)
-- 월별(2401~2405) 테이블을 UNION ALL 로 합쳐 단일 통합 테이블 생성
-- sanitized for public repo
create table global_table3_query_2401_2405 as
select * from (
select * from global_table3_query_2401
union all
select * from global_table3_query_2402
union all
select * from global_table3_query_2403
union all
select * from global_table3_query_2404
union all
select * from global_table3_query_2405
) combined_table
