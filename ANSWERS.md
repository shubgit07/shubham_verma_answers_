# Pricing Refactor Regression - Answers

## Q1. Count rows where v2_total != v1_total?
16000 out of 20000.

This is not useful because most of those differ by only 1-2 cents from floating-point reordering (median |v2-v1| = $0.01). It mixes noise + intentional books change + real bug into one number.

## Q2. Orders affected by genuine regression? Shared conditions?
985 orders.

All 985 share:
- category = fragile
- express = True
- coupon = any (772 empty, 213 SAVE10)

Method: `|v2-v1| > 1.00 AND category != books`. Bins are `<=0.02: 14144, 0.02-1.00: 2191, >1.00: 3665 (2680 books + 985 bug)`. Threshold-proof: >0.02 to >5.00 all give 985 (noise max $0.02, bug min $5.08). Total fragile+express rows in file is also 985, so 100% hit, 0 elsewhere.

## Q3. Total overcharged?
19779.14 (overcharge).

Sum of `v2-v1` over the 985. All positive, min 5.08, mean 20.08, max 34.98. Exact Decimal sum.

## Q4. Average difference for NOT bug AND NOT books?
0.00988265306122449 (~$0.01).

Baseline = 20000 - 3335 books - 985 bug = 15680 rows. Mean |v2-v1| = 0.00988, max 0.02.

This shows Q2 is distinct: clean moves a penny, bug moves $5.08-$34.98. Not "everything a little different."

## Q5. Bonus: likely code bug?
Express fee is added twice for fragile orders only.

Normal express is `+$5 + $0.10/km` (fragile False: 2.6*w+0.05*d, fragile True: 2.6*w+0.15*d+5). Bug diff is `0.10*d+5` again (SAVE10: 0.09*d+4.49, same x0.9 after discount). Likely the fragile branch adds express and the general express block adds it again.

## Investigation
- Naive `!=` count gave 16000; `abs diff` median 0.01 vs max 34.98 showed noise vs bug mixed.
- Binned by size to separate cents vs dollars.
- Dead end: size cutoff alone kept small books ($0.08-$1.00), had to exclude by category.
- Dead end: groupby hid 772 empty coupons (pandas drops NaN), fixed with fillna.
- Correlation ruled out weight (0.01), confirmed distance (0.99).
- Verified 0.02-5.00 thresholds all give 985.
- Fit v1 rates and bug slope to identify double express.
- Decimal sum for exact $19779.14; baseline mean for proof.
