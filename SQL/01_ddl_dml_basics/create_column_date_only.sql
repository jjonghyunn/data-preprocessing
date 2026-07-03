-- source: create_column2.sql (2024-08)
-- day 테이블에 DATE 타입 date_only 컬럼을 NULL 값으로 추가
-- sanitized for public repo
ALTER TABLE day
ADD date_only DATE -- null값으로 칼럼생성
