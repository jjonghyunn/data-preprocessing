# launch/utils/ — 추출 핵심 모듈

6개 추출 노트북이 공통으로 import하는 유틸리티 패키지.  
직접 실행하는 파일이 아니라 노트북 실행 시 자동으로 로드되는 라이브러리입니다.

---

## 모듈 목록

| 모듈 | 역할 |
|---|---|
| `aa_exporter.py` | AA API 호출 / 페이지네이션 / CSV 저장 코어 |
| `site_registry.py` | site code → RSID / 국가 메타 조회 |
| `check_failed_status.py` | `aa_exports/` CSV에서 FAILED 행 집계 |

---

## 모듈별 상세

### `aa_exporter.py`

AA Data API 추출 전체를 담당하는 메인 클래스.

**`ExportConfig` (dataclass)**  
25+ 파라미터로 추출 동작을 제어합니다. 주요 항목:

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `limit` | 50,000 | 페이지당 최대 행 수 |
| `max_workers` | 6 | 병렬 site 처리 스레드 수 |
| `parallel_sites` | True | 병렬 추출 ON/OFF |
| `sleep_between` | - | 요청 간 대기(초) |

**`AAExporter` (class)**

```
입력: site_code CSV  →  JSON payload 로드  →  API 호출 (페이지네이션)
    →  임시 CSV 누적  →  병합 → 최종 CSV 저장
```

- `ThreadPoolExecutor`로 site별 병렬 추출
- HTTP 429 / 5xx 응답 시 지수 백오프 재시도
- 추출 실패 행은 `status=FAILED`로 마킹해 CSV에 포함
- 추출 성공 행의 메트릭 컬럼명은 `ExportConfig.metric_col_map`으로 rename

**인증**  
환경변수(`AA_API_KEY`, `AA_ACCESS_TOKEN`, `AA_GLOBAL_COMPANY_ID`) 또는 `aanalyticsact_auth.json` 파일 중 하나를 사용.

---

### `site_registry.py`

site code 문자열을 받아 `SiteInfo`를 반환하는 단일 함수 모듈.

**`SiteInfo` (frozen dataclass)**

| 필드 | 설명 |
|---|---|
| `subsidiary` | 법인명 |
| `country` | 국가 코드 |
| `site_code` | 정규화된 site code |
| `rsid` | Report Suite ID |

**`lookup_site(code)` 해석 순서**

1. 정규화 코드 그대로 `_SITE_MASTER` 조회 (예: `"ca_fr"`)
2. underscore 제거 후 재조회 (예: `"cafr"` → `"ca_fr"` 매칭)
3. 없으면 `company_rsid_{normalized_code}` 패턴으로 fallback rsid 생성

> RS ID가 변경된 경우(VRS 교체, US 특이 케이스 등) `_SITE_MASTER` 딕셔너리를 직접 수정해야 합니다.  
> 관련 안내: 상위 폴더 `README.md` → STEP 1 참고.

---

### `check_failed_status.py`

`aa_exports/` 폴더의 추출 결과 CSV를 스캔해 FAILED 건수를 리포트하는 진단 도구.

**검사 대상 파일**  
- `aa_exports/*.csv` 중 `union*`, `*separate*` 제외한 원본 추출 파일만 검사

**출력 분류**

| 표시 | 의미 |
|---|---|
| `❌` | FAILED 행이 있는 파일 (건수 표시) |
| `-` | status 컬럼 없음 |
| `!` | 파일 읽기 오류 |

> 이 모듈은 노트북에서 import해서 쓰는 버전입니다.  
> 루트 폴더의 `check_failed_status_260313.py`는 단독 실행용 버전으로, US 파일에서 OK 행이 0개인 경우 추가 경고(`⚠️ 추출 값 없음`)를 출력합니다.

---

## `__init__.py`

패키지 노출용 빈 파일. 수정 불필요.
