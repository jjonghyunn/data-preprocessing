"""
mail_search_to_msg.py
2026-04-30  Jonghyun Park w/ Claude

team_name 메일함에서 키워드 매칭되는 메일을 .msg 파일로 다운로드.

검색 대상:
  - 제목(Subject) 또는 본문(Body) 부분일치 (대소문자 무관)
  - KEYWORDS 리스트 — 어느 하나라도 포함되면 매칭 (OR)

저장 위치:
  C:\\Users\\<user>\\Downloads\\mail_search_<YYMMDD>\\

사용:
  스크립트 상단 ── 설정 ── 섹션에서 KEYWORDS 등을 바꾼 뒤 실행.
    python mail_search_to_msg.py
"""

import re
import win32com.client
from pathlib import Path
from datetime import datetime

# ── 설정 ────────────────────────────────────────────────────────
# 검색할 키워드 — 제목 또는 본문에 어느 하나라도 포함되면 매칭 (OR, 대소문자 무관)
KEYWORDS = [
    "personal shopper kv",
    # "법인별",
    # "추가 키워드 ...",
]

# Outlook 메일함 이름 (DisplayName 부분 일치)
STORE_NAME = "team_name"

# 검색 대상 폴더 — None 이면 받은편함(Inbox)
FOLDER_NAME = None

# 하위 폴더까지 재귀 검색?
RECURSE_SUBFOLDERS = False

# 본문(Body)도 검색? False면 제목(Subject)만 검색 — 빠름
SEARCH_BODY = True

# ── 자동 결정 ───────────────────────────────────────────────────
TODAY = datetime.now().strftime("%y%m%d")
SAVE_DIR = Path.home() / "Downloads" / f"mail_search_{TODAY}"

# Outlook 상수
OL_FOLDER_INBOX = 6   # GetDefaultFolder
OL_CLASS_MAIL   = 43  # MailItem
OL_SAVE_AS_MSG  = 3   # SaveAs Type


def safe_filename(name: str) -> str:
    """Windows 파일명 허용 문자만 남기고 길이 제한."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name or "")
    cleaned = cleaned.strip(". ")
    return cleaned[:150] or "no_subject"


def matches_keywords(subject: str, body: str) -> bool:
    text = subject.lower()
    if SEARCH_BODY:
        text += "\n" + body.lower()
    return any(k.lower() in text for k in KEYWORDS)


def iter_folders(root, recurse: bool):
    """폴더 + (옵션) 하위 폴더 재귀 yield."""
    yield root
    if recurse:
        for sub in root.Folders:
            yield from iter_folders(sub, True)


def find_store(ns, store_name: str):
    for store in ns.Stores:
        if store_name.lower() in store.DisplayName.lower():
            return store
    return None


def find_folder(store, folder_name: str | None):
    """folder_name이 None이면 받은편함, 아니면 루트 하위에서 이름 일치 폴더."""
    if not folder_name:
        return store.GetDefaultFolder(OL_FOLDER_INBOX)
    root = store.GetRootFolder()
    for f in root.Folders:
        if f.Name == folder_name:
            return f
    raise RuntimeError(f"폴더를 찾을 수 없습니다: {folder_name}")


def main():
    print(f"[키워드] {KEYWORDS}  (대소문자 무관, OR 매칭)")
    print(f"[검색 범위] 제목{' + 본문' if SEARCH_BODY else ' (본문 미검색)'}")
    print(f"[메일함] {STORE_NAME}")
    print(f"[저장]   {SAVE_DIR}")
    print()

    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")

    target_store = find_store(ns, STORE_NAME)
    if target_store is None:
        raise RuntimeError(f"메일함을 찾을 수 없습니다: {STORE_NAME}")

    target_folder = find_folder(target_store, FOLDER_NAME)
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    saved = 0
    failed = 0
    seen_names = set()

    for folder in iter_folders(target_folder, RECURSE_SUBFOLDERS):
        items = folder.Items
        try:
            items.Sort("[ReceivedTime]", True)  # 최신 순
        except Exception:
            pass

        total = items.Count
        print(f"▶ 폴더 '{folder.Name}' — {total}개 검색 중...")

        for idx, mail in enumerate(items, 1):
            if idx % 500 == 0:
                print(f"    진행 {idx}/{total} (저장 {saved}, 실패 {failed})")
            try:
                if mail.Class != OL_CLASS_MAIL:
                    continue
                subject = mail.Subject or ""
                body = mail.Body if SEARCH_BODY else ""
            except Exception:
                continue

            if not matches_keywords(subject, body):
                continue

            # 파일명: <YYMMDD_HHMM>_<safe subject>.msg
            try:
                received = mail.ReceivedTime
                date_prefix = received.strftime("%y%m%d_%H%M")
            except Exception:
                date_prefix = "unknown"

            base = f"{date_prefix}_{safe_filename(subject)}"
            name = f"{base}.msg"
            counter = 1
            while name.lower() in seen_names or (SAVE_DIR / name).exists():
                counter += 1
                name = f"{base} ({counter}).msg"
            seen_names.add(name.lower())

            dest = SAVE_DIR / name
            try:
                mail.SaveAs(str(dest), OL_SAVE_AS_MSG)
                print(f"    [저장] {name}")
                saved += 1
            except Exception as e:
                print(f"    [실패] {subject[:50]} → {e}")
                failed += 1

    print()
    print(f"완료 — 저장 {saved}개 / 실패 {failed}개")
    print(f"위치: {SAVE_DIR}")


if __name__ == "__main__":
    main()
