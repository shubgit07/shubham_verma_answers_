# Pricing Refactor Regression - Answers

## Q1. If you just count rows where v2 != v1, how many?
**Answer: 16000 out of 20000 (4000 are exactly equal, `q1_naive_nonzero_count = 16000`).**

Why this is not useful (in 2 sentences): Most of those 16000 differ by only 1-2 cents because the refactor changed addition order, so floating-point wobble (`abs_diff = |v2-v1|`) shows up everywhere. That count lumps harmless noise together with the intentional books price change and the real bug, so it tells us nothing about how many customers were actually hurt.

Technical check (`analyze.py`): `abs_diff.describe()` gives median $0.01, 75% $0.02, mean $1.40, max $34.98. Tiny median vs huge mean/max = two populations mixed (cents vs dollars). Code: `(df["v2_total"] != df["v1_total"]).sum()` — verified with both string compare and Decimal compare, both 16000.

## Q2. How many orders have a genuine bug, and what do they share?
**Answer: 985 orders (`q2_affected_count = 985`, `q2_affected_category = "fragile"`).**

They all share the same inputs — this is an exact rule, no exceptions:
- `category == "fragile"`
- `express == True` (boolean True)
- `coupon` is irrelevant: 772 had empty/NaN coupon, 213 had `SAVE10`, both broken

How I got there, technically: I defined `abs_diff = |v2-v1|`, binned it as `<=0.02: 14144 (noise), 0.02-1.00: 2191 (655 small-weight books with 0.08-1.00 + 1536 exact 0.02 noise), >1.00: 3665 (2680 big-books + 985 suspects)`. Then `suspects = (abs_diff > 1.00) & (category != "books")` leaves 985. Threshold-independence proof: `>0.02, >0.05, >0.10, >1.00, >5.00` all give 985 non-books, because noise max is $0.02 and bug min is $5.08 — clean gap. Completeness proof: total `fragile+express True` rows in file is also 985, so 100% of that combo is hit; zero `fragile False >0.02` and zero other categories `>1.00`. Pandas note: `groupby(category,express,coupon)` drops NaN coupons by default and showed only 213, so I used `fillna("(empty)")` to reveal 772+213=985.

## Q3. How much were customers overcharged in total?
**Answer: $19779.14 overcharged (`q3_total_overcharge = 19779.14`).**

I summed `diff = v2-v1` over just those 985: `df.loc[is_bug, "diff"].sum()` where `is_bug = (category=="fragile") & (express==True)`. Stats: min +$5.08, mean +$20.08, max +$34.98, all 985 positive, so pure overcharge. Technical: used Python `Decimal` sum for exact cents (float sum also 19779.14, but Decimal proves no binary rounding error).

## Q4. Sanity check: average difference for clean orders?
**Answer: $0.00988265306122449, about 1 cent (`q4_baseline_mean_abs_diff`).**

Clean defined as NOT bug AND NOT books: `20000 - 3335 books - 985 bug = 15680` rows (`is_baseline = ~is_bug & (category!="books")`). Technical: `mean(|v2-v1|) = 154.96/15680 = 0.00988`, with `describe(): mean 0.00988, std 0.00705, min 0.00, 25% 0.00, 50% 0.01, 75% 0.01, max 0.02`.

Why this matters: clean moves a penny (max 2 cents) while bug moves $5.08-$34.98. That ~2000x gap proves Q2 is a real distinct pattern and not just “everything is a little different.”

## Q5. Bonus: what do you think the code bug is?
The refactored code adds the express surcharge twice, only for fragile parcels.

Technical derivation (`analyze.py` Q5 with `numpy.linalg.lstsq`):
- Fit `v1 = w*weight + d*distance + base` on no-coupon rows: `fragile exp=False: 2.6000*w + 0.0500*d + 0.00`, `fragile exp=True: 2.6000*w + 0.1500*d + 5.00`. So normal express premium = `+0.10/km + $5 base`.
- Fit `diff vs distance` on bug: empty coupon `slope 0.09999 intercept 5.003 (n=772)`, SAVE10 `slope 0.09001 intercept 4.498 (n=213)`. Empty matches express premium exactly; SAVE10 is same x0.9.
- Correlations: `weight-diff 0.01 (none), distance-diff 0.99 (almost perfect)`, confirming per-km fee duplication. SAVE10 x0.9 shows coupon discount applied after duplication (whole inflated total discounted).

Plain English: likely the fragile branch kept its own `+5 +0.10*distance` express addition and the generic `if express:` block added it again during refactor (copy-paste/merge error). Only triggers when `category==fragile and express==True`.

## How I investigated (including dead ends)
- Started with naive `(v2 != v1).sum()` = 16000 and `abs_diff.describe()`; tiny median ($0.01) vs huge max ($34.98) told me noise and bug were mixed.
- Binned `abs_diff` into `<=0.02 / 0.02-1.00 / >1.00` to separate cents (noise) vs dollars (books+bug).
- Dead end: dollar cutoff alone still mixed 655 small-weight books ($0.08-$1.00) — learned to exclude by `category!="books"`, not by size.
- Dead end: `groupby(category,express,coupon)` showed only 213 SAVE10 and hid 772 empties because pandas drops NaN by default — fixed with `coupon.fillna("(empty)")`, full 985 appeared.
- Tested correlations: `weight-diff ~0.01` ruled out per-kg change, `distance-diff ~0.99` pointed at per-km express fee.
- Verified threshold-independence: `>0.02, >0.05, >0.10, >1.00, >5.00` all give 985; bug min $5.08 vs noise max $0.02 = clean separation.
- Reverse-engineered `v1` with least-squares per `category/express` to learn rates (`w/d/base`), then fit `diff vs distance` to match double express.
- Recomputed money with `Decimal` for exact cents ($19779.14) and baseline mean on 15680 rows ($0.00988) to prove distinctness.
- Final cross-check: 100% of `fragile+express` broken, 0% elsewhere; all diffs positive.
