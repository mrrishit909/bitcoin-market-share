"""Step 1: the market capitalisation of every asset in the Coin Metrics community data, on the last day of each month.

    ./venv/bin/python download.py   -> data/market_caps.csv, results/pull.json

Coin Metrics community API (https://community-api.coinmetrics.io/v4), metric CapMrktCurUSD ("capitalization, market, current supply, USD": price times the current supply, which counts supply that is
locked or in escrow), for every asset that has it, on each month end from 2013-01-31 to 2026-04-30. Free for non-commercial use under CC BY-NC 4.0; attribution: Coin Metrics (coinmetrics.io).
One request per date; the 160 responses are stored as one small table (date, asset, cap), so the exact data used is committed, with its checksum.
"""
import csv
import hashlib
import json
import ssl
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import certifi

HERE = Path(__file__).parent
URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=*&metrics=CapMrktCurUSD&frequency=1d&start_time={d}&end_time={d}&page_size=10000"
CTX = ssl.create_default_context(cafile=certifi.where())


def month_ends(first=(2013, 1), last=(2026, 4)):
    y, m = first
    while (y, m) <= last:
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        yield date(ny, nm, 1) - timedelta(days=1); y, m = ny, nm


def main():
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "results").mkdir(exist_ok=True)
    rows = []; dates = list(month_ends())
    for d in dates:
        req = urllib.request.Request(URL.format(d=d.isoformat()), headers={"User-Agent": "research-portfolio (Rishit Raj Mathur)"})
        for attempt in range(5):
            try:
                data = json.load(urllib.request.urlopen(req, context=CTX, timeout=90))["data"]; break
            except Exception as e:                    # rate limit or a dropped connection: wait and retry
                time.sleep(3 * (attempt + 1)); err = e
        else:
            raise err
        rows += [(r["time"][:10], r["asset"], r["CapMrktCurUSD"]) for r in data if r.get("CapMrktCurUSD")]
        time.sleep(0.8)
    rows.sort()
    with open(HERE / "data" / "market_caps.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "asset", "cap_usd"]); w.writerows(rows)
    blob = (HERE / "data" / "market_caps.csv").read_bytes()
    info = {"pulled": date.today().isoformat(), "source": "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics (CapMrktCurUSD, 1d, all assets)", "dates": len(dates), "rows": len(rows), "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
    (HERE / "results" / "pull.json").write_text(json.dumps(info, indent=2) + "\n"); print(info)


if __name__ == "__main__":
    main()
