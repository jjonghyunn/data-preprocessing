"""
check_mail_attachment.py

team_name 받은편함에서 CAMPAIGN NAME 법인별 일정 첨부파일을 감지해 저장.
이미 같은 파일명이 있으면 스킵.
"""

import win32com.client
from pathlib import Path

SAVE_FOLDER = Path(
    r"C:\Users\user_name\OneDrive - company_name"
    r"\Project_team_name - 1 company_name - 02 part_name"
    r"\part_name\2026\# CAMPAIGN_PROJECTS\02. CAMPAIGN NAME"
    r"\02. SCHEDULE\1.고객 법인 일정 파일"
)
STORE_NAME   = "team_name"
SUBJECT_KEYS = ["campaign name", "법인별"]  # 모두 포함된 메일만

# ── Outlook 연결 ──────────────────────────────────────────────
outlook = win32com.client.Dispatch("Outlook.Application")
ns      = outlook.GetNamespace("MAPI")

target_store = None
for store in ns.Stores:
    if STORE_NAME.lower() in store.DisplayName.lower():
        target_store = store
        break

if target_store is None:
    raise RuntimeError(f"메일함을 찾을 수 없습니다: {STORE_NAME}")

inbox = target_store.GetDefaultFolder(6)  # 6 = 받은편함
print(f"[메일함] {target_store.DisplayName} / 받은편함 ({inbox.Items.Count}개)")

# ── 메일 순회 ────────────────────────────────────────────────
saved = 0
skipped = 0

for mail in inbox.Items:
    try:
        subject = mail.Subject.lower()
    except Exception:
        continue

    if not all(k in subject for k in SUBJECT_KEYS):
        continue

    for att in mail.Attachments:
        name = att.FileName
        if not name.lower().endswith(".xlsx"):
            continue

        dest = SAVE_FOLDER / name
        if dest.exists():
            print(f"[스킵] 이미 존재: {name}")
            skipped += 1
        else:
            att.SaveAsFile(str(dest))
            print(f"[저장] {name}")
            saved += 1

print(f"\n완료 - 저장 {saved}개 / 스킵 {skipped}개")
