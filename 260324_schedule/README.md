# update_schedule.py

## 개요
캠페인 법인별 일정 파일을 자동으로 Auto 정제 파일에 붙여넣는 스크립트.

## 동작 순서
1. `1.고객 법인 일정 파일/` 폴더에서 최신 파일 자동 선택
2. 로컬 마커 파일과 비교 → 소스 파일명·수정시각(mtime) 모두 동일하면 즉시 종료 (스킵)
3. 소스 파일 첫 번째 시트 **B3:J** 값 읽기
4. Auto 파일의 `고객법인일정파일` 시트 **B2:K999** 값·음영 클리어 후 **B2**부터 값 붙여넣기
5. 이전 소스 파일과 비교해 변경된 셀에 노란 음영 표시
6. win32com으로 Excel을 백그라운드 실행 → `CalculateFull()` → 재계산된 상태로 저장
7. 로컬 마커 파일에 처리한 소스 파일명 기록

## 최신 파일 선택 기준
파일명에서 아래 정렬 키를 추출하고, 가장 큰 튜플을 가진 파일을 최신으로 판단:

```python
(doc_date, hhmm, ver_float, ver_int, mail_date)
```

### SW형 — 8자리 날짜(YYYYMMDD) 포함

| 패턴 | 예시 | 정렬 키 |
|---|---|---|
| `YYYYMMDD_HHMM[_YYMMDD]` | `20260415_1543_260417` | `(20260415, 1543, 0, 0, 260417)` |
| `YYYYMMDD_vN[_YYMMDD]`   | `20260421_v2`          | `(20260421, 0, 0, 2, 0)`        |
| `YYYYMMDD_YYMMDD`        | `20260401_260406`      | `(20260401, 0, 0, 0, 260406)`   |
| `YYYYMMDD`               | `20260421`             | `(20260421, 0, 0, 0, 0)`        |

전체 예시 (오름차순 정렬):
```
···20260401_260406.xlsx       → (20260401, 0, 0, 0, 260406)
···20260407_v2_260408.xlsx    → (20260407, 0, 0, 2, 260408)
···20260409_260409.xlsx       → (20260409, 0, 0, 0, 260409)
···20260409_v1_260409.xlsx    → (20260409, 0, 0, 1, 260409)
···20260409_v2_260409.xlsx    → (20260409, 0, 0, 2, 260409)
···20260409_v2_260414.xlsx    → (20260409, 0, 0, 2, 260414)
···20260415_1543.xlsx         → (20260415, 1543, 0, 0, 0)
···20260415_1543_260417.xlsx  → (20260415, 1543, 0, 0, 260417)
···20260420_0906.xlsx         → (20260420, 906, 0, 0, 0)
···20260421.xlsx              → (20260421, 0, 0, 0, 0)
···20260421_v2.xlsx           → (20260421, 0, 0, 2, 0)  ← 최신
```

### MD형 — 6자리 날짜(YYMMDD) + 소수점 버전

| 키 | 정규식 | 예시 | 파싱 결과 |
|---|---|---|---|
| `date6`   | `(?<!\d)\d{6}(?!\d)` | `_260325`  | `260325` |
| `version` | `_v(\d+\.\d+)`        | `_v0.441`  | `0.441`  |
| `suffix`  | `_(\d{1,5})$`         | `_2` (끝)  | `2`      |

```
_v0.44_260319   → (260319, 0, 0.44, 0, 0)
_v0.48_260420   → (260420, 0, 0.48, 0, 0)
_v0.49_260420   → (260420, 0, 0.49, 0, 0)  ← 최신
```

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
| 마커 파일 | `BASE/schedule_last_source.txt` — `파일명\|mtime` 형식으로 저장 (Auto 파일과 같은 폴더에 두어 프로젝트별 독립 관리. 다른 캠페인으로 fork 시 BASE만 교체하면 마커도 따라감) |

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

> 💡 **창 없이 실행하려면 `pythonw.exe` 사용**  
> `python.exe`는 콘솔 앱이라 실행 시 cmd 창이 팝업됨.  
> `pythonw.exe`(같은 경로에 있음)를 대신 쓰면 창이 전혀 뜨지 않음.  
> 단, stdout/stderr 출력이 버려지므로 로그가 필요하면 스크립트 내에서 파일로 기록해야 함.

> ⚠️ `/tr` 경로에 공백이 있으면 schtasks가 경로를 잘라 오류 발생 (0x80070005).  
> python.exe 경로와 py 파일 경로를 각각 `\"...\"` 로 감싸야 공백이 포함된 경로도 처리 가능.

### CLI 등록 명령어

```bat
schtasks /create /tn md_mail_check_v2 ^
  /tr "\"C:\Python3xx\pythonw.exe\" \"C:\Users\user_name\OneDrive - company_name\user_id\...\check_mail_attachment.py\"" ^
  /sc minute /mo 20 /st 09:55 /ed 2026/06/30 /it /f

schtasks /create /tn md_schedule_update_v2 ^
  /tr "\"C:\Python3xx\pythonw.exe\" \"C:\Users\user_name\OneDrive - company_name\user_id\...\update_schedule.py\"" ^
  /sc minute /mo 20 /st 10:00 /ed 2026/06/30 /it /f
```

전체 경로가 포함된 명령어는 `create_schtasks_v2.txt` 참고.

| 옵션 | 설명 |
|---|---|
| `/sc minute /mo 20` | 20분마다 실행 |
| `/st 09:55 / 10:00` | 각 스크립트 시작 시각 |
| `/it` | 로그온 중일 때만 실행 |
| `/f` | 동일 이름 작업 덮어쓰기 |

### 배터리 모드 허용 (등록 후 추가 실행)

`schtasks`는 배터리 조건을 직접 지정할 수 없으므로, 등록 후 아래 명령어를 별도로 실행.

**[권장] PowerShell 창에서 직접 실행** — 래퍼 없이 한 줄, 빠름:

```powershell
$names = 'md_mail_check_v2','md_schedule_update_v2'; foreach ($n in $names) { $t = Get-ScheduledTask -TaskName $n; $t.Settings.DisallowStartIfOnBatteries = $false; $t.Settings.StopIfGoingOnBatteries = $false; Set-ScheduledTask -InputObject $t }
```

또는 가독성 버전:

```powershell
$names = 'md_mail_check_v2', 'md_schedule_update_v2'
foreach ($n in $names) {
    $t = Get-ScheduledTask -TaskName $n
    $t.Settings.DisallowStartIfOnBatteries = $false
    $t.Settings.StopIfGoingOnBatteries = $false
    Set-ScheduledTask -InputObject $t
}
```

**[cmd/bat에서 실행할 때만] `powershell -Command` 래퍼 사용**:

```bat
powershell -Command "$names = 'md_mail_check_v2','md_schedule_update_v2'; foreach ($n in $names) { $t = Get-ScheduledTask -TaskName $n; $t.Settings.DisallowStartIfOnBatteries = $false; $t.Settings.StopIfGoingOnBatteries = $false; Set-ScheduledTask -InputObject $t }"
```

⚠ **PowerShell 창에서 래퍼 형태를 쓰지 말 것** — 바깥 PS가 `$names`, `$n`, `$t`를 자기 변수로 먼저 치환(빈 값)해버려 `foreach 뒤에 변수 이름이 없습니다` 오류가 발생합니다.

### Python 경로 확인

```bat
where pythonw
:: 예) C:\Python314\pythonw.exe
```

### GUI 등록

1. `taskschd.msc` 실행
2. **작업 만들기** → 일반 탭: 이름 입력, "사용자가 로그온할 때만 실행" 선택
3. **트리거** 탭 → 새로 만들기 → 반복 주기 설정
4. **동작** 탭 → 새로 만들기:
   - 프로그램/스크립트: `C:\Python3xx\pythonw.exe` (창 없이 실행; 일반 python.exe 쓰면 cmd 창 팝업됨)
   - 인수 추가: `"C:\Users\user_name\OneDrive - company_name\...\update_schedule.py"`
5. **조건** 탭 → 전원 섹션 → **"AC 전원이 연결된 경우에만 작업 시작" 체크 해제**

## check_mail_attachment.py

Outlook 수신함을 폴링해 일정 파일 첨부를 자동으로 로컬에 저장하는 스크립트.  
`update_schedule.py`와 쌍으로 작업 스케줄러에 등록해 주기적으로 실행합니다.  
새 소스 파일이 도착하면 다음 `update_schedule.py` 실행 시 자동 반영됩니다.

### 동작 순서

1. `win32com.client`로 Outlook 수신함 접근
2. 제목 필터 조건에 맞는 메일만 선별 (스크립트 상단 `SUBJECT_KEYWORDS` 참고)
3. 처리 이력(`sw_mail_processed_ids.txt`)에 없는 메일만 처리
4. `.xlsx` 첨부파일을 지정 폴더에 저장
5. 처리한 메일의 EntryID를 이력 파일에 추가

### 실행 방법

```bash
python check_mail_attachment.py
```

작업 스케줄러 등록 방법은 위의 **작업 스케줄러 등록** 섹션 참고 (`md_mail_check_v2` 작업).

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
