"""Steps 2-4: clean the cross-sections, then ask how much of the tracked crypto market is Bitcoin, how that moved, and what else is in it.

    ./venv/bin/python analyze.py
        -> results/audit.csv  coverage.csv  cleaning.csv  monthly.csv  tops.csv  movers.csv  extremes.csv  summary.csv

Data: month-end market capitalisation (Coin Metrics "current supply" definition) of every asset in the Coin Metrics community data, 2013-01-31 to 2026-04-30.
The universe is whatever Coin Metrics tracks, not the whole market (Solana and Tron's own coin, for example, are not in it), and it grows from 2 assets in 2013 to about 100.
Cleaning, in order, on each date: (1) rows with a market cap of zero or less are dropped; (2) wrapped, migrated or staked claims on another tracked asset are dropped (WRAPPED); (3) the three Avalanche
chains are summed into one asset; (4) a chain-specific copy (an id with an underscore, like usdt_eth) is dropped if the whole asset (usdt) is also reported that day, and otherwise the copies are
summed into one asset named by the part before the underscore. Categories: stablecoins and tokenized gold are named lists below; everything else is "other".
"""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
R = HERE / "results"
WRAPPED = {"wbtc", "hbtc", "renbtc", "weth", "wnxm", "lend", "susde_eth", "sdai_eth"}
AVAX = {"avaxc": "avax", "avaxp": "avax", "avaxx": "avax"}
STABLE = {"usdt", "usdc", "dai", "busd", "tusd", "usde", "pyusd", "crvusd", "frax", "fdusd", "usdd", "lusd", "gusd", "pax", "eurc", "usdm"}
GOLD = {"xaut", "paxg"}
SNAPSHOTS = ["2014-12-31", "2017-12-31", "2021-12-31", "2026-04-30"]


def clean(g):
    """one date's rows (asset, cap) -> {asset family: cap}, and what each rule did"""
    present = set(g["asset"]); out, log = {}, {}
    for a, c in zip(g["asset"], g["cap"]):
        if a in WRAPPED:
            log[a] = "dropped: wrapped, migrated or staked claim on another tracked asset"; continue
        fam = AVAX.get(a, a)
        if fam != a:
            log[a] = "summed into avax"
        if "_" in a:
            base = a.split("_")[0]
            if base in present:
                log[a] = f"dropped: chain-specific copy of {base}, which is reported as a whole"; continue
            fam = base; log[a] = f"kept as {base} (no whole-asset row), copies summed"
        out[fam] = out.get(fam, 0.0) + c
    return out, log


def main():
    R.mkdir(exist_ok=True)
    d = pd.read_csv(HERE / "data" / "market_caps.csv", parse_dates=["date"]); d["cap"] = d["cap_usd"].astype(float)
    zero = int((d["cap"] <= 0).sum()); dupes = int(d.duplicated(["date", "asset"]).sum()); d = d[d["cap"] > 0]
    yearend = d[d["date"].dt.month == 12].groupby("date")["asset"].nunique()
    audit = [("rows", len(d) + zero), ("dates", d["date"].nunique()), ("assets", d["asset"].nunique()), ("duplicate date-asset rows", dupes), ("rows with a market cap of zero (dropped)", zero),
             ("assets whose id has an underscore", len({a for a in d["asset"].unique() if "_" in a})), ("first date", int(d["date"].min().strftime("%Y%m%d"))), ("last date", int(d["date"].max().strftime("%Y%m%d")))]
    pd.DataFrame(audit, columns=["check", "value"]).to_csv(R / "audit.csv", index=False)
    pd.DataFrame({"year_end": [x.strftime("%Y-%m-%d") for x in yearend.index], "assets_reported": yearend.to_numpy()}).to_csv(R / "coverage.csv", index=False)

    rows, tops, logs, fam_by_date = [], [], {}, {}
    for dt, g in d.groupby("date"):
        s, log = clean(g); fam_by_date[dt] = s; t = sum(s.values()); srt = sorted(s.items(), key=lambda kv: (-kv[1], kv[0]))
        for a, msg in log.items():
            logs.setdefault((a, msg), []).append(dt)
        st = sum(v for k, v in s.items() if k in STABLE); gd = sum(v for k, v in s.items() if k in GOLD); hhi = sum((v / t) ** 2 for v in s.values())
        rows.append({"date": dt.strftime("%Y-%m-%d"), "assets": len(s), "total_cap_usd": t, "btc_share": s.get("btc", 0.0) / t, "eth_share": s.get("eth", 0.0) / t, "stablecoin_share": st / t, "gold_share": gd / t,
                     "other_share": 1 - (s.get("btc", 0.0) + s.get("eth", 0.0) + st + gd) / t, "uncleaned_total_cap_usd": g["cap"].sum(), "uncleaned_btc_share": g.loc[g["asset"] == "btc", "cap"].sum() / g["cap"].sum(), "top5_share": sum(v for _, v in srt[:5]) / t, "top10_share": sum(v for _, v in srt[:10]) / t, "effective_assets": 1 / hhi})
        if dt.strftime("%Y-%m-%d") in SNAPSHOTS:
            tops += [{"date": dt.strftime("%Y-%m-%d"), "rank": i + 1, "asset": a, "cap_usd": v, "share": v / t} for i, (a, v) in enumerate(srt[:10])]
    m = pd.DataFrame(rows); m.to_csv(R / "monthly.csv", index=False); pd.DataFrame(tops).to_csv(R / "tops.csv", index=False)
    cl = [{"asset": a, "what_happens": msg, "dates_affected": len(ds), "first_date": min(ds).strftime("%Y-%m-%d"), "last_date": max(ds).strftime("%Y-%m-%d")} for (a, msg), ds in sorted(logs.items())]
    pd.DataFrame(cl).to_csv(R / "cleaning.csv", index=False)

    # movers: the change in market cap over the last twelve months among the largest assets now
    now, then = fam_by_date[pd.Timestamp("2026-04-30")], fam_by_date[pd.Timestamp("2025-04-30")]
    top15 = sorted(now.items(), key=lambda kv: (-kv[1], kv[0]))[:15]
    pd.DataFrame([{"asset": a, "cap_usd_now": v, "cap_usd_year_ago": then.get(a, float("nan")), "change_pct": 100 * (v / then[a] - 1) if a in then else float("nan")} for a, v in top15]).to_csv(R / "movers.csv", index=False)

    big = m[m["assets"] >= 10]
    ex = [("lowest Bitcoin share (at least 10 assets)", big.loc[big["btc_share"].idxmin(), "date"], big["btc_share"].min()), ("highest Bitcoin share (at least 10 assets)", big.loc[big["btc_share"].idxmax(), "date"], big["btc_share"].max()),
          ("highest stablecoin share", m.loc[m["stablecoin_share"].idxmax(), "date"], m["stablecoin_share"].max()), ("highest Ether share", m.loc[m["eth_share"].idxmax(), "date"], m["eth_share"].max()),
          ("highest total market cap", m.loc[m["total_cap_usd"].idxmax(), "date"], m["total_cap_usd"].max())]
    pd.DataFrame(ex, columns=["what", "date", "value"]).to_csv(R / "extremes.csv", index=False)
    last = m.iloc[-1]; share_at = lambda day: float(m.loc[m["date"] == day, "btc_share"].iloc[0])
    summ = {"btc_share_2013_12_31": share_at("2013-12-31"), "btc_share_2017_12_31": share_at("2017-12-31"), "btc_share_2021_12_31": share_at("2021-12-31"), "btc_share_latest": last["btc_share"], "eth_share_latest": last["eth_share"], "stablecoin_share_latest": last["stablecoin_share"],
            "top5_share_latest": last["top5_share"], "top10_share_latest": last["top10_share"], "effective_assets_latest": last["effective_assets"], "assets_latest": last["assets"], "total_cap_latest_usd": last["total_cap_usd"],
            "months_with_btc_below_50pct": int((big["btc_share"] < 0.5).sum()), "months_with_at_least_10_assets": len(big), "btc_share_latest_uncleaned": last["uncleaned_btc_share"], "total_cap_latest_uncleaned_usd": last["uncleaned_total_cap_usd"]}
    pd.DataFrame(list(summ.items()), columns=["key", "value"]).to_csv(R / "summary.csv", index=False)
    for f in ("audit", "cleaning", "extremes", "summary", "movers", "tops"):
        print("==", f); print(pd.read_csv(R / f"{f}.csv").round(4).to_string(index=False))


if __name__ == "__main__":
    main()
