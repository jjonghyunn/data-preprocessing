# update_schedule.py

## 개요
캠페인 법인별 일정 파일을 자동으로 Auto 정제 파일에 붙여넣는 스크립트.

## 동작 순서
1. `1.고객 법인 일정 파일/` 폴더에서 최신 파일 자동 선택
2. 로컬 마커 파일과 비교 → 소스 파일 미변경 시 즉시 종료 (스킵)
3. 소스 파일 첫 번째 시트 **B3:J** 값 읽기
4. Auto 파일의 `고객법인일정파일` 시트 **B2:K999** 값·음영 클리어 후 **B2**부터 값 붙여넣기
5. 이전 소스 파일과 비교해 변경된 셀에 노란 음영 표시
6. win32com으로 Excel을 백그라운드 실행 → `CalculateFull()` → 재계산된 상태로 저장
7. 로컬 마커 파일에 처리한 소스 파일명 기록

## 최신 파일 선택 기준
파일명에서 아래 순서로 정렬 키를 추출하고, 가장 큰 튜플을 가진 파일을 최신으로 판단:

```python
(date, version, suffix)
```

| 키 | 정규식 | 예시 매칭 | 파싱 결과 |
|---|---|---|---|
| `date`    | `(?<!\d)\d{6}(?!\d)` | `_260325`  | `260325` |
| `version` | `_v(\d+\.\d+)`        | `_v0.441`  | `0.441`  |
| `suffix`  | `_(\d{1,5})$`         | `_2` (끝)  | `2`      |

### Pattern A — 기존 캠페인 (YYMMDD + 소수점 버전)

6자리 날짜와 소수점 버전 패턴. 정렬 키가 정상 작동.

```
_v0.44_260319            → (260319, 0.44,  0)
_v0.44_260325            → (260325, 0.44,  0)
_v0.44_260325_2          → (260325, 0.44,  2)
_v0.441_260325           → (260325, 0.441, 0)
_v0.45_260325            → (260325, 0.45,  0)  ← 최신
```

### Pattern B — 현재 캠페인 (YYYYMMDD + 정수 버전)

파일명에 8자리 날짜(YYYYMMDD)와 정수 버전(`_vN`)이 붙는 패턴.  
- 6자리 정규식이 8자리 날짜에 매칭 불가 → `date = 0`  
- 소수점 없는 `_vN`은 버전 정규식에 매칭 불가 → `version = 0.0`  
- 결과적으로 모든 파일의 키가 `(0, 0.0, 0)` → 정렬 키 무효

단, Windows의 `Path.glob()`이 알파벳 순으로 파일을 반환하고  
YYYYMMDD + `_vN` 패턴은 알파벳 순 = 시간 순이므로 결과적으로 올바른 파일이 선택됨.

예시:
```
[파일명 앞부분]···20260401.xlsx       → 해당일 초기 수신본
[파일명 앞부분]···20260407_v2.xlsx    → 수정본 (v1 없이 v2로 수신되기도 함)
[파일명 앞부분]···20260409.xlsx       → 해당일 초기 수신본
[파일명 앞부분]···20260409_v1.xlsx    → 해당일 1차 수정본
[파일명 앞부분]···20260409_v2.xlsx    → 해당일 2차 수정본  ← 최신
```

적용 규칙:
- 날짜만 있는 파일이 해당일의 초기본
- `_v1`, `_v2` 등 버전이 붙으면 해당 버전이 최신
- 더 최근 날짜가 항상 우선 (알파벳 순 보장)

### Pattern C — 날짜+시간만 있는 경우 (YYYYMMDD_HHMM, 버전 없음)

버전 없이 날짜와 시간만 붙는 패턴. 2026-04-15 최초 발생.

```
[파일명 앞부분]···20260415_1543.xlsx  → (20260415, 1543, 0.0, 0)
```

- 정렬 키: `(date=YYYYMMDD, time=HHMM, version=0.0, suffix=0)`
- `YYYYMMDD(8자리) > YYMMDD(6자리)`이므로 Pattern A/B보다 항상 최신으로 정렬됨
- 같은 날 여러 파일이 오면 시간(HHMM) 기준으로 최신 선택

## 값 변환 규칙
| 소스 셀 타입 | 변환 결과 |
|---|---|
| `datetime` | `date` 객체 (number_format: `YYYY-MM-DD`) |
| WEEKNUM 수식 결과 (정수) | `W01` 형식 문자열 |
| 나머지 | 그대로 |

## 전후 비교 음영 표시
- 매칭 기준: **C열 (Subs)**
- 비교 대상: **E열** (Participation), **F열** (Start at), **H열** (End at)
- 이전 파일 없으면 스킵
- 매 실행마다 기존 음영 초기화 후 재적용

## 파일 경로
| 구분 | 경로 |
|---|---|
| 소스 폴더 | `02. SCHEDULE/1.고객 법인 일정 파일/` |
| 업데이트 대상 | `02. SCHEDULE/*Auto*.xlsx` (자동 탐색) |
| 마커 파일 | `C:\Users\user_name\Documents\schedule_last_source.txt` (로컬, OneDrive 외부) |

## 실행 방법
```bash
python update_schedule.py
# 또는
run_schedule_update.bat
```

## 스케줄 작업
- 작업 이름: `md_schedule_update_v2`
- 실행 주기: 20분마다
- 시작: 10:00
- 기간: ~ 2026-05-15
- 조건: 로그온 중일 때만 실행 (`/it`)
- 배터리: 배터리 전원에서도 실행 (schtasks 등록 후 PowerShell 추가 설정 필요 → 아래 참고)

## 작업 스케줄러 등록

Python 스크립트를 작업 스케줄러에 직접 등록. bat/vbs 래퍼 불필요.

> ⚠️ `/tr` 경로에 공백이 있으면 schtasks가 경로를 잘라 오류 발생 (0x80070005).  
> python.exe 경로와 py 파일 경로를 각각 `\"...\"` 로 감싸야 공백이 포함된 경로도 처리 가능.

### CLI 등록 명령어

```bat
schtasks /create /tn md_mail_check_v2 ^
  /tr "\"C:\Python3xx\python.exe\" \"C:\Users\user_name\OneDrive - company_name\user_id\...\check_mail_attachment.py\"" ^
  /sc minute /mo 20 /st 09:55 /ed 2026/05/15 /it /f

schtasks /create /tn md_schedule_update_v2 ^
  /tr "\"C:\Python3xx\python.exe\" \"C:\Users\user_name\OneDrive - company_name\user_id\...\update_schedule.py\"" ^
  /sc minute /mo 20 /st 10:00 /ed 2026/05/15 /it /f
```

전체 경로가 포함된 명령어는 `create_schtasks_v2.txt` 참고.

| 옵션 | 설명 |
|---|---|
| `/sc minute /mo 20` | 20분마다 실행 |
| `/st 09:55 / 10:00` | 각 스크립트 시작 시각 |
| `/it` | 로그온 중일 때만 실행 |
| `/f` | 동일 이름 작업 덮어쓰기 |

### 배터리 모드 허용 (등록 후 PowerShell에서 추가 실행)

`schtasks`는 배터리 조건을 직접 지정할 수 없으므로, 등록 후 아래 PowerShell 명령어를 별도로 실행:

```powershell
$names = "md_mail_check_v2", "md_schedule_update_v2"
foreach ($n in $names) {
    $t = Get-ScheduledTask -TaskName $n
    $t.Settings.DisallowStartIfOnBatteries = $false
    $t.Settings.StopIfGoingOnBatteries = $false
    Set-ScheduledTask -InputObject $t
}
```

### Python 경로 확인

```bat
where python
:: 예) C:\Python314\python.exe
```

### GUI 등록

1. `taskschd.msc` 실행
2. **작업 만들기** → 일반 탭: 이름 입력, "사용자가 로그온할 때만 실행" 선택
3. **트리거** 탭 → 새로 만들기 → 반복 주기 설정
4. **동작** 탭 → 새로 만들기:
   - 프로그램/스크립트: `C:\Python3xx\python.exe`
   - 인수 추가: `"C:\Users\user_name\OneDrive - company_name\...\update_schedule.py"`
5. **조건** 탭 → 전원 섹션 → **"AC 전원이 연결된 경우에만 작업 시작" 체크 해제**

## check_mail_attachment.py 개요

`run_mail_check.bat` / `run_mail_check_to_my_folder.bat`이 호출하는 메일 수신 스크립트.

- Outlook 수신함에서 미처리 첨부파일을 탐색
- 지정된 로컬 폴더에 자동 저장
- `update_schedule.py`와 함께 작업 스케줄러에 등록해 주기적으로 실행
- 새 소스 파일이 도착하면 다음 `update_schedule.py` 실행 시 자동 반영됨

### 재처리 방지 (EntryID 마커)

처리 완료한 메일의 `EntryID`를 마커 파일에 기록해, 다음 실행 시 동일 메일을 건너뜀.

```
C:\Users\user_name\Documents\sw_mail_processed_ids.txt
```

- 파일이 없으면 자동 생성
- 새 첨부파일이 저장되거나 이미 처리된 것으로 간주된 경우에만 EntryID 기록

### 중복 파일명 처리

동일한 파일명의 첨부파일이 재전송되면 수신일(`_yymmdd`)을 붙여 별도 저장.

```
원본 파일명: [앞부분]···20260409_v2.xlsx  (이미 저장됨)
신규 수신 시: [앞부분]···20260409_v2_260414.xlsx  (수신일 260414 = 4월 14일)
```

날짜 붙인 파일도 이미 존재하면 저장 없이 스킵.

### MAX_PATH 우회

저장 경로가 Windows 260자 제한을 초과하면 `att.SaveAsFile()` 오류 발생.  
임시 파일에 먼저 저장 후 `shutil.move()`로 이동하는 방식으로 우회.

> 레지스트리 설정(`LongPathsEnabled = 1`)도 병행 적용 필요 → [`enable_long_path.md`](enable_long_path.md) 참고
