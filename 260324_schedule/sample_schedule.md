# campaign schedule — 캠페인 일정 자동 정제 Excel 도구

> 처음 보는 사람을 위한 구조·수식 가이드
> 작성: 2026-03-24 / 최종 수정: 2026-03-25
> **※ 이 README는 공개용 샘플입니다. 법인명은 XX 형식으로 익명화, 담당자는 가명 처리.**

---

## 개요

이 도구는 **캠페인 일정(schedule) 데이터를 자동으로 정제해주는 Excel 파일**입니다.

**입력**: 고객(파트너) 파일의 법인별 참여 여부·일정 → `AU:BB` 구간에 붙여넣기
**출력**: `A:H` 구간에 `SORT/UNIQUE/FILTER`로 자동 정렬된 최종 일정표

Excel 2019+ 및 Google Sheets 양쪽에서 동작하도록 수식을 구성했습니다.

---

## 파일 구성

```
260324_schedule/
├── README.md                  ← 이 파일
├── schedule_수식모음.txt       ← 핵심 수식 모음 (익명화)
├── create_sample_xlsx.py      ← 샘플 xlsx 생성 스크립트
└── sample_schedule.xlsx    ← 생성된 샘플 파일 (Excel/Sheets로 열기)
```

---

## 열 구성 (5개 블록)

```
A  B  C  D  E  F  G  H    …    M  N  O  P  Q  R  S  T  U    …    Z  AA AB AC AD AE AF AG AH    …    AL AM AN AO AP    …    AT AU AV AW AX AY AZ BA BB
```

| 블록 | 열 범위 | 역할 |
|------|---------|------|
| ① 최종 출력 | A:H | A4 단일 수식이 스필(spill). 편집 불가 |
| ② 중간 연산 | M:T + U | 행별 수식으로 출력값 조합. **여기를 수정하면 ①이 바뀜** |
| ③ Site 마스터 | Z:AG (+ AH) | 전체 site 목록. 직접 편집하지 않음 |
| ④ 헬퍼 | AL:AP | 고객 파일 ↔ 마스터 매핑 중간 계산. 직접 편집하지 않음 |
| ⑤ 고객 파일 | AT:BB | 고객 파일에서 복사해 붙여넣는 영역 |

---

## 데이터 흐름

```
[고객 파일] ── 붙여넣기 ──▶ AU:BB
                                │
                    ④ 헬퍼 열 자동 계산
                    AL(AR_clean) → AM(AR_key) → AN(Participation) → AO/AP(날짜)
                                │
                    ② 중간 연산 블록 (M:T) 자동 갱신
                    O열 Subs = AM 기반 (고객 파일 형식 그대로)
                                │
                    ① A4 수식이 M:T에서 FILTER → UNIQUE → SORT
                                │
                    [최종 출력] A:H 자동 스필
```

---

## 블록별 상세 설명

### ① 최종 출력 (A:H)

A4 셀 하나의 수식이 아래 전체를 채웁니다.

```excel
=SORT(UNIQUE(FILTER(M4:T200,
    (Q4:Q200<>"") * (S4:S200<>"") * (U4:U200<>"O")
)))
```

| 조건 | 의미 |
|------|------|
| `Q<>""` | RS가 있는 행만 (site_code가 있는 유효한 site) |
| `S<>""` | start_date가 있는 행만 (참여 확정 + 날짜 있음, 또는 X) |
| `U<>"O"` | U열(추천제외)에 `O` 표시된 행 제외 |

**→ 편집 절대 금지.** 내용을 바꾸려면 M:T 블록 수식을 수정합니다.

---

### ② 중간 연산 블록 (M:T)

| 열 | 헤더 | 수식 요약 |
|----|------|-----------|
| M | Tier | 수동 입력 |
| N | RHQ | `=IF(ISBLANK(AD),"",AA)` — 마스터 AA열 |
| **O** | **Subs** | `=IF(ISBLANK(AD),"",IF(AM="한총","KR",IF(LEN(TRIM(AM))=0,AB,AM)))` |
| P | COUNTRY | `=IF(ISBLANK(AD),"",AC)` |
| Q | RS | `=IF(ISBLANK(AD),"",AH)` |
| R | site_code | `=IF(ISBLANK(Z),"",AD)` |
| S | start_date | `=IF(ISBLANK(AD),"",IF(AN="X","X",AO))` |
| T | end_date | `=IF(ISBLANK(AD),"",IF(AN="X","",AP))` |
| U | 추천제외 | 수동 입력. `O` 입력하면 최종 출력에서 제외 |

#### O열 Subs 수식 설명 (핵심)

```excel
=IF(ISBLANK(AD4), "",
    IF(AM4="한총", "KR",
        IF(LEN(TRIM(AM4))=0, AB4, AM4)
    )
)
```

| 조건 | 결과 | 예시 |
|------|------|------|
| AD(site_code) 비어있음 | `""` | (마스터 빈 행) |
| AM = "한총" | `"KR"` | 한국법인 → KR |
| AM이 비어있음 (매칭 실패) | AB 폴백 | 마스터 표준명 사용 |
| 그 외 | AM 그대로 | `UK`, `BN-BE`, `UK-IE` 등 |

---

### ③ Site 마스터 (Z:AG)

전체 site 목록이 고정으로 입력된 참조 테이블입니다.

| 열 | 헤더 | 내용 |
|----|------|------|
| Z | # | 번호 |
| AA | RHQ | 지역본부 (MENA, EU, N.America …) |
| AB | Subsidiary | 표준 법인명 (UK, BN, WA …) |
| AC | Country | 국가명 |
| AD | SiteCode | site_code (ae, be, uk …) |
| AE | URL | 사이트 URL |
| AF | Platform | HQ Shop / Non-shop 등 |
| AG | App | O / X |
| AH | RS | RS 표시명 (site_code 기반 자동 변환) |

**→ 편집 금지.** 새 site 추가가 필요하면 하단에 행 추가 후 수식 복사.

---

### ④ 헬퍼 열 (AL:AP)

고객 파일(AU열)과 Site 마스터(AB열)를 자동으로 연결합니다.
**직접 편집하지 않습니다.**

#### AL — AR_clean

AU열 Subs명의 접미어를 제거한 정제값.

| AU 원본 | AL 결과 |
|---------|---------|
| `BN-BE` | `BN` |
| `AS-SG` | `AS` |
| `SA (ZA)` | `SA` |
| `한총` | `한총` |

AM열이 폴백 조회할 때 이 값을 사용합니다.

#### AM — AR_key (7단계 우선순위)

AB(마스터 표준 법인명)에 대응하는 **AU열 조회 키**를 결정합니다.

```
1순위: AB + "-" + UPPER(site_code "_" 앞부분) 형태가 AU에 있으면 → dash-variant 키 사용
       예) AB=BN, site_code=be  → "BN-BE"  → AU에 있음 → AM=BN-BE
           AB=UK, site_code=ie  → "UK-IE"  → AU에 있음 → AM=UK-IE  ★site 우선
           AB=AS, site_code=sg  → "AS-SG"  → AM=AS-SG

1.5순위 ★: AB + " (PROPER(prefix)_UPPER(suffix))" 형태가 AU에 있으면 → 괄호-variant 키 사용
       site_code에 "_"가 있을 때, "_" 기준으로 앞부분은 PROPER, 뒷부분은 UPPER로 조합
       예) AB=WA, site_code=africa_en → "WA (Africa_EN)" → AU에 있음 → AM=WA (Africa_EN)
           AB=WA, site_code=africa_fr → "WA (Africa_FR)" → AU에 있음 → AM=WA (Africa_FR)
           AB=WA, site_code=africa_pt → "WA (Africa_PT)" → AU에 없음 → 다음 순위로
       * site_code에 "_"가 없으면 COUNTIF 오류 → 0으로 처리되어 안전하게 통과

2순위: AB 값이 AU에 그대로 있으면 → AB 사용
       예) AB=UK → AU에 UK 있음 → AM=UK

2.5순위 ★: site_code에 "_"가 포함된 경우 → 즉시 "" 반환 (3순위 이하 스킵)
       2순위까지 실패했고 site_code에 "_"가 있다는 것은 고객파일에 대응 항목이 없는 지역 변형 site.
       AM=""로 두면 O열에서 AB(마스터 표준명) 폴백이 적용되고, 해당 값이 AU에 없으면 최종 출력에서 자동 제외.
       예) AB=WA, site_code=africa_pt → 1.5/2순위 실패 → AM="" → O=AB="WA"
           → AU에 plain "WA" 없음 → AN="" → 최종 출력 미포함

3순위: AL(AR_clean)로 AU에서 MATCH 후 원본 반환  ← site_code에 "_" 없는 사이트에만 적용
       예) AB=SA → AL="SA" → AU에서 "SA (ZA)" 검색 → AM=SA (ZA)

4순위: AB 자체에 "-" 포함된 경우 → AB 앞부분만으로 AU 검색
       예) AB=EG-S → LEFT(AB, "-" 앞) = "EG" → AU에 있음 → AM=EG

5순위: AB = "CA"인 경우 → site_code 끝 3자리로 Africa 구분  (현재 사실상 미사용)
       예) site_code=africa_fr → "_fr" → AM=WA (Africa_FR)
           site_code=africa_en → "_en" → AM=WA (Africa_EN)
       ※ WA Africa 사이트는 현재 AB="WA"로 관리되어 1.5순위에서 처리됨.
```

> **1.5순위와 2.5순위는 쌍으로 동작합니다.**
> 괄호-variant(WA Africa_EN/FR)는 1.5순위에서, 매칭 실패한 지역 변형(africa_pt)은 2.5순위에서 처리합니다.

#### AN — Participation

AM 키로 AW열(Participation) 조회.

| 값 | 의미 |
|----|------|
| `O` | 참여 → start/end 날짜 가져옴 |
| `X` | 미참여 → start에 X 표시, end 공백 |
| ` ` (공백) | 미회신 / 미정 → 날짜 없음, 최종 출력 미포함 |

#### AO / AP — start_raw / end_raw

AN = O일 때만 AX(Starts at), AZ(Ends at)에서 날짜 가져옵니다.

---

### ⑤ 고객 파일 입력 구간 (AT:BB)

고객 파일에서 복사해 붙여넣는 유일한 영역입니다.

| 열 | 헤더 | 내용 |
|----|------|------|
| AT | Region | 지역 구분 — 소계 구분용 |
| AU | Subs | 법인명 (고객 파일 그대로) |
| AV | PIC | 담당자 |
| AW | Participation | 참여 여부 (O / X / 공백) |
| AX | Starts at | 시작일 또는 TBC |
| AY | (Week) | 시작 주차 |
| AZ | Ends at | 종료일 또는 TBC |
| BA | (Week) | 종료 주차 |
| BB | Note | 메모 |

> **AT열에 값이 있는 행**(Region 소계 행)은 헬퍼 계산에서 자동 제외됩니다.
> **AU = "Total" 행**도 자동 제외됩니다.

#### AS열 — 사용 안됨 체크

```excel
=IF((AW="X")+(AW=""), "",
    IF(COUNTIF($O$4:$O$191, IF(AU="한총","KR",AU)) > 0, "", "사용 안됨")
)
```

- **공백** → 정상 반영됨
- **"사용 안됨"** → AU의 이 Subs가 마스터에 매핑되지 않음

---

## 샘플 데이터 예시

샘플 xlsx에는 아래 구조로 익명화된 데이터가 들어 있습니다.

### 마스터 (Z:AG)

| # | RHQ | Subsidiary | Country | SiteCode |
|---|-----|-----------|---------|----------|
| 1 | EU | UK | United Kingdom | uk |
| 2 | EU | UK | Ireland | ie |
| 3 | EU | BN | Belgium | be |
| 4 | AF | WA | Africa | africa_en |
| 5 | AF | WA | Africa | africa_fr |
| 6 | AF | WA | Africa | africa_pt |
| 7 | AP | 한총 | Korea | kr |
| 8 | AF | SA | South Africa | za |

### 고객 파일 입력 (AT:BB)

| Region | Subs | PIC | Participation | Starts at | Ends at |
|--------|------|-----|--------------|-----------|---------|
| EU Region | Total | | | | |
| | UK | 홍길동 | O | 2026-04-01 | 2026-05-31 |
| | UK-IE | 김철수 | O | 2026-04-15 | 2026-05-31 |
| | BN-BE | 이영희 | X | | |
| AF Region | Total | | | | |
| | WA (Africa_EN) | 박민준 | O | 2026-04-01 | 2026-05-31 |
| | WA (Africa_FR) | 최수진 | X | | |
| AP Region | Total | | | | |
| | 한총 | 정다영 | O | 2026-04-08 | 2026-05-31 |
| | SA (ZA) | 강민서 | (미회신) | | |

### 예상 최종 출력 (A:H)

africa_pt (고객파일 미등록) / SA (미회신)은 제외됩니다.

| RHQ | Subs | Country | RS | site_code | start_date | end_date |
|-----|------|---------|-----|-----------|-----------|---------|
| EU | UK | United Kingdom | United Kingdom | uk | 2026-04-01 | 2026-05-31 |
| EU | UK-IE | Ireland | Ireland | ie | 2026-04-15 | 2026-05-31 |
| EU | BN-BE | Belgium | Belgium | be | X | |
| AF | WA (Africa_EN) | Africa | Africa (en) | africa_en | 2026-04-01 | 2026-05-31 |
| AF | WA (Africa_FR) | Africa | Africa (fr) | africa_fr | X | |
| AP | KR | Korea | Korea | kr | 2026-04-08 | 2026-05-31 |

---

## 작업 절차

1. **고객 파일 열기** — AU:BB 구간의 기존 데이터 확인
2. **AU:BB 구간 업데이트** — 새 데이터 붙여넣기 (AT열 Region 소계행 포함)
3. **AS열 확인** — "사용 안됨"이 뜨는 Subs가 있으면 AM열과 마스터 확인
4. **U열(추천제외)** — 최종 출력에서 뺄 site는 U열에 `O` 입력
5. **A:H 출력 확인** — 자동으로 정렬·필터된 결과 확인

---

## 알려진 제약

| 케이스 | 현상 | 해결 |
|--------|------|------|
| 한총 (한국법인) | AU = "한총" → AM 매칭 → O열에서 KR 강제 변환 | 자동 처리됨 |
| EG-S (이집트 등) | AB="EG-S", AU="EG" — 이름 불일치 | AM 4순위 자동 처리 |
| UK-IE (아일랜드) | AB="UK", AU="UK-IE" — base 이름이 먼저 매칭될 위험 | AM 1순위 우선 처리 |
| WA Africa_EN/FR | AU="WA (Africa_EN/FR)" — AL 정제 시 둘 다 "WA"로 동일해져 3순위 오매칭 | AM 1.5순위 PROPER/UPPER 패턴 직접 조회 |
| WA Africa_PT | 고객파일 미등록 → AM="" → O=AB="WA" → AU에 없음 → 최종 출력 제외 | AM 2.5순위 자동 처리 |
| 마스터에 없는 신규 법인 | AS = "사용 안됨" | Z-AG 하단에 행 추가 필요 |
| TBC 날짜 | start/end = "TBC" 그대로 출력 | 날짜 확정 후 고객 파일 갱신 |
| 미회신 (AW 공백) | 출력 미포함 (S열 공백 → FILTER 제외) | 참여 여부 확정 후 AW 업데이트 |

---

## 수식 호환성

| 함수 | Excel | Google Sheets |
|------|-------|---------------|
| `SORT` | O (2019+) | O |
| `UNIQUE` | O (2019+) | O |
| `FILTER` | O (2019+) | O |
| `COUNTIF` | O | O |
| `INDEX/MATCH` | O | O |
| `PROPER` | O | O |
| `ANCHORARRAY` | O | **X** — 이 파일에서 제거됨 |

> v260324: `ANCHORARRAY` 의존 수식 제거. Excel 2019+ 및 Google Sheets 모두 동작.
> v260325: AM 수식 1.5/2.5순위 추가. `PROPER` 신규 사용.
