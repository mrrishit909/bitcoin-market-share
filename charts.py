"""Step 6: charts.   ./venv/bin/python charts.py -> charts/00_cover.png, 01_composition.png, 02_tops.png, 03_concentration.png, 04_movers.png"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
R = HERE / "results"
INK, DIM, GRID, BG, BLUE, ORANGE, GRAY, GREEN = "#f2f2f0", "#8a8a87", "#1d1d1d", "#0b0b0b", "#3987e5", "#d95926", "#9a9a96", "#3aa876"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": INK,
                     "axes.edgecolor": "#3a3a3a", "axes.labelcolor": DIM, "xtick.color": DIM, "ytick.color": DIM,
                     "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 1,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 11, "axes.titlesize": 13,
                     "axes.titlelocation": "left", "axes.titlepad": 12})
M = pd.read_csv(R / "monthly.csv", parse_dates=["date"]); T = pd.read_csv(R / "tops.csv"); MV = pd.read_csv(R / "movers.csv")
CAT = {"btc": ORANGE, "eth": BLUE, "stable": GREEN}


def save(fig, name):
    fig.tight_layout(); fig.savefig(HERE / "charts" / name, dpi=150); plt.close(fig)


def composition(ax):
    m = M[M["date"] >= "2016-12-31"]; parts = [m["btc_share"], m["eth_share"], m["stablecoin_share"], m["gold_share"] + m["other_share"]]
    ax.stackplot(m["date"], [100 * p for p in parts], colors=[ORANGE, BLUE, GREEN, "#4a4a48"], labels=["Bitcoin", "Ether", "stablecoins", "everything else"], linewidth=0, alpha=0.95)
    ax.set_ylim(0, 100); ax.set_xlim(m["date"].min(), m["date"].max()); ax.set_ylabel("% of the tracked market's value"); ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.0))
    for dt, txt, dy in (("2017-12-31", "33.0%", -9), ("2018-01-31", "28.7% (low)", -22), ("2026-04-30", "65.0%", -8)):
        v = float(M.loc[M["date"] == dt, "btc_share"].iloc[0]) * 100; x = pd.Timestamp(dt)
        ax.annotate(txt, (x, v), xytext=(-6 if dt == "2026-04-30" else 6, dy), textcoords="offset points", color="#fff", fontsize=9, ha="right" if dt == "2026-04-30" else "left", fontweight="bold")
    ax.set_title("What the tracked crypto market is made of, month by month")


def tops(axes):
    for ax, dt in zip(axes.flat, ["2014-12-31", "2017-12-31", "2021-12-31", "2026-04-30"]):
        t = T[T["date"] == dt].iloc[::-1]; n = int(M.loc[M["date"] == dt, "assets"].iloc[0])
        ax.barh(range(len(t)), 100 * t["share"], color=[ORANGE if a == "btc" else BLUE if a == "eth" else GREEN if a in ("usdt", "usdc") else GRAY for a in t["asset"]], height=0.68)
        for i, (a, s) in enumerate(zip(t["asset"], t["share"])):
            ax.text(100 * s + 1, i, f"{100 * s:.1f}%", va="center", color=INK, fontsize=8)
        ax.set_yticks(range(len(t))); ax.set_yticklabels([a.upper() for a in t["asset"]], fontsize=9); ax.set_xlim(0, 85); ax.grid(axis="y", visible=False)
        ax.set_title(f"{pd.Timestamp(dt):%b %Y}: {n} assets", fontsize=11)


def concentration(axes):
    m = M[M["date"] >= "2016-12-31"]; ax = axes[0]
    ax.plot(m["date"], 100 * m["top5_share"], color=BLUE, linewidth=2, label="five largest"); ax.plot(m["date"], 100 * m["top10_share"], color=GRAY, linewidth=2, label="ten largest")
    ax.set_ylim(60, 100); ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="lower right"); ax.set_ylabel("% of the tracked market's value"); ax.set_title("Share held by the largest assets", fontsize=12)
    ax = axes[1]; ax.plot(m["date"], m["effective_assets"], color=ORANGE, linewidth=2); ax.set_ylim(0, 6); ax.set_ylabel("effective number of assets"); ax.set_title("As if the market were this many equal assets", fontsize=12)


def movers(ax):
    t = MV.iloc[::-1].reset_index(drop=True); y = np.arange(len(t)); v = t["change_pct"].clip(-100, 100)
    ax.barh(y, v, color=[BLUE if c > 0 else ORANGE for c in t["change_pct"]], height=0.66); ax.axvline(0, color=DIM, linewidth=1)
    for yi, (a, c) in enumerate(zip(t["asset"], t["change_pct"])):
        ax.text(max(min(c, 100), 0) + 2 if c > 0 else min(c, 0) - 2, yi, f"{c:+.0f}%", va="center", ha="left" if c > 0 else "right", color=INK, fontsize=8.5)
    ax.set_yticks(y); ax.set_yticklabels([a.upper() for a in t["asset"]]); ax.set_xlim(-100, 130); ax.set_xlabel("change in market value, April 2025 to April 2026 (%; the bar for ZEC is cut at 100)"); ax.grid(axis="y", visible=False)
    ax.set_title("The 15 largest assets today: what happened to their value in a year")


def main():
    (HERE / "charts").mkdir(exist_ok=True)
    fig = plt.figure(figsize=(14, 8)); g = fig.add_gridspec(1, 2, width_ratios=[1.35, 1]); a = fig.add_subplot(g[0]); b = fig.add_subplot(g[1]); composition(a)
    t = T[T["date"] == "2026-04-30"].iloc[::-1]; b.barh(range(len(t)), 100 * t["share"], color=[ORANGE if x == "btc" else BLUE if x == "eth" else GREEN if x in ("usdt", "usdc") else GRAY for x in t["asset"]], height=0.68)
    for i, s in enumerate(t["share"]):
        b.text(100 * s + 1, i, f"{100 * s:.1f}%", va="center", color=INK, fontsize=10)
    b.set_yticks(range(len(t))); b.set_yticklabels([x.upper() for x in t["asset"]]); b.set_xlim(0, 85); b.grid(axis="y", visible=False); b.set_title("The ten largest, April 2026")
    for ax in (a, b):
        ax.title.set_fontsize(15)
    fig.suptitle("How much of the tracked crypto market is Bitcoin? 65% today, 29% at its low in January 2018", x=0.01, ha="left", fontsize=20, color=INK, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(HERE / "charts" / "00_cover.png", dpi=100); plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 3.9)); composition(ax); save(fig, "01_composition.png")
    fig, axes = plt.subplots(2, 2, figsize=(10, 5.2)); tops(axes); save(fig, "02_tops.png")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6)); concentration(axes); save(fig, "03_concentration.png")
    fig, ax = plt.subplots(figsize=(10, 4.3)); movers(ax); save(fig, "04_movers.png")


if __name__ == "__main__":
    main()
