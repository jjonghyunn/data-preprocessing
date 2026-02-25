import csv
import os
import re
from datetime import datetime

# ===============================
# 파일 경로 설정
# ===============================
base_dir = r'C:\Users\CNXK\Downloads'
csv_filename = '26_nyny_qry_cutoff_20th_260122_v2.csv'
input_path = os.path.join(base_dir, csv_filename)

base_name = os.path.splitext(csv_filename)[0]
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

separated_path = os.path.join(
    base_dir, f'separated_{base_name}_{timestamp}.csv'
)
report_path = os.path.join(
    base_dir, f'report_format_{base_name}_{timestamp}.csv'
)

# ===============================
# 사이트코드 목록
# ===============================
valid_site_codes = set("""
de
es
br
mx
tr
us
africa_en
za
kz_ru
kz_kz
mn
hk
al
ba
hr
mk
rs
si
hu
it
pl
bg
ro
ua
jp
co
ar
cl
latin_en
latin
pe
iq_ar
ku
levant
levant_ar
pk
sa
sa_en
ca
ca_fr
id
ph
sg
my
th
uk_epp
""".split())

# ===============================
# us 채널 매핑
# ===============================
us_mapping = {
    "US Channel":"Global Channel Mapping ",
    "Affiliate":"Affiliate Marketing",
    "Display":"Display",
    "Display Retargeting":"Display",
    "Other External Campaign":"Paid Others",
    "Other Paid Ecomm":"Paid Others",
    "Paid Search":"Paid Search",
    "Paid Search - eComm":"Paid Search",
    "PLA":"Pmax",
    "Social (Paid)":"Social Media Campaigns",
    "Vanity":"Paid Others",
    "Direct":"Direct",
    "Email - CRM":"Email",
    "Email - eComm":"Email",
    "Email - Upsell it":"Email",
    "Email (Retired)":"Email",
    "EPP":"EPP - US",
    "Natural Search":"Natural Search",
    "Other":"Other",
    "None":"Other",
    "Push Notifications":"Push",
    "Referring Domains":"Other",
    "Session Refresh":"Session Refresh",
    "Social (Free and Owned)":"Owned Social",
    "Social (Retired)":"Social Network Referrals",
    "Other External CampaignSegments":"Mobile Application",
    "Other External CampaignUS_Smartthings":"Mobile Application - Smartthings",
    "Other External CampaignUS_Samsung Members":"Mobile Application - Samsung Members",
    "SMS":"SMS",
    "Gen AI Search":"Gen AI (Organic)"
}

# ===============================
# Paid / Non-Paid
# ===============================
global_paid_mapping = {
    "Paid Search":"Paid",
    "Social Media Campaigns":"Paid",
    "Affiliate Marketing":"Paid",
    "Display":"Paid",
    "Other Campaigns":"Paid",
    "QR code (Paid)":"Paid",
    "Pmax":"Paid",
    "Demand Gen":"Paid",
    "Paid Others":"Paid",
    "Video":"Paid",
    "Gen AI (Paid)":"Paid",
    "Session Refresh":"Non-Paid",
    "Email":"Non-Paid",
    "Direct":"Non-Paid",
    "Natural Search":"Non-Paid",
    "Mobile Application":"Non-Paid",
    "Push":"Non-Paid",
    "Social Network Referrals":"Non-Paid",
    "Other":"Non-Paid",
    "SMS":"Non-Paid",
    "None":"Non-Paid",
    "Owned Social":"Non-Paid",
    "QR code (Owned)":"Non-Paid",
    "Samsung Web":"Non-Paid",
    "Gen AI (Organic)":"Non-Paid",
    "Owned Others":"Non-Paid"
}

# ===============================
# REPORT NO 매핑
# ===============================
report_no_mapping = {
    "1_1": "1_1~2. S.com Traffic by Division",
    "2_1": "2_1~4. Basic Traffic",
    "3_1": "3_1. Traffic by Channel (Internal)",
    "3_2": "3_2. Traffic by Channel (External)",
    "3_3": "3_3. Home KV & GNB to Campaign Page",
    "4_1": "4_1. Order Conversion with Login/Non_Login",
    "4_2": "4_2. Order Conversion with Login/Non_Login (Visit)",
    "5_1": "5_1. S.com Order Conversion",
    "6_1": "6_1. S.com Cross Sell Order (Multi Purchase)",
    "6_2": "6_2. S.com Cross Sell Order (Total)",
    "6_3": "6_3. Campaign Page Cross Sell Order",
    "7_1": "7_1~2. Order Conversion/Traffic by Channel"
}

# ===============================
# 유틸
# ===============================
def split_by_number_pattern(parts):
    for i in (2, 3):
        if i + 1 < len(parts) and parts[i].isdigit() and parts[i+1].isdigit():
            return '_'.join(parts[:i]), f"{parts[i]}_{parts[i+1]}", parts[i+2:]
    return parts[0], f"{parts[1]}_{parts[2]}", parts[3:]

def find_report_key(values):
    for v in values:
        if isinstance(v, str) and re.fullmatch(r"\d+_\d+", v):
            return v
    return ''

def to_number(val):
    try:
        return float(val)
    except:
        return ''

# ===============================
# separated.csv 생성
# ===============================
with open(input_path, newline='', encoding='utf-8') as f_in, \
     open(separated_path, 'w', newline='', encoding='utf-8') as f_out:

    reader = csv.reader(f_in)
    writer = csv.writer(f_out)

    header = next(reader)
    writer.writerow(header + [f"J{i}" for i in range(1, 12)])

    for row in reader:
        if not row:
            continue

        site_code = row[2].strip()
        if site_code not in valid_site_codes:
            continue

        a_val = row[0]
        b_val = row[1] if len(row) > 1 else ''

        parts = a_val.split('_')
        first, second, remaining = split_by_number_pattern(parts)

        result = [first, second]
        processed = []
        i = 0

        while i < len(remaining):
            if remaining[i].isdigit() and remaining[i].startswith('202'):
                if i + 2 < len(remaining) and remaining[i+2].lower() == 'prior':
                    processed.append(f"{remaining[i]}_{remaining[i+1]}_{remaining[i+2]}")
                    i += 3
                elif i + 1 < len(remaining):
                    processed.append(f"{remaining[i]}_{remaining[i+1]}")
                    i += 2
                else:
                    processed.append(remaining[i])
                    i += 1
            else:
                processed.append(remaining[i])
                i += 1

        all_parts = result + processed
        j1_to_j7 = all_parts[:7]
        while len(j1_to_j7) < 7:
            j1_to_j7.append('')

        j8 = j9 = j10 = ''

        if b_val.strip():
            mapped = us_mapping.get(b_val.strip(), b_val.strip()) if site_code == 'us' else b_val.strip()
            if mapped.lower() == 'none':
                mapped = 'Other'
            j9 = mapped
            j8 = global_paid_mapping.get(j9, '')
        else:
            j10 = '_'.join([v for v in j1_to_j7 if v]) + '_'

        report_key = find_report_key(j1_to_j7)
        j11 = report_no_mapping.get(report_key, '')

        # value / valueorigin 숫자 처리
        row[4] = to_number(row[4])
        row[5] = to_number(row[5])

        writer.writerow(row + j1_to_j7 + [j8, j9, j10, j11])

# ===============================
# report_format.csv 생성
# ===============================
with open(separated_path, newline='', encoding='utf-8') as f_in, \
     open(report_path, 'w', newline='', encoding='utf-8') as f_out:

    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)

    writer.writerow(list("ABCDEFGHIJKLMNOPQRSTU"))

    for r in reader:
        writer.writerow([
            "", "", "",
            r["site_code"].upper(),   # D
            r["J11"],                # E
            r["J3"], r["J4"], r["J5"], r["J6"], r["J7"], r["J8"], r["J9"],  # F~L
            r["value"],              # M
            r[reader.fieldnames[0]], # N (원본 A)
            r["valueorigin"],        # O
            "", "", "",
            r["start_date"],         # S
            r["end_date"],           # T
            r["J10"],                # U
        ])

print("✅ CSV 2개 생성 완료")
print(separated_path)
print(report_path)
