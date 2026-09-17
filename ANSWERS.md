# Pricing Refactor Regression - Answers

## Q1. Naive `v2_total != v1_total` count?
**16000 / 20000** (4000 exactly equal).

Why useless (1-2 sentences): almost every order differs by 1-2 cents from floating-point reordering (`median abs_diff = 0.01, 75% = 0.02`), so this count mixes harmless noise + intentional books change + real bug into one number.

Evidence from `analyze.py`:
- `total rows: 20000, q1_naive_nonzero_count: 16000`
- `abs_diff describe: 50% 0.01, 75% 0.02, max 34.98, mean 1.40` — median tiny but mean large = two populations mixed.

## Q2. Genuine regression count and conditions?
**985 orders.**

Shared conditions: **all** satisfy:
- `category == fragile`
- `express == True`
- `coupon` = either empty (772) or SAVE10 (213) — coupon does not matter.

Verification:
- `abs_diff > 1.0 & category != books` = 985.
- Threshold-independent: `>0.02, >0.05, >0.10, >1.00, >5.00` all give 985 non-books (bug min 5.08, noise max 0.02).
- `fragile True total in file = 985` = 100% of that combo broken. Zero `fragile False >0.02`, zero other categories `>1.0`.
- Bins: `<=0.02: 14144 (noise), 0.02-1.00: 2191 (655 small-books + 1536 exact 0.02), >1.00: 3665 (2680 big-books + 985 bug)`.

## Q3. Total overcharged amount?
**19779.14 dollars overcharged (v2 - v1 sum).**

All 985 diffs positive (min 5.08, mean 20.08, max 34.98). Exact Decimal sum = 19779.14, no undercharge.

## Q4. Baseline average for clean orders?
**Mean abs_diff = 0.00988265306122449 (~$0.01).**

Baseline = NOT bug AND NOT books = `20000 - 3335 - 985 = 15680` rows.
`mean 0.00988, median 0.01, max 0.02, min 0.00`.

Justification: clean moves 1 cent, bug moves $5-$35 (min 5.08). 2000x gap proves Q2 is distinct pattern, not "everything a little different".

## Q5. Bonus: likely code bug?
Express surcharge (`$5 base + $0.10/km`) is added **twice** for fragile orders only.

Evidence (`analyze.py` Q5 section):
- `fragile exp=False v1: 2.6*w + 0.05*d`
- `fragile exp=True v1: 2.6*w + 0.15*d + 5` → normal express = `+0.10*d + $5`
- `bug diff empty: 0.09999*d + 5.003` = same express fee again
- `bug diff SAVE10: 0.09001*d + 4.498` = same x0.9 → coupon discounts after duplication

Plain English: refactored code likely adds express fee inside `if fragile:` branch and again in generic `if express:` block (copy-paste), so `fragile+express` double-charges distance premium and base fee.

## Investigation process
- Started with naive `!=` count (16000) and `abs_diff.describe()` to see median 0.01 vs max 34.98.
- Binned `abs_diff` into `<=0.02 / 0.02-1.0 / >1.0` to separate noise vs dollars.
- Dead end: threshold 0.05 alone still mixed small-weight books (0.08-1.0) — had to explicitly exclude `category==books`.
- Dead end: `groupby(category,express,coupon)` showed only 213 SAVE10, hid 772 empty because pandas drops NaN — fixed with `fillna("(empty)")`.
- Checked weight correlation 0.01 (no) vs distance correlation 0.99 (yes) to point at distance fee.
- Verified threshold-independence (0.02 to 5.00 all give 985) and 100% fragile-True broken.
- Reverse-engineered v1 linear fit per category/express to get `w/d/base` rates, then fit bug diff vs distance to find double express.
- Used Decimal sum for exact money (19779.14) to avoid float error.
- Computed baseline 15680 mean 0.00988 to prove separation.
