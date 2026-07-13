# data-preprocessing  
<sub>2026-07-13  Jonghyun Park w/ Claude</sub>  

preprocessing data — 캠페인 매핑·정제, 일정 자동화, 분석 결과 리마킹, SQL 쿼리 모음.

> 각 모듈 상세는 해당 폴더의 README를 참고하세요.  
> - 일정 자동화: [`260324_schedule/README.md`](260324_schedule/README.md)  
> - 리마킹 피봇 변환: [`remark_pivot_raw/README.md`](remark_pivot_raw/README.md)  
> - SQL 쿼리 모음: [`SQL/README.md`](SQL/README.md)

## 폴더 구조

```
data-preprocessing/
├── 260324_schedule/                  ← 캠페인 일정 자동화 (xlsx 정제 + Outlook 첨부 감지)
│   ├── update_schedule.py            ← 고객 일정 xlsx → Auto 정제 파일 업데이트
│   ├── check_mail_attachment.py      ← Outlook 신규 첨부 xlsx 감지·저장
│   └── create_schtasks_v2.txt        ← 작업 스케줄러 등록 명령어(전체 경로 포함) 모음
├── remark_pivot_raw/                 ← 분석 결과 xlsx/CSV → 외부 공유용 리마킹 (Classic/OLAP 피봇)
├── SQL/                              ← study SQL 쿼리 모음 (BigQuery·AA 패널, 9개 카테고리)
├── campaign_mapping_key_separator_260109v3.py    ← 캠페인 매핑 키 분리
├── campaign_main_value_mapping_251224_add_date.py ← 캠페인 main value 매핑 (+ 날짜)
├── campaign_default_value_splitter_251217.py     ← 캠페인 default value 분리
└── requirements.txt
```

---

## **260324_schedule**

캠페인 법인별 일정 파일을 자동 정제 Excel에 반영하고, Outlook 수신함에서 첨부파일을 감지해 저장하는 자동화 스크립트 모음.

### 주요 스크립트

| 파일 | 역할 |
|---|---|
| `update_schedule.py` | 최신 고객 일정 xlsx → Auto 정제 파일 업데이트 |
| `check_mail_attachment.py` | Outlook 수신함 → 신규 첨부 xlsx 로컬 저장 |

### 작업 스케줄러 자동 실행

`pythonw.exe`로 작업 스케줄러에 직접 등록 (bat/vbs 래퍼 불필요).  
등록 명령어, 배터리 모드 허용, 트러블슈팅 등 상세는 `260324_schedule/README.md` 참고.

---

## **remark_pivot_raw**

분석 결과 xlsx/CSV를 외부 공유용 리마킹 파일로 변환하는 스크립트 모음. 피봇 종류(Classic / OLAP)에 따라 도구가 나뉩니다. 상세는 `remark_pivot_raw/README.md` 참고.

---

## **SQL**

구글드라이브 `study_SQL` 아카이브를 주제별로 정리한 SQL 쿼리 모음 (BigQuery · Adobe Analytics 패널 기반). 총 40개 쿼리 / 9개 카테고리(DDL·DML, 윈도우 함수, UNION·pivot, 페이지 경로·세션, 기획전 컨버전, 검색 키워드, 상품, 트래픽 지표, 콘텐츠). 회사 식별자(도메인·스키마·캠페인명 등)는 placeholder로 sanitize 처리. 상세는 `SQL/README.md` 참고.

---

## 캠페인 매핑 스크립트 (루트)

캠페인 매핑 테이블(CSV/xlsx)을 정제·변환하는 유틸. 모두 `~/Downloads` 의 입력 파일을 읽어 타임스탬프가 붙은 결과 CSV/xlsx 를 같은 폴더에 출력한다(`campaign_main_value_mapping_*` 는 xlsx 출력). 파일 상단의 경로·파일명 상수만 바꿔 재사용.

| 파일 | 역할 |
|---|---|
| `campaign_mapping_key_separator_*.py` | 매핑 키를 분리해 `separated_*` + `report_format_*` CSV 생성 |
| `campaign_main_value_mapping_*.py` | 입력 CSV 값을 xlsx 매핑표에 조인해 main value 매핑 (+ 날짜) |
| `campaign_default_value_splitter_*.py` | default value 컬럼을 분리 |
