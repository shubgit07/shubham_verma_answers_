# Pricing Refactor Regression

Finds genuine pricing regression in `pricing_diff.csv` (v1 old vs v2 new), excluding intentional `books` rate change and 1-2 cent floating-point noise.

## Results
- Q1 naive `v2 != v1`: **16000 / 20000**
- Q2 genuine bug: **985** orders, all `category=fragile + express=True` (772 empty coupon + 213 SAVE10)
- Q3 total overcharge: **19779.14**
- Q4 baseline (not bug, not books, n=15680): **mean abs_diff 0.00988265, max 0.02**
- Q5 likely bug: express surcharge (`$5 + $0.10/km`) added **twice** for fragile only (SAVE10 version x0.9)

See `ANSWERS.md` for full Q1-Q5 answers with evidence.
See `answers.json` for auto-check numbers.
See `analyze.py` for reproduction : pandas is used.

## Reproduce
```powershell
# place pricing_diff.csv next to analyze.py
python analyze.py
```
