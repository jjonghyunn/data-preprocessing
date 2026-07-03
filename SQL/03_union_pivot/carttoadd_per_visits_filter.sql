-- source: 240520_study1.sql (2024-05)
-- 장바구니 담기/방문 지표 테이블에서 visits 5백만 이상 행만 필터
-- sanitized for public repo
with A as(
select * from act.`carttoadd-per-visits-month2-2401-2404`
where visits >= 5000000
)
select * from A
