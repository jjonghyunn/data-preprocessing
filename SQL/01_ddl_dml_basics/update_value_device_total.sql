-- source: update_value.sql (2024-06)
-- device 값 'All' 을 'Total' 로 일괄 UPDATE
-- sanitized for public repo
UPDATE tb_query_whyproduct_re2
SET device = 'Total'
WHERE device = 'All';
