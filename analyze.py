"""Pricing Refactor Regression - reproduction script.
Requires: pricing_diff.csv in same folder (not submitted), pandas or stdlib only.
Run: python analyze.py
"""
import pandas as pd
import numpy as np

df = pd.read_csv("pricing_diff.csv")
df["diff"] = df["v2_total"] - df["v1_total"]
df["abs_diff"] = df["diff"].abs()
df["coupon_f"] = df["coupon"].fillna("(empty)")

# Q1: naive count
q1 = int((df["v2_total"] != df["v1_total"]).sum())
print(f"Q1 naive nonzero: {q1} / {len(df)}")

# Bins: noise vs dollars
print("<=0.02:", int((df["abs_diff"] <= 0.02).sum()))
print("0.02-1.00:", int(((df["abs_diff"] > 0.02) & (df["abs_diff"] <= 1.0)).sum()))
print(">1.00:", int((df["abs_diff"] > 1.0).sum()))

# Q2: suspects = big diff, exclude books intentional change
suspects = df[(df["abs_diff"] > 1.0) & (df["category"] != "books")]
print(f"Q2 suspects: {len(suspects)}")
print(suspects.groupby(["category", "express", "coupon_f"]).size().to_string())

is_bug = (df["category"] == "fragile") & (df["express"] == True)
print(f"bug count: {int(is_bug.sum())}, min abs_diff: {df.loc[is_bug, 'abs_diff'].min()}")

# Q3: total overcharge
q3 = float(df.loc[is_bug, "diff"].sum())
print(f"Q3 total overcharge: {q3:.2f}")

# Q4: baseline = not bug and not books
is_baseline = (~is_bug) & (df["category"] != "books")
q4 = float(df.loc[is_baseline, "abs_diff"].mean())
print(f"Q4 baseline rows: {int(is_baseline.sum())}, mean abs_diff: {q4}")
print(df.loc[is_baseline, "abs_diff"].describe().to_string())

# Q5: reverse-engineer v1 formula + bug slope
for exp in [False, True]:
    sub = df[(df["category"] == "fragile") & (df["express"] == exp) & (df["coupon"].isna())]
    A = np.vstack([sub["weight_kg"].values, sub["distance_km"].values, np.ones(len(sub))]).T
    w, d, b = np.linalg.lstsq(A, sub["v1_total"].values, rcond=None)[0]
    print(f"fragile exp={exp} v1: w={w:.4f} d={d:.4f} base={b:.4f}")

bug = df[is_bug]
for c, sub in bug.groupby(bug["coupon"].fillna("(empty)")):
    x = sub["distance_km"].values
    y = sub["diff"].values
    A = np.vstack([x, np.ones(len(x))]).T
    s, i = np.linalg.lstsq(A, y, rcond=None)[0]
    print(f"coupon={c} diff slope={s:.5f} intercept={i:.3f} n={len(sub)}")
