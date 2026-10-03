# How much of the tracked crypto market is Bitcoin?

The market value of every asset in the Coin Metrics community data on the last day of each month from January 2013 to April 2026, cleaned of double counting. Five questions:
- how big a share of the tracked market is Bitcoin, and how has it moved;
- what else is in it: Ether, stablecoins, tokenized gold and the rest;
- how concentrated is the market in a few assets;
- who were the ten largest at four moments, and what happened to the largest assets over the last year;
- how much does cleaning the data change the answer.

The questions follow DataCamp's "Exploring the Bitcoin Cryptocurrency Market" (clean the data, compare Bitcoin with the other currencies). The data is real, not a course file, and the page says plainly what it does and does not cover.

Build log: https://mrrishit909.github.io/projects/bitcoin-market-share/

## Data

Coin Metrics community data, through its free API (https://community-api.coinmetrics.io/v4): the metric `CapMrktCurUSD` for every asset that has it, on each month end from 2013-01-31 to 2026-04-30. Free for non-commercial use under CC BY-NC 4.0; attribution: Coin Metrics (coinmetrics.io).
Market capitalisation here is price times the current supply, which counts supply that is locked or in escrow. 160 responses give 10,885 rows for 135 assets; `download.py` fetches them (about 4 minutes) and the table is committed, with its checksum.

```
./venv/bin/pip install pandas numpy matplotlib certifi      # in a venv
./venv/bin/python download.py    # data/market_caps.csv
./venv/bin/python analyze.py     # results/*
./venv/bin/python check.py
./venv/bin/python charts.py
```

## Steps

1. **Download** the cross-section on each month end.
2. **Audit:** duplicates, caps of zero, how many assets are reported at each year end, and the asset ids with an underscore (copies of an asset on one blockchain).
3. **Clean,** on each date, in this order: drop rows with a cap of zero or less; drop wrapped, migrated or staked claims on another tracked asset (wbtc, hbtc, renbtc, weth, wnxm, lend, susde, sdai); sum the three Avalanche chains into one asset;
   drop a chain-specific copy (usdt_eth, usdc_trx, ...) if the whole asset is reported that day, and otherwise sum the copies into one asset named by the part before the underscore. `results/cleaning.csv` lists every asset a rule touched.
4. **Measure:** on each date the shares of Bitcoin, Ether, stablecoins (a named list) and tokenized gold, the shares of the five and ten largest, and the effective number of assets (1 divided by the sum of squared shares); the top ten on four dates; and the twelve-month change in value of the 15 largest today.
5. **Check.** `check.py` recomputes 2,394 numbers in plain Python straight from the raw table, re-implementing the cleaning rules with dicts and loops: the audit, what each rule did, every date's shares and concentration measures, the top tens, the movers and the extremes.
   Changing the wrapped list, the copy rule or the top-five cut makes it fail.
6. **Charts.**

## Results

- **Bitcoin's share has swung between 29% and 87%, and is 65% now.** Among the cleaned tracked assets it is 93.9% at the end of 2013 (2 assets), 33.0% at the end of 2017 (53 assets), 43.3% at the end of 2021 (99) and 65.0% on 30 April 2026 (86). With at least 10 assets reported, the lowest is 28.7% in
  January 2018 and the highest 86.8% in November 2015; it is below half in 45 of the 135 such months.
- **Cleaning matters.** On 30 April 2026 the uncleaned table sums to 2.61 trillion dollars with Bitcoin at 58.5%; cleaned it is 2.35 trillion and 65.0%, because copies of Tether and USD Coin on other chains, and wrapped Bitcoin and Ether, were counted twice.
- **What else is in it.** Ether peaked at 24.0% in June 2017 and is 11.7% now. Stablecoins went from 0.4% in January 2018 to a peak of 19.7% in December 2022 and are 12.0% now; tokenized gold is 0.2%.
- **Concentrated, and more so.** The five largest hold 93.8% of the tracked value now, the ten largest 96.4%; the effective number of assets is 2.24, down from 6.14 in January 2018.
- **The cast changes.** December 2014 (9 assets): Bitcoin 62.7%, XRP 35.1%, Litecoin 1.4%. December 2017 (53): Bitcoin 33.0%, XRP 28.0%, Ether 10.1%, Bitcoin Cash 5.7%, Stellar 5.2%. December 2021 (99): Bitcoin 43.3%, Ether 21.5%, XRP 4.1%, Tether 4.1%, Cronos 2.8%.
  April 2026 (86): Bitcoin 65.0%, Ether 11.7%, Tether 8.2%, XRP 5.8%, USD Coin 3.1%.
- **A year of change.** From April 2025 to April 2026 the value of Bitcoin fell 18%, Ether rose 27%, Tether 27% and USD Coin 24%; XRP fell 38%, Stellar 42%, Dogecoin 36%, Cardano 63% and Shiba Inu 53%; Monero rose 38% and Zcash 910%.

## Not done, and caveats

- This is the market Coin Metrics tracks, not the whole market: Solana, the Tron coin and Toncoin are not in it, and BNB appears in only 21 months (2017-07 to 2019-03), so "Bitcoin's share" is a share of these assets. The universe grows from 2 assets in 2013 to about 100, so early shares are high partly because little else was tracked.
- Value is price times the current supply, so supply that is locked or in escrow is counted. That makes XRP look much larger in 2014 and 2017 than a circulating-supply measure would; XRP's 35.1% and 28.0% above are on this definition.
- The cleaning lists (wrapped claims, stablecoins, tokenized gold) are my classification, and which copies count as the same asset is a judgement; other choices would move the shares by a few points. They are all in the code and in `results/cleaning.csv`.
- Month-end snapshots only, in a market that moves a lot inside a month. Market value is not liquidity or the money invested, and nothing here says what any asset is worth.
- Free for non-commercial use only (CC BY-NC 4.0); this is a portfolio project.
