# mail_search_to_msg.py 가이드
<!-- 2026-04-30  Jonghyun Park w/ Claude -->

`team_name` 메일함에서 키워드 매칭되는 메일을 `.msg` 파일로 다운로드하는 스크립트.

검색 결과는 `~/Downloads/mail_search_<YYMMDD>/` 폴더에 일괄 저장.

---

## 동작 흐름

```
Outlook.Application (win32com)
    ↓
GetNamespace("MAPI")
    ↓
Stores 중 STORE_NAME(부분 일치) 선택  → team_name
    ↓
Inbox(받은편함) 또는 지정 폴더 진입
    ↓
(옵션) 하위 폴더 재귀 순회
    ↓
각 메일에 대해 — Subject + (옵션) Body lowercase 결합
    ↓
KEYWORDS 중 어느 하나라도 substring 매칭? (OR, 대소문자 무관)
    ↓
MailItem.SaveAs(path, 3)  # 3 = olMSG
    ↓
~/Downloads/mail_search_<YYMMDD>/<YYMMDD_HHMM>_<safe subject>.msg
```

---

## 설정 (스크립트 상단)

| 변수 | 기본값 | 의미 |
|---|---|---|
| `KEYWORDS` | `["CAMPAIGN NAME"]` | 검색 키워드 리스트. 어느 하나라도 포함되면 매칭 (OR). 대소문자 무관 |
| `STORE_NAME` | `"team_name"` | Outlook 메일함 DisplayName 부분 일치로 검색 |
| `FOLDER_NAME` | `None` | `None`이면 받은편함(Inbox). 다른 폴더 이름(예: `"매칭 메일"`) 지정 가능 |
| `RECURSE_SUBFOLDERS` | `False` | True면 하위 폴더까지 재귀 검색 |
| `SEARCH_BODY` | `True` | False면 제목만 검색 (수천 개 메일 처리 시 훨씬 빠름) |

---

## 실행

```bash
python mail_search_to_msg.py
```

매번 키워드 바뀌면 스크립트 상단 `KEYWORDS` 리스트 수정 후 실행.

---

## 출력 파일명 규칙

```
<YYMMDD_HHMM>_<safe subject>.msg
```

- `YYMMDD_HHMM` — 메일 수신 시각 (`ReceivedTime`)
- `safe subject` — Windows 금지문자(`<>:"/\\|?*` + 제어문자) 모두 `_` 로 치환, 길이 150자 제한
- 동일 파일명 중복 시 `(2)`, `(3)` ... 자동 부여
- 이미 저장된 파일이 있으면 자동으로 다음 번호 사용

---

## 성능 팁

- 받은편함 수천 개 메일에서 본문(Body)까지 검색하면 **수십 초~수 분** 소요
- 빠른 검색이 필요하면 `SEARCH_BODY = False` 로 제목만 검색
- 폴더 정렬: `Items.Sort("[ReceivedTime]", True)` 최신 순
- 진행 표시: 500개마다 `진행 N/Total (저장 X, 실패 Y)` 출력

---

## 주의사항

| 항목 | 내용 |
|---|---|
| Outlook 실행 필요 | `win32com.client.Dispatch("Outlook.Application")` — Outlook 데스크톱 앱 설치/로그인 상태여야 함 |
| 메일함 권한 | `team_name` 가 본인 Outlook 프로필에 등록돼 있어야 `Stores`에서 찾힘 |
| 본문 인코딩 | `mail.Body`는 plain text. HTMLBody가 필요하면 별도 처리 |
| `.msg` 포맷 | Outlook 기본 메일 저장 포맷. 다른 OS / 클라이언트에선 열기 제한적 |
| 매칭 0개 | 폴더만 만들고 종료 (저장 0개) — 키워드 / 폴더 / 메일함 명 재확인 |
| 첨부 포함 여부 | `.msg` 파일은 첨부까지 함께 저장됨 (별도 처리 불필요) |
| MailItem 외 항목 | `Class != 43` (회의·작업·연락처 등)은 자동 skip |

---

## 변경 이력

- **2026-04-30** (Jonghyun Park) — 초기 작성
