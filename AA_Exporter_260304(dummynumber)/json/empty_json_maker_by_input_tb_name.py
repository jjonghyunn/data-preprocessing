import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))

names = """
25_ny_1_1_scom_da_traffic_app
25_ny_1_1_scom_da_traffic_web
25_ny_1_1_scom_mx_traffic_app
25_ny_1_1_scom_mx_traffic_web
25_ny_1_1_scom_vd_traffic_app
25_ny_1_1_scom_vd_traffic_web
25_ny_2_1_basic_traffic_cmp
25_ny_2_1_basic_traffic_scom
25_ny_2_1_basic_traffic_time
25_ny_3_1_channel_internal
25_ny_3_2_channel_traffic_external
25_ny_3_3_homepage_kv_gnb_to_cmp
25_ny_4_1_order_cvr_loginout
25_ny_4_1_scom_order_cvr_loginout
25_ny_5_1_scom_campaign_order_cvr
25_ny_6_1_multi_order_cross_sell
25_ny_6_2_total_order_cross_sell
25_ny_6_3_cmp_order_cross_sell
25_ny_7_1_order_by_channel_cmp
26_ny_1_1_scom_da_traffic_app
26_ny_1_1_scom_da_traffic_app_prior
26_ny_1_1_scom_da_traffic_web
26_ny_1_1_scom_da_traffic_web_prior
26_ny_1_1_scom_mx_traffic_app
26_ny_1_1_scom_mx_traffic_app_prior
26_ny_1_1_scom_mx_traffic_web
26_ny_1_1_scom_mx_traffic_web_prior
26_ny_1_1_scom_vd_traffic_app
26_ny_1_1_scom_vd_traffic_app_prior
26_ny_1_1_scom_vd_traffic_web
26_ny_1_1_scom_vd_traffic_web_prior
26_ny_2_1_basic_traffic_cmp
26_ny_2_1_basic_traffic_scom
26_ny_2_1_basic_traffic_scom_prior
26_ny_2_1_basic_traffic_time_cmp
26_ny_2_1_basic_traffic_time_scom
26_ny_2_1_basic_traffic_time_scom_prior
26_ny_3_1_channel_internal
26_ny_3_2_channel_external_cmp
26_ny_3_2_channel_external_scom
26_ny_3_2_channel_external_scom_prior
26_ny_3_3_homepage_kv_gnb_to_cmp
26_ny_4_1_order_cvr_loginout
26_ny_4_2_order_cvr_visit_visitor
26_ny_5_1_campaign_order_cvr
26_ny_5_1_scom_order_cvr
26_ny_6_1_multi_order_cross_sell
26_ny_6_1_multi_order_cross_sell_prior
26_ny_6_2_total_order_cross_sell
26_ny_6_2_total_order_cross_sell_prior
26_ny_6_3_cmp_order_cross_sell
26_ny_7_1_order_by_channel_cmp
26_ny_7_1_order_by_channel_scom
26_ny_7_1_order_by_channel_scom_prior
us_26_ny_5_1_campaign_order_cvr_total
26_ny_bestselling
26_ny_raw_multi_purchase_v41
26_ny_raw_multi_purchase_v41_prior
26_ny_nextpage
25_ny_bestselling
26_ny_8_8_cmp_adaptive_banner
""".strip().splitlines()

cnt_exist = 0
cnt_created = 0

for name in names:
    name = name.strip()
    if not name:
        continue
    filepath = os.path.join(script_dir, f"{name}.json")
    if os.path.exists(filepath):
        print(f"✔ 있음 (미생성): {name}.json")
        cnt_exist += 1
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({}, f)
        print(f"✚ 없음 → 생성됨: {name}.json")
        cnt_created += 1

total = cnt_exist + cnt_created
print(f"\n{'─'*40}")
print(f"입력한 파일명 : {len(names)}개")
print(f"체크한 파일  : {total}개")
print(f"  ✔ 있음    : {cnt_exist}개")
print(f"  ✚ 생성됨  : {cnt_created}개")
print(f"  합계      : {total}개")

input_set = {n.strip() for n in names if n.strip()}
extra = sorted([
    f[:-5] for f in os.listdir(script_dir)
    if f.endswith(".json") and f[:-5] not in input_set
])
print(f"\n{'─'*40}")
print(f"입력 목록 외 폴더에 있는 json 파일: {len(extra)}개")
for i, fname in enumerate(extra, 1):
    print(f"  {i:>3}. {fname}.json")
