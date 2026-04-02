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
파일명에서 아래 순서로 정렬해 가장 큰 값을 최신으로 판단:
1. 날짜 `YYMMDD` (6자리)
2. 버전 `_vX.XX`
3. 끝 번호 `_2` 등 (1~5자리)

예시 우선순위:
```
_v0.44_260319  <  _v0.44_260325  <  _v0.44_260325_2  <  _v0.441_260325  <  _v0.45_260325
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
| 마커 파일 | `C:\Users\user_name\Documents\schedule_last_source.txt` (로컬, OneDrive 외부) |

## 실행 방법
```bash
python update_schedule.py
# 또는
run_md_schedule_update.bat
```

## 스케줄 작업
- 작업 이름: `md_schedule_update_v2`
- 실행 주기: 20분마다
- 시작: 10:00
- 기간: ~ 2026-05-15
- 조건: 로그온 중일 때만 실행 (`/it`)

## 작업 스케줄러에 vbs로 등록하기

bat 파일을 작업 스케줄러에 직접 등록하면 실행 시 CMD 창이 잠깐 뜨는 문제가 있음.  
vbs 래퍼를 통해 창 없이 백그라운드 실행 가능.

> ⚠️ **경로에 공백이 있으면 작업 스케줄러 실행 시 오류가 발생할 수 있음.**  
> OneDrive, 바탕화면 등 경로에 공백이 포함된 폴더는 피하고,  
> `C:\Users\user_name\Documents\` (내 문서) 또는 `C:\scripts\` 같은 공백 없는 경로에 bat/vbs 파일을 보관할 것.

### 1. vbs 파일 작성 (`Documents\run_md_schedule_update.vbs`)

```vbscript
CreateObject("WScript.Shell").Run """C:\Users\user_name\Documents\run_md_schedule_update.bat""", 0, False
```

- 두 번째 인수 `0` = 창 숨김
- 세 번째 인수 `False` = 완료 대기 안 함 (비동기)

### 2. 작업 스케줄러 등록 (GUI)

1. `taskschd.msc` 실행
2. **작업 만들기** (일반 탭: 이름 입력, "사용자가 로그온할 때만 실행" 선택)
3. **트리거** 탭 → 새로 만들기 → 반복 주기 설정 (예: 20분마다)
4. **동작** 탭 → 새로 만들기:
   - 프로그램/스크립트: `wscript.exe`
   - 인수 추가: `"C:\Users\user_name\Documents\run_md_schedule_update.vbs"`

### 3. 작업 스케줄러 등록 (CLI)

```bat
schtasks /create /tn "md_schedule_update_v2" ^
  /tr "wscript.exe \"C:\Users\user_name\Documents\run_md_schedule_update.vbs\"" ^
  /sc minute /mo 20 /st 10:00 /it /f
```

| 옵션 | 설명 |
|---|---|
| `/sc minute /mo 20` | 20분마다 실행 |
| `/st 10:00` | 10:00부터 시작 |
| `/it` | 로그온 중일 때만 실행 |
| `/f` | 동일 이름 작업 덮어쓰기 |

### 4. vbs 파일 목록

| vbs 파일 | 연결된 bat | 용도 |
|---|---|---|
| `run_md_schedule_update.vbs` | `run_md_schedule_update.bat` | 스케줄 업데이트 |
| `run_md_mail_check.vbs` | `run_md_mail_check.bat` | 메일 첨부 확인 |
| `run_md_mail_check_to_my_folder.vbs` | `run_md_mail_check_to_my_folder.bat` | 메일 → 내 폴더 저장 |
