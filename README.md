# data-preprocessing  
<sub>2026-10-01  Jonghyun Park w/ Claude</sub>  

preprocessing data — 캠페인 매핑·정제, 분석 결과 리마킹, SQL 쿼리 모음.

> 각 모듈 상세는 해당 폴더의 README를 참고하세요.  
> - 일정 자동화(메일 첨부 감시 → 워크북 반영)는 [`auto_mailing/schedule_automation/`](https://github.com/jjonghyunn/auto_mailing/tree/main/schedule_automation) 로 옮겼습니다.  
> - 리마킹 피봇 변환: [`remark_pivot_raw/README.md`](remark_pivot_raw/README.md)  
> - SQL 쿼리 모음: [`SQL/README.md`](SQL/README.md)

## 폴더 구조

```
data-preprocessing/
├── remark_pivot_raw/                 ← 분석 결과 xlsx/CSV → 외부 공유용 리마킹 (Classic/OLAP 피봇)
│   ├── remark_classic.py             ← Classic 피봇 xlsx 리마킹
│   ├── remark_olap.py                ← OLAP 피봇 (fact/dim CSV) 리마킹
│   ├── check_pivot_cache.py          ← 피봇 캐시 점검·추출
│   └── README.md                     ← remark_pivot_raw 상세 가이드
├── SQL/                              ← study SQL 쿼리 모음 (BigQuery·AA 패널)
│   ├── 01_ddl_dml_basics/ … 09_content/   ← 9개 카테고리, 총 40개 .sql
│   └── README.md                     ← 카테고리별 쿼리 인덱스
├── campaign_mapping_key_separator_260109v3.py    ← 캠페인 매핑 키 분리
├── campaign_main_value_mapping_251224_add_date.py ← 캠페인 main value 매핑 (+ 날짜)
├── campaign_default_value_splitter_251217.py     ← 캠페인 default value 분리
├── requirements.txt
├── .gitignore
└── LICENSE
```

---

## **remark_pivot_raw**

분석 결과 xlsx/CSV를 외부 공유용 리마킹 파일로 변환하는 스크립트 모음. 피봇 종류(Classic / OLAP)에 따라 도구가 나뉩니다. 상세는 `remark_pivot_raw/README.md` 참고.

---

## **SQL**

구글드라이브 `study_SQL` 아카이브를 주제별로 정리한 SQL 쿼리 모음 (BigQuery · Adobe Analytics 패널 기반). 총 40개 쿼리 / 9개 카테고리(DDL·DML, 윈도우 함수, UNION·pivot, 페이지 경로·세션, 기획전 컨버전, 검색 키워드, 상품, 트래픽 지표, 콘텐츠). 회사 식별자(도메인·스키마·캠페인명 등)는 placeholder로 sanitize 처리. 상세는 `SQL/README.md` 참고.

---

## 캠페인 매핑 스크립트 (루트)

캠페인 매핑 테이블(CSV/xlsx)을 정제·변환하는 유틸. 입력 파일을 읽어 결과 CSV/xlsx 를 같은 폴더에 출력한다(`campaign_main_value_mapping_*` 는 xlsx 출력).

> ⚠ **입력 폴더는 스크립트마다 다르다.** `campaign_main_value_mapping_*` 만 `base_dir = Path.home()/"Downloads"` 로 홈 기준 자동 탐색이고, `campaign_mapping_key_separator_*`·`campaign_default_value_splitter_*` 는 `base_dir = r'C:\Users\{username}\Downloads'` 라는 **리터럴 placeholder**(f-string 아님 → `{username}` 이 치환되지 않음)이므로 실행 전 직접 고쳐야 한다.

결과 파일 접미사도 스크립트마다 다르다 — `campaign_main_value_mapping_*` 는 **입력 파일명의 `YYMMDD_HHMMSS` 패턴**에서 추출하고, `campaign_mapping_key_separator_*`·`campaign_default_value_splitter_*` 는 **실행 시각(`datetime.now()`)**을 접미사로 붙인다. 파일 상단의 경로·파일명 상수만 바꿔 재사용.

| 파일 | 역할 |
|---|---|
| `campaign_mapping_key_separator_*.py` | 매핑 키를 분리해 `separated_*` + `report_format_*` CSV 생성 |
| `campaign_main_value_mapping_*.py` | 입력 CSV 값을 xlsx 매핑표에 조인해 main value 매핑 (+ 날짜) |
| `campaign_default_value_splitter_*.py` | `metric` 컬럼을 `_` 기준으로 `split1`·`split2`… 컬럼으로 분리 |
