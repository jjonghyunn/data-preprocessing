# utils/aa_exporter.py
from __future__ import annotations

import os
import json
import time
import csv
import shutil
from dataclasses import dataclass
from datetime import datetime
from importlib.resources import files
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import pandas as pd
from tqdm.auto import tqdm
import aanalytics2 as api2

# ✅ site_registry에서 RSID/메타 가져오기
try:
    from utils.site_registry import lookup_site
except ImportError:  # pragma: no cover
    from site_registry import lookup_site


@dataclass
class ExportConfig:
    # input
    data_csv: str
    json_file: str

    # output
    out_dir: str = "aa_exports"
    out_prefix: str = "AA_EXPORT"
    output_format: str = "csv"          # "csv" | "xlsx" (현재 구현은 csv에 최적화)
    csv_encoding: str = "utf-8-sig"     # 엑셀에서 바로 열기 좋게 기본은 utf-8-sig

    # auth
    cfg_filename: str = "aanalyticsact_auth.json"
    company_id: str = "samsun0"

    # request settings
    limit: int = 50000                  # ✅ 가능하면 50,000 (요청 횟수 ↓)
    sleep_sec: float = 0.0              # 보통 0 (429/5xx는 retry가 처리)
    max_pages: int = 100000
    timeout: int = 600
    max_retries: int = 10

    # data columns
    site_col: str = "Site_Code"
    start_col: str = "Start_Date"
    end_col: str = "End_Date"

    # ✅ tbColumn처럼 “원하는 컬럼명”을 직접 넣고 싶을 때
    # - None이면 payload의 metrics/id+columnId로 자동 생성(units_2, orders_3 ... 형태)
    # - list를 주면 그 이름을 그대로 헤더로 사용 (순서가 payload.metrics 순서와 1:1 매칭이어야 함)
    tb_columns: list[str] | None = None

    # logging
    log_each_page: bool = False

    # ✅ 속도 핵심: 국가(site) 단위 병렬
    parallel_sites: bool = True
    max_workers: int = 6                # 5~8 추천 (오류 생기면 값 낮추기)

    # tmp merge
    cleanup_tmp: bool = True

    # whether End_Date in CSV is inclusive (default True)
    # if True, the code will add +1 day to End_Date when building API dateRange
    inclusive_end_date: bool = True
class AAExporter:
    def __init__(self, cfg: ExportConfig):
        self.cfg = cfg
        os.makedirs(self.cfg.out_dir, exist_ok=True)

        # headers/endpoint는 모든 스레드가 공유(읽기전용)해도 OK
        self.headers, self.endpoint = self._get_headers_and_endpoint()

        # payload template 로드 + sanitize
        self.payload_template = self._sanitize_payload(self._load_payload_from_file(self.cfg.json_file))
        self.payload_template.setdefault("settings", {})
        self.payload_template["settings"]["limit"] = self._cap_limit(self.cfg.limit)
        self.payload_template["settings"]["page"] = 0

        # metrics 길이
        self.metrics_len = len(self.payload_template["metricContainer"]["metrics"])

        # metric columns 결정: tb_columns가 있으면 강제 / 없으면 자동
        if self.cfg.tb_columns is not None:
            if len(self.cfg.tb_columns) != self.metrics_len:
                raise ValueError(
                    f"tb_columns 개수({len(self.cfg.tb_columns)}) != payload metrics 개수({self.metrics_len}).\n"
                    f"payload metrics 개수에 맞게 tb_columns를 맞춰줘야 컬럼 매핑이 안 틀어져."
                )
            self.metric_cols = list(self.cfg.tb_columns)
        else:
            self.metric_cols = self._metric_columns_from_payload(self.payload_template)

        # 최종 CSV header
        self.header = (
            ["Subsidiary", "Country", self.cfg.site_col, "RSID", self.cfg.start_col, self.cfg.end_col, "itemId", "value"]
            + self.metric_cols
            + ["status", "error"]
        )

        if self.cfg.output_format.lower() != "csv":
            raise NotImplementedError("현재 완성본은 CSV 출력에 최적화되어 있어. output_format='csv'로 써줘.")

    # -------------------------
    # PUBLIC
    # -------------------------
    def run(self) -> str:
        df = pd.read_csv(self.cfg.data_csv)

        # 컬럼 존재 체크
        for c in (self.cfg.site_col, self.cfg.start_col, self.cfg.end_col):
            if c not in df.columns:
                raise ValueError(f"'{c}' 컬럼이 CSV에 없습니다. 현재 컬럼: {list(df.columns)}")

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        out_csv = os.path.join(self.cfg.out_dir, f"{self.cfg.out_prefix}_{ts}.csv")

        # tmp dir (site별 csv 쪼개서 병렬로 쓰고 마지막에 merge)
        tmp_dir = os.path.join(self.cfg.out_dir, f"__tmp_{self.cfg.out_prefix}_{ts}")
        os.makedirs(tmp_dir, exist_ok=True)

        start_ts = datetime.now()
        print(f"▶ Start time: {start_ts.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"▶ Output: {out_csv}")
        print(f"▶ Parallel sites: {self.cfg.parallel_sites} (max_workers={self.cfg.max_workers})")
        print(f"▶ limit(page size): {self._cap_limit(self.cfg.limit):,}")
        print(f"▶ Metric columns: {self.metric_cols}")  
        
        if self.cfg.parallel_sites:
            results = self._run_parallel(df=df, tmp_dir=tmp_dir)
        else:
            results = self._run_sequential(df=df, tmp_dir=tmp_dir)

        # merge
        self._merge_tmp_csvs(results=results, out_csv=out_csv)

        # cleanup
        if self.cfg.cleanup_tmp:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        end_ts = datetime.now()
        total_rows = sum(r["rows_written"] for r in results if r["ok"])
        failed = [r for r in results if not r["ok"]]

        print("\n*****Data Extraction Completed*****")
        print(f"✅ Saved CSV: {out_csv}")
        print(f"총 데이터 row(FAILED row 제외, header 제외): {total_rows:,}")
        print(f"⏱ Elapsed: {end_ts - start_ts}")
        print(f"❌ 실패 site: {len(failed)}")
        if failed:
            print("실패 목록(앞 50개):")
            for r in failed[:50]:
                print(" -", r["site_code"], "|", r["error"])

        return out_csv

    # -------------------------
    # RUN MODES
    # -------------------------
    def _run_parallel(self, df: pd.DataFrame, tmp_dir: str) -> list[dict]:
        results: list[dict] = []
        futures = {}

        with ThreadPoolExecutor(max_workers=self.cfg.max_workers) as ex:
            for idx, row in df.iterrows():
                fut = ex.submit(self._export_one_site_to_tmp, idx, row, tmp_dir)
                futures[fut] = idx

            pbar = tqdm(total=len(futures), desc="AA Export (sites)", unit="site")
            for fut in as_completed(futures):
                res = fut.result()
                results.append(res)
                pbar.set_postfix(site=res["site_code"], rows=res["rows_written"], ok=res["ok"])
                pbar.update(1)
            pbar.close()

        # merge 순서를 원본 df 순서로 맞추기
        results.sort(key=lambda x: x["idx"])
        return results

    def _run_sequential(self, df: pd.DataFrame, tmp_dir: str) -> list[dict]:
        results: list[dict] = []
        pbar = tqdm(total=len(df), desc="AA Export (sites)", unit="site")
        for idx, row in df.iterrows():
            res = self._export_one_site_to_tmp(idx, row, tmp_dir)
            results.append(res)
            pbar.set_postfix(site=res["site_code"], rows=res["rows_written"], ok=res["ok"])
            pbar.update(1)
        pbar.close()
        return results

    # -------------------------
    # EXPORT (per site)
    # -------------------------
    def _export_one_site_to_tmp(self, idx: int, row: pd.Series, tmp_dir: str) -> dict:
        raw_site_code = row[self.cfg.site_col]
        start_date = row[self.cfg.start_col]
        end_date = row[self.cfg.end_col]

        info = lookup_site(raw_site_code)
        site_code_out = str(raw_site_code).strip().upper()

        tmp_path = os.path.join(tmp_dir, f"{idx:04d}_{site_code_out}.csv")

        # ✅ 스레드마다 Session 따로 (requests.Session은 thread-safe 아님)
        session = requests.Session()

        rows_written = 0
        ok = True
        err = ""

        try:
            payload = self._build_payload(self.payload_template, info.rsid, start_date, end_date)

            with open(tmp_path, "w", newline="", encoding=self.cfg.csv_encoding) as f:
                w = csv.writer(f)
                w.writerow(self.header)

                rows_written = self._export_all_pages_to_csv_writer(
                    session=session,
                    payload=payload,
                    writer=w,
                    context_values=[info.subsidiary, info.country, site_code_out, info.rsid, start_date, end_date],
                )

        except Exception as e:
            ok = False
            err = str(e)

            zeros = [0] * len(self.metric_cols)
            with open(tmp_path, "w", newline="", encoding=self.cfg.csv_encoding) as f:
                w = csv.writer(f)
                w.writerow(self.header)
                w.writerow(
                    [info.subsidiary, info.country, site_code_out, info.rsid, start_date, end_date, None, None]
                    + zeros
                    + ["FAILED", err]
                )

        finally:
            session.close()

        return {
            "idx": idx,
            "site_code": site_code_out,
            "rsid": info.rsid,
            "tmp_path": tmp_path,
            "rows_written": rows_written,
            "ok": ok,
            "error": err,
        }

    def _export_all_pages_to_csv_writer(
        self,
        session: requests.Session,
        payload: dict,
        writer: csv.writer,
        context_values: list,
    ) -> int:
        limit = int(payload.get("settings", {}).get("limit", 0) or 0)
        written = 0

        for page in range(self.cfg.max_pages):
            payload["settings"]["page"] = page

            r = self._post_with_retry(session=session, payload=payload)
            res = r.json()

            rows = res.get("rows", [])
            if not rows:
                break

            batch = []
            for row in rows:
                itemId = row.get("itemId")
                value = row.get("value")
                data = row.get("data", [])

                rec = context_values + [itemId, value]
                for i in range(len(self.metric_cols)):
                    rec.append(data[i] if i < len(data) else None)
                rec += ["OK", ""]
                batch.append(rec)

            writer.writerows(batch)
            written += len(batch)

            if self.cfg.log_each_page:
                print(f"  [page={page}] fetched {len(rows):,} | written(total)={written:,}")

            if res.get("lastPage") is True:
                break
            total_pages = res.get("totalPages")
            if isinstance(total_pages, int) and page >= total_pages - 1:
                break
            if limit and len(rows) < limit:
                break

            if self.cfg.sleep_sec and self.cfg.sleep_sec > 0:
                time.sleep(self.cfg.sleep_sec)

        return written

    # -------------------------
    # MERGE
    # -------------------------
    def _merge_tmp_csvs(self, results: list[dict], out_csv: str) -> None:
        with open(out_csv, "w", newline="", encoding=self.cfg.csv_encoding) as out_f:
            out_w = csv.writer(out_f)
            out_w.writerow(self.header)

            for r in results:
                tmp_path = r["tmp_path"]
                with open(tmp_path, "r", newline="", encoding=self.cfg.csv_encoding) as in_f:
                    reader = csv.reader(in_f)
                    _ = next(reader, None)  # header skip
                    for row in reader:
                        out_w.writerow(row)

    # -------------------------
    # AUTH
    # -------------------------
    def _get_headers_and_endpoint(self):
        API_KEY = os.getenv("AA_API_KEY")
        GLOBAL_COMPANY_ID = os.getenv("AA_GLOBAL_COMPANY_ID")
        ACCESS_TOKEN = os.getenv("AA_ACCESS_TOKEN")

        if API_KEY and GLOBAL_COMPANY_ID and ACCESS_TOKEN:
            headers = {
                "x-api-key": API_KEY,
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "x-proxy-global-company-id": GLOBAL_COMPANY_ID,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            endpoint = f"https://analytics.adobe.io/api/{GLOBAL_COMPANY_ID}/reports"
            return headers, endpoint

        cfg_path = files("aanalyticsactauth") / self.cfg.cfg_filename
        if not cfg_path.is_file():
            raise FileNotFoundError(f"설정 파일이 패키지 안에 없습니다: {cfg_path}")

        api2.importConfigFile(str(cfg_path))
        api2.Login()

        ags = api2.Analytics(self.cfg.company_id)
        h = dict(ags.header) if isinstance(getattr(ags, "header", None), dict) else {}

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        if "x-api-key" in h:
            headers["x-api-key"] = h["x-api-key"]
        elif "x-api-key".lower() in h:
            headers["x-api-key"] = h["x-api-key".lower()]

        if "Authorization" in h:
            headers["Authorization"] = h["Authorization"]
        elif "authorization" in h:
            headers["Authorization"] = h["authorization"]

        gcid = h.get("x-proxy-global-company-id") or h.get("x-proxy-global-company-id".lower())
        if not gcid:
            raise RuntimeError("x-proxy-global-company-id를 헤더에서 못 찾았습니다. config/로그인 상태 확인 필요")

        headers["x-proxy-global-company-id"] = gcid
        endpoint = f"https://analytics.adobe.io/api/{gcid}/reports"
        return headers, endpoint

    # -------------------------
    # HTTP
    # -------------------------
    def _post_with_retry(self, session: requests.Session, payload: dict):
        for attempt in range(self.cfg.max_retries + 1):
            r = session.post(self.endpoint, headers=self.headers, json=payload, timeout=self.cfg.timeout)

            if r.status_code < 400:
                return r

            if r.status_code in (429, 500, 502, 503, 504):
                ra = r.headers.get("Retry-After")
                if ra:
                    try:
                        sleep_sec = float(ra)
                    except ValueError:
                        sleep_sec = 2.0
                else:
                    sleep_sec = min(2 ** attempt, 30)

                if attempt == self.cfg.max_retries:
                    r.raise_for_status()

                time.sleep(sleep_sec)
                continue

            r.raise_for_status()

        raise RuntimeError("post_with_retry: unexpected fall-through")

    # -------------------------
    # PAYLOAD
    # -------------------------
    def _load_payload_from_file(self, json_path: str) -> dict:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _sanitize_payload(self, payload: dict) -> dict:
        p = json.loads(json.dumps(payload))
        p.pop("capacityMetadata", None)
        p.pop("statistics", None)

        for gf in p.get("globalFilters", []):
            if gf.get("type") == "dateRange":
                gf.pop("dateRangeId", None)

        if "settings" not in p or not isinstance(p["settings"], dict):
            p["settings"] = {}
        p["settings"].pop("includeAnnotations", None)
        p["settings"].setdefault("page", 0)
        return p

    def _to_aa_iso(self, d) -> str:
        dt = pd.to_datetime(str(d).strip())
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000")

    def _build_payload(self, payload_template: dict, rsid: str, start_date, end_date) -> dict:
        """
        Build payload for given rsid and date range.
        If cfg.inclusive_end_date is True, end_date will be incremented by 1 day
        so that CSV's inclusive End_Date is interpreted correctly by the API
        (API expects exclusive end timestamp).
        """
        p = json.loads(json.dumps(payload_template))
        p["rsid"] = rsid

        # start_date -> AA ISO
        # end_date: apply inclusive -> exclusive conversion if configured
        start_iso_input = start_date
        end_iso_input = end_date

        if self.cfg.inclusive_end_date:
            # try to parse end_date and add 1 day
            try:
                end_dt = pd.to_datetime(str(end_date).strip())
                end_dt = end_dt + pd.Timedelta(days=1)
                end_iso_input = end_dt
            except Exception:
                # fallback: keep original end_date string (best-effort)
                end_iso_input = end_date

        dr = f"{self._to_aa_iso(start_iso_input)}/{self._to_aa_iso(end_iso_input)}"

        found = False
        for gf in p.get("globalFilters", []):
            if gf.get("type") == "dateRange":
                gf["dateRange"] = dr
                gf.pop("dateRangeId", None)
                found = True
                break
        if not found:
            p.setdefault("globalFilters", []).append({"type": "dateRange", "dateRange": dr})

        p.setdefault("settings", {})
        p["settings"]["page"] = 0
        p["settings"]["limit"] = self._cap_limit(self.cfg.limit)
        return p

    def _metric_columns_from_payload(self, payload: dict) -> list[str]:
        n = len(payload["metricContainer"]["metrics"])
        return [f"value{i+1}" for i in range(n)]
    
    def _cap_limit(self, limit: int) -> int:
        try:
            x = int(limit)
        except Exception:
            x = 10000
        return max(1, min(x, 50000))


