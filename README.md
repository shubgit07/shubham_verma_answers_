# Pricing Refactor Regression — InfoLion AI

Finds genuine pricing regression in `pricing_diff.csv` (v1 old vs v2 new), excluding intentional `books` rate change and 1-2 cent floating-point noise.

## Results
- Q1 naive `v2 != v1`: **16000 / 20000**
- Q2 genuine bug: **985** orders, all `category=fragile + express=True` (772 empty coupon + 213 SAVE10)
- Q3 total overcharge: **19779.14**
- Q4 baseline (not bug, not books, n=15680): **mean abs_diff 0.00988265, max 0.02**
- Q5 likely bug: express surcharge (`$5 + $0.10/km`) added **twice** for fragile only (SAVE10 version x0.9)

See `ANSWERS.md` for full Q1-Q5 answers with evidence.
See `answers.json` for auto-check numbers.
See `analyze.py` for reproduction (pandas only).

## Reproduce
```powershell
# place pricing_diff.csv next to analyze.py (csv not submitted per spec)
python analyze.py
```

## Investigation (short)
- Naive count + `abs_diff.describe()` (median 0.01 vs max 34.98) showed mixed populations.
- Binned `<=0.02 / 0.02-1.0 / >1.0`: 14144 noise, 2191 (655 small-books + 1536 exact 0.02), 3665 (2680 big-books + 985 bug).
- Dead end: threshold alone still mixed small books — had to exclude `books` explicitly.
- Dead end: `groupby` hid empty coupon (pandas drops NaN) — fixed with `fillna`.
- Threshold check 0.02 to 5.00 all give 985; bug min 5.08 vs noise max 0.02.
- Grouped suspects: 100% `fragile+express`, 0 elsewhere.
- Decimal sum for exact money; baseline mean to prove separation.
- Linear fit v1 (`2.6*w+0.05*d` vs `2.6*w+0.15*d+5`) and bug diff (`0.10*d+5`) revealed double express.

## Submit contents
- `ANSWERS.md`
- `answers.json`
- `analyze.py`
- `README.md` (this file)
