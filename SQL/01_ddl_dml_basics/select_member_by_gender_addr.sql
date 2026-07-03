-- source: study_230808.sql (2023-08)
-- Member 테이블에서 성별 필터 조회 및 주소(addr)별 회원수 집계 (SQL 기초 학습)
USE edu;
SELECT *
FROM [Member]
where gender = 'man';

select addr
,COUNT(mem_no) as [회원수]
from [Member]
group
by addr;
