import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))

# ── 서브폴더 자동 결정 ─────────────────────────────────────────────────────────
def get_subfolder(name: str) -> str:
    """파일명 prefix/suffix 로 서브폴더 자동 결정"""
    n = name.strip()
    if n.startswith("last_us_"):
        return "last_us_main"
    if n.startswith("last_"):
        return "last_main"
    if n.startswith("us_") and n.endswith("_prior"):
        return "us_main_prior"
    if n.startswith("us_"):
        return "us_main"
    if n.endswith("_prior"):
        return "main_prior"
    return "main"

# ── 파일명 목록 (확장자 .json 제외) ────────────────────────────────────────────
# 각 이름은 자동으로 올바른 서브폴더에 생성됩니다.
names = """
1_1_scom_da_traffic_app
1_1_scom_da_traffic_web
1_1_scom_mx_traffic_app
1_1_scom_mx_traffic_web
1_1_scom_vd_traffic_app
1_1_scom_vd_traffic_web
2_1_basic_traffic_cmp
2_1_basic_traffic_scom
2_1_basic_traffic_time_cmp
2_1_basic_traffic_time_scom
3_1_channel_internal
3_2_channel_external_cmp
3_2_channel_external_scom
3_3_homepage_kv_gnb_to_cmp
4_1_order_cvr_loginout
4_2_order_cvr_visit_visitor
5_1_campaign_order_cvr
5_1_scom_order_cvr
6_1_multi_order_cross_sell
6_2_total_order_cross_sell
6_3_cmp_order_cross_sell
7_1_order_by_channel_cmp
7_1_order_by_channel_scom
8_1_login_cta
bestselling
multi_purchase
nextpage

1_1_scom_da_traffic_app_prior
1_1_scom_da_traffic_web_prior
1_1_scom_mx_traffic_app_prior
1_1_scom_mx_traffic_web_prior
1_1_scom_vd_traffic_app_prior
1_1_scom_vd_traffic_web_prior
2_1_basic_traffic_scom_prior
2_1_basic_traffic_time_scom_prior
3_2_channel_external_scom_prior
6_1_multi_order_cross_sell_prior
6_2_total_order_cross_sell_prior
7_1_order_by_channel_scom_prior
multi_purchase_prior

us_1_1_scom_da_traffic_web
us_1_1_scom_mx_traffic_web
us_1_1_scom_vd_traffic_web
us_2_1_basic_traffic_cmp
us_2_1_basic_traffic_scom
us_2_1_basic_traffic_time_cmp
us_2_1_basic_traffic_time_scom
us_3_1_channel_internal_web
us_3_2_channel_external_cmp
us_3_2_channel_external_scom
us_3_3_homepage_kv_gnb_to_cmp
us_4_1_order_cvr_loginout
us_4_2_order_cvr_visit_visitor
us_5_1_campaign_order_cvr_total
us_6_1_multi_order_cross_sell
us_6_2_total_order_cross_sell
us_6_3_cmp_order_cross_sell
us_7_1_order_by_channel_cmp
us_7_1_order_by_channel_scom
us_8_1_login_cta
us_bestselling
us_multi_purchase
us_nextpage

us_1_1_scom_da_traffic_web_prior
us_1_1_scom_mx_traffic_web_prior
us_1_1_scom_vd_traffic_web_prior
us_2_1_basic_traffic_scom_prior
us_2_1_basic_traffic_time_scom_prior
us_3_2_channel_external_scom_prior
us_6_1_multi_order_cross_sell_prior
us_6_2_total_order_cross_sell_prior
us_7_1_order_by_channel_scom_prior
us_multi_purchase_prior

last_1_1_scom_da_traffic_app
last_1_1_scom_da_traffic_web
last_1_1_scom_mx_traffic_app
last_1_1_scom_mx_traffic_web
last_1_1_scom_vd_traffic_app
last_1_1_scom_vd_traffic_web
last_2_1_basic_traffic_cmp
last_2_1_basic_traffic_scom
last_2_1_basic_traffic_time
last_3_1_channel_internal
last_3_2_channel_traffic_external
last_3_3_homepage_kv_gnb_to_cmp
last_4_1_order_cvr_loginout
last_4_1_scom_order_cvr_loginout
last_5_1_scom_campaign_order_cvr
last_6_1_multi_order_cross_sell
last_6_2_total_order_cross_sell
last_6_3_cmp_order_cross_sell
last_7_1_order_by_channel_cmp
last_bestselling

last_us_1_1_scom_da_traffic_web
last_us_1_1_scom_mx_traffic_web
last_us_1_1_scom_vd_traffic_web
last_us_2_1_basic_traffic_cmp
last_us_2_1_basic_traffic_scom
last_us_2_1_basic_traffic_time_cmp
last_us_2_1_basic_traffic_time_scom
last_us_3_1_channel_internal_web
last_us_3_2_channel_external_cmp
last_us_3_2_channel_external_scom
last_us_3_3_homepage_kv_gnb_to_cmp
last_us_4_1_order_cvr_loginout
last_us_4_2_order_cvr_visit_visitor
last_us_5_1_campaign_order_cvr_total
last_us_6_1_multi_order_cross_sell
last_us_6_2_total_order_cross_sell
last_us_6_3_cmp_order_cross_sell
last_us_7_1_order_by_channel_cmp
last_us_7_1_order_by_channel_scom
last_us_bestselling
""".strip().splitlines()

cnt_exist = 0
cnt_created = 0

for name in names:
    name = name.strip()
    if not name:
        continue
    subdir   = get_subfolder(name)
    folder   = os.path.join(script_dir, subdir)
    filepath = os.path.join(folder, f"{name}.json")

    if os.path.exists(filepath):
        print(f"✔ 있음 (미생성): {subdir}/{name}.json")
        cnt_exist += 1
    else:
        open(filepath, "w", encoding="utf-8").close()
        print(f"✚ 없음 → 생성됨: {subdir}/{name}.json")
        cnt_created += 1

total = cnt_exist + cnt_created
print(f"
{chr(9472)*40}")
print(f"입력한 파일명 : {len([n for n in names if n.strip()])}개")
print(f"체크한 파일  : {total}개")
print(f"  ✔ 있음    : {cnt_exist}개")
print(f"  ✚ 생성됨  : {cnt_created}개")
print(f"  합계      : {total}개")

input_set = {n.strip() for n in names if n.strip()}
extra = []
SUBDIRS = ["main", "main_prior", "us_main", "us_main_prior", "last_main", "last_us_main"]
for subdir in SUBDIRS:
    folder = os.path.join(script_dir, subdir)
    if not os.path.isdir(folder):
        continue
    for f in sorted(os.listdir(folder)):
        if f.endswith(".json") and f[:-5] not in input_set:
            extra.append(f"{subdir}/{f}")

print(f"
{chr(9472)*40}")
print(f"입력 목록 외 폴더에 있는 json 파일: {len(extra)}개")
for i, fname in enumerate(extra, 1):
    print(f"  {i:>3}. {fname}")
