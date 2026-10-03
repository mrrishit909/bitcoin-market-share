"""Step 5: the project's check. Recompute with different code, in plain Python straight from data/market_caps.csv (the csv module, dicts and loops: no pandas): the audit and coverage, the cleaning
rules and what each did, the shares of Bitcoin, Ether, stablecoins and tokenized gold on every date, the concentration measures, the top ten on four dates, the twelve-month movers, the extremes
and the summary figures.

    ./venv/bin/python check.py
"""
import csv
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
R = HERE / "results"
WRAPPED = ("wbtc", "hbtc", "renbtc", "weth", "wnxm", "lend", "susde_eth", "sdai_eth")
STABLE = ("usdt", "usdc", "dai", "busd", "tusd", "usde", "pyusd", "crvusd", "frax", "fdusd", "usdd", "lusd", "gusd", "pax", "eurc", "usdm")
GOLD = ("xaut", "paxg")
n_ok = 0


def same(label, got, want, rel=1e-9):
    global n_ok
    n_ok += 1
    want = float(want) if want != "" else float("nan")
    if math.isnan(want):
        assert math.isnan(got), f"{label}: recount {got} != results nan"
    else:
        assert abs(got - want) <= rel * max(1.0, abs(want)), f"{label}: recount {got} != results {want}"


def eq(label, got, want):
    global n_ok
    n_ok += 1
    assert got == want, f"{label}: recount {got!r} != results {want!r}"


def table(name):
    return list(csv.DictReader(open(R / f"{name}.csv")))


def clean(rows):
    """rows: [(asset, cap)] for one date -> ({family: cap}, {asset: message})"""
    present = {a for a, _ in rows}; out = defaultdict(float); log = {}
    for a, c in rows:
        if a in WRAPPED:
            log[a] = "dropped: wrapped, migrated or staked claim on another tracked asset"; continue
        fam = "avax" if a in ("avaxc", "avaxp", "avaxx") else a
        if fam != a:
            log[a] = "summed into avax"
        if "_" in a:
            base = a.split("_")[0]
            if base in present:
                log[a] = f"dropped: chain-specific copy of {base}, which is reported as a whole"; continue
            fam = base; log[a] = f"kept as {base} (no whole-asset row), copies summed"
        out[fam] += c
    return dict(out), log


def main():
    raw = list(csv.DictReader(open(HERE / "data" / "market_caps.csv"))); zero = sum(1 for r in raw if float(r["cap_usd"]) <= 0)
    keys = [(r["date"], r["asset"]) for r in raw]; dupes = len(keys) - len(set(keys))
    by_date = defaultdict(list)
    for r in raw:
        if float(r["cap_usd"]) > 0:
            by_date[r["date"]].append((r["asset"], float(r["cap_usd"])))
    dates = sorted(by_date); assets = {a for rows in by_date.values() for a, _ in rows}

    a = {r["check"]: float(r["value"]) for r in table("audit")}
    for label, got in (("rows", len(raw)), ("dates", len(dates)), ("assets", len(assets)), ("duplicate date-asset rows", dupes), ("rows with a market cap of zero (dropped)", zero),
                       ("assets whose id has an underscore", sum("_" in x for x in assets)), ("first date", int(dates[0].replace("-", ""))), ("last date", int(dates[-1].replace("-", "")))):
        same(label, got, a[label])
    cov = table("coverage"); eq("coverage dates", [r["year_end"] for r in cov], [d for d in dates if d[5:7] == "12"])
    for r in cov:
        same(f"coverage {r['year_end']}", len({x for x, _ in by_date[r["year_end"]]}), r["assets_reported"])

    fam, logs = {}, defaultdict(list)
    for d in dates:
        fam[d], log = clean(by_date[d])
        for asset, msg in log.items():
            logs[(asset, msg)].append(d)
    for r, ((asset, msg), ds) in zip(table("cleaning"), sorted(logs.items())):
        eq("cleaning asset", r["asset"], asset); eq("cleaning message", r["what_happens"], msg); same("dates affected", len(ds), r["dates_affected"]); eq("first", r["first_date"], min(ds)); eq("last", r["last_date"], max(ds))
    eq("cleaning rows", len(table("cleaning")), len(logs))

    monthly = table("monthly"); eq("monthly dates", [r["date"] for r in monthly], dates); calc = {}
    for r in monthly:
        d = r["date"]; s = fam[d]; t = sum(s.values()); srt = sorted(s.items(), key=lambda kv: (-kv[1], kv[0])); st = sum(v for k, v in s.items() if k in STABLE); gd = sum(v for k, v in s.items() if k in GOLD)
        o = {"assets": len(s), "total_cap_usd": t, "btc_share": s.get("btc", 0.0) / t, "eth_share": s.get("eth", 0.0) / t, "stablecoin_share": st / t, "gold_share": gd / t, "other_share": 1 - (s.get("btc", 0.0) + s.get("eth", 0.0) + st + gd) / t, "uncleaned_total_cap_usd": sum(c for _, c in by_date[d]), "uncleaned_btc_share": sum(c for x, c in by_date[d] if x == "btc") / sum(c for _, c in by_date[d]),
             "top5_share": sum(v for _, v in srt[:5]) / t, "top10_share": sum(v for _, v in srt[:10]) / t, "effective_assets": 1 / sum((v / t) ** 2 for v in s.values())}
        calc[d] = o
        for k, v in o.items():
            same(f"monthly {d} {k}", v, r[k], 1e-8)
    tp = table("tops")
    for r in tp:
        s = fam[r["date"]]; t = sum(s.values()); srt = sorted(s.items(), key=lambda kv: (-kv[1], kv[0])); i = int(r["rank"]) - 1
        eq(f"top {r['date']} {i + 1}", r["asset"], srt[i][0]); same("cap", srt[i][1], r["cap_usd"], 1e-8); same("share", srt[i][1] / t, r["share"], 1e-8)
    eq("top rows", sorted({r["date"] for r in tp}), ["2014-12-31", "2017-12-31", "2021-12-31", "2026-04-30"]); eq("top count", len(tp), sum(min(10, len(fam[x])) for x in ["2014-12-31", "2017-12-31", "2021-12-31", "2026-04-30"]))
    now, then = fam["2026-04-30"], fam["2025-04-30"]; top15 = sorted(now.items(), key=lambda kv: (-kv[1], kv[0]))[:15]
    for r, (asset, v) in zip(table("movers"), top15):
        eq("mover", r["asset"], asset); same("now", v, r["cap_usd_now"], 1e-8); same("year ago", then.get(asset, float("nan")), r["cap_usd_year_ago"], 1e-8); same("change", 100 * (v / then[asset] - 1) if asset in then else float("nan"), r["change_pct"], 1e-8)
    big = [d for d in dates if calc[d]["assets"] >= 10]; lo = min(big, key=lambda d: (calc[d]["btc_share"], d)); hi = max(big, key=lambda d: (calc[d]["btc_share"], d)); ex = {r["what"]: r for r in table("extremes")}
    for what, d, v in (("lowest Bitcoin share (at least 10 assets)", lo, calc[lo]["btc_share"]), ("highest Bitcoin share (at least 10 assets)", hi, calc[hi]["btc_share"]),
                       ("highest stablecoin share", max(dates, key=lambda x: (calc[x]["stablecoin_share"], x)), max(calc[x]["stablecoin_share"] for x in dates)), ("highest Ether share", max(dates, key=lambda x: (calc[x]["eth_share"], x)), max(calc[x]["eth_share"] for x in dates)),
                       ("highest total market cap", max(dates, key=lambda x: (calc[x]["total_cap_usd"], x)), max(calc[x]["total_cap_usd"] for x in dates))):
        eq(f"extreme {what} date", ex[what]["date"], d); same(f"extreme {what}", v, ex[what]["value"], 1e-8)
    L = calc[dates[-1]]; sm = {r["key"]: float(r["value"]) for r in table("summary")}
    exp = {"btc_share_2013_12_31": calc["2013-12-31"]["btc_share"], "btc_share_2017_12_31": calc["2017-12-31"]["btc_share"], "btc_share_2021_12_31": calc["2021-12-31"]["btc_share"], "btc_share_latest": L["btc_share"], "eth_share_latest": L["eth_share"],
           "stablecoin_share_latest": L["stablecoin_share"], "top5_share_latest": L["top5_share"], "top10_share_latest": L["top10_share"], "effective_assets_latest": L["effective_assets"], "assets_latest": L["assets"], "total_cap_latest_usd": L["total_cap_usd"],
           "months_with_btc_below_50pct": sum(calc[d]["btc_share"] < 0.5 for d in big), "months_with_at_least_10_assets": len(big), "btc_share_latest_uncleaned": L["uncleaned_btc_share"], "total_cap_latest_uncleaned_usd": L["uncleaned_total_cap_usd"]}
    eq("summary keys", sorted(sm), sorted(exp))
    for k, v in exp.items():
        same(f"summary {k}", v, sm[k], 1e-8)
    print(f"check.py: {n_ok} recomputed numbers agree with results/ (the cleaning rules re-implemented in plain Python)")


if __name__ == "__main__":
    main()
