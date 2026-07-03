-- source: create_column.sql (2024-06)
-- 제조사별 지표 컬럼(company_name/Co.A/Cbrand/Google/Others)을 원본 테이블에 추가하는 ALTER TABLE
-- sanitized for public repo
ALTER TABLE tb_origin_whyproduct_mnfctrr
 ADD COLUMN `company_name` VARCHAR(255), ADD COLUMN `Co.A` VARCHAR(255), ADD COLUMN `Cbrand` VARCHAR(255)
 , ADD COLUMN `Google` VARCHAR(255), ADD COLUMN `Others` VARCHAR(255)
 ;
