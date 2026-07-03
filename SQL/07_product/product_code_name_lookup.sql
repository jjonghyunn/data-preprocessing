-- source: 상품코드,상품명-쿼리 240103 / 시트1 (2024-01)
-- 상품 마스터에서 판매 가능 상태의 상품코드(GdsNo)·상품명(GdsNm)을 등록일 역순으로 조회
SELECT GdsNo, GdsNm
FROM `gdsList_raw.{YYYYMMDD}`  -- 원본: 시트 셀 참조로 일자별 raw 테이블 지정
WHERE GdsStat NOT IN ('단종', '임시저장','삭제','판매보류','판매대기','품절')
ORDER BY GdsRegYmdt DESC
