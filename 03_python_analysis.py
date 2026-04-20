"""
CooperVision Pricing & Promotion Analytics — Python Analysis
=============================================================
Runs the core analytics on the generated transaction data,
produces summary tables, and validates insights.

Author: Rahul Muddhapuram
Date:   April 2026
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = "/home/claude/coopervision-project/data"
OUTPUT_DIR = "/home/claude/coopervision-project/outputs"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load data
txn = pd.read_csv(f"{DATA_DIR}/fact_transactions.csv", parse_dates=["transaction_date"])
products = pd.read_csv(f"{DATA_DIR}/dim_products.csv")
distributors = pd.read_csv(f"{DATA_DIR}/dim_distributors.csv")
promotions = pd.read_csv(f"{DATA_DIR}/dim_promotions.csv")
contracts = pd.read_csv(f"{DATA_DIR}/dim_contracts.csv")
competitors = pd.read_csv(f"{DATA_DIR}/dim_competitors.csv")

print("=" * 65)
print("  COOPERVISION PRICING ANALYTICS — SUMMARY REPORT")
print("  FY2025 Full Year | Americas Commercial | Strategic Pricing")
print("=" * 65)


# ============================================================
# 1. QUARTERLY KPI SUMMARY
# ============================================================
print("\n\n📊 1. QUARTERLY KPI SUMMARY")
print("-" * 65)

qtr = txn.groupby("quarter").agg(
    transactions=("transaction_id", "count"),
    total_lenses=("total_lenses", "sum"),
    net_revenue=("net_revenue", "sum"),
    gross_margin=("gross_margin", "sum"),
    avg_discount=("discount_pct", "mean"),
    avg_margin=("margin_pct", "mean"),
    rebate_spend=("rebate_amount", "sum"),
).reset_index()

qtr["asp"] = qtr["net_revenue"] / qtr["total_lenses"]
qtr["rebate_pct_rev"] = qtr["rebate_spend"] / qtr["net_revenue"] * 100

for _, r in qtr.iterrows():
    print(f"\n  Q{int(r['quarter'])}:")
    print(f"    Net Revenue:      ${r['net_revenue']:>12,.0f}")
    print(f"    Avg Net Price:    ${r['asp']:>12.4f} /lens")
    print(f"    Avg Discount:     {r['avg_discount']*100:>11.1f}%")
    print(f"    Gross Margin:     {r['avg_margin']*100:>11.1f}%")
    print(f"    Rebate Spend:     ${r['rebate_spend']:>12,.0f} ({r['rebate_pct_rev']:.1f}% of rev)")
    print(f"    Volume:           {r['total_lenses']:>12,.0f} lenses")


# ============================================================
# 2. PRODUCT FAMILY ANALYSIS
# ============================================================
print("\n\n📊 2. PRODUCT FAMILY PRICING ANALYSIS")
print("-" * 65)

# Competitor benchmarks
comp_bench = competitors.groupby(["lens_type", "replacement"])["est_wholesale_price"].mean().reset_index()
comp_bench.columns = ["lens_type", "replacement", "competitor_avg"]

fam = txn.groupby(["family", "lens_type", "replacement"]).agg(
    net_revenue=("net_revenue", "sum"),
    volume=("total_lenses", "sum"),
    avg_list=("list_price_per_lens", "mean"),
    avg_net=("net_price_per_lens", "mean"),
    avg_discount=("discount_pct", "mean"),
    avg_margin=("margin_pct", "mean"),
).reset_index()

fam = fam.merge(comp_bench, on=["lens_type", "replacement"], how="left")
fam["price_position"] = fam.apply(
    lambda r: "Below Market" if pd.notna(r["competitor_avg"]) and r["avg_net"] < r["competitor_avg"] * 0.97
    else ("Above Market" if pd.notna(r["competitor_avg"]) and r["avg_net"] > r["competitor_avg"] * 1.03
    else "At Market / No Comp"), axis=1
)
fam = fam.sort_values("net_revenue", ascending=False)

print(f"\n  {'Family':<12} {'Type':<12} {'Net Rev':>10} {'ASP':>7} {'Disc%':>6} {'Marg%':>6} {'Comp':>7} {'Position':<14}")
print("  " + "-" * 80)
for _, r in fam.iterrows():
    comp_str = f"${r['competitor_avg']:.4f}" if pd.notna(r["competitor_avg"]) else "   —"
    print(f"  {r['family']:<12} {r['lens_type']:<12} ${r['net_revenue']:>9,.0f} ${r['avg_net']:.4f} {r['avg_discount']*100:>5.1f}% {r['avg_margin']*100:>5.1f}% {comp_str} {r['price_position']:<14}")


# ============================================================
# 3. DISTRIBUTOR SCORECARD
# ============================================================
print("\n\n📊 3. DISTRIBUTOR SCORECARD")
print("-" * 65)

portfolio_asp = txn["net_revenue"].sum() / txn["total_lenses"].sum()

dist = txn.groupby(["distributor_name", "distributor_tier"]).agg(
    net_revenue=("net_revenue", "sum"),
    volume=("total_lenses", "sum"),
    avg_discount=("discount_pct", "mean"),
    avg_margin=("margin_pct", "mean"),
    txn_count=("transaction_id", "count"),
).reset_index()

dist["revenue_share"] = dist["net_revenue"] / dist["net_revenue"].sum() * 100
dist["asp"] = dist["net_revenue"] / dist["volume"]
dist["price_index"] = (dist["asp"] / portfolio_asp * 100).round(0)
dist = dist.sort_values("net_revenue", ascending=False)

print(f"\n  {'Distributor':<25} {'Tier':<7} {'Rev Share':>9} {'ASP':>7} {'Index':>6} {'Disc%':>6} {'Marg%':>6}")
print("  " + "-" * 72)
for _, r in dist.iterrows():
    print(f"  {r['distributor_name']:<25} {r['distributor_tier']:<7} {r['revenue_share']:>8.1f}% ${r['asp']:.4f} {r['price_index']:>5.0f} {r['avg_discount']*100:>5.1f}% {r['avg_margin']*100:>5.1f}%")

# HHI Concentration
hhi = (dist["revenue_share"] ** 2).sum()
print(f"\n  HHI Index: {hhi:.0f} — {'HIGHLY CONCENTRATED' if hhi > 2500 else 'MODERATELY CONCENTRATED' if hhi > 1500 else 'COMPETITIVE'}")
print(f"  Top distributor share: {dist['revenue_share'].max():.1f}%")


# ============================================================
# 4. PROMOTION ROI
# ============================================================
print("\n\n📊 4. PROMOTION ROI ANALYSIS")
print("-" * 65)

promo_txn = txn[txn["rebate_amount"] > 0].copy()
promo_txn = promo_txn.merge(promotions[["promo_id", "promo_name", "promo_type", "reward_amount"]],
                             left_on="rebate_promo_id", right_on="promo_id", how="left")

promo_summary = promo_txn.groupby(["promo_name", "promo_type"]).agg(
    redemptions=("transaction_id", "count"),
    net_revenue=("net_revenue", "sum"),
    rebate_cost=("rebate_amount", "sum"),
    gross_margin=("gross_margin", "sum"),
).reset_index()

promo_summary["revenue_roi"] = promo_summary["net_revenue"] / promo_summary["rebate_cost"]
promo_summary["net_roi"] = (promo_summary["gross_margin"] - promo_summary["rebate_cost"]) / promo_summary["rebate_cost"]
promo_summary = promo_summary.sort_values("net_roi", ascending=False)

print(f"\n  {'Campaign':<25} {'Type':<12} {'Redemptions':>11} {'Rebate Cost':>12} {'Net Rev':>10} {'ROI':>5}")
print("  " + "-" * 80)
for _, r in promo_summary.iterrows():
    print(f"  {r['promo_name']:<25} {r['promo_type']:<12} {r['redemptions']:>11,} ${r['rebate_cost']:>11,.0f} ${r['net_revenue']:>9,.0f} {r['revenue_roi']:>4.1f}x")


# ============================================================
# 5. PRICE INCREASE OPPORTUNITY ANALYSIS
# ============================================================
print("\n\n📊 5. PRICING RECOMMENDATIONS")
print("-" * 65)

prod_analysis = txn.merge(products[["product_id", "product_name", "family", "lens_type", "replacement"]],
                           on="product_id", suffixes=("", "_prod"))
prod_summary = prod_analysis.groupby(["product_name", "family", "lens_type", "replacement"]).agg(
    avg_net=("net_price_per_lens", "mean"),
    avg_margin=("margin_pct", "mean"),
    volume=("total_lenses", "sum"),
    net_revenue=("net_revenue", "sum"),
).reset_index()

prod_summary = prod_summary.merge(comp_bench, on=["lens_type", "replacement"], how="left")
prod_summary["gap_pct"] = ((prod_summary["competitor_avg"] - prod_summary["avg_net"])
                            / prod_summary["competitor_avg"] * 100).round(1)
prod_summary["est_2pct_increase"] = (prod_summary["net_revenue"] * 0.02).round(0)

for _, r in prod_summary.sort_values("est_2pct_increase", ascending=False).head(10).iterrows():
    if pd.notna(r["competitor_avg"]) and r["avg_net"] < r["competitor_avg"] * 0.95 and r["avg_margin"] > 0.55:
        rec = "✅ PRICE INCREASE OPPORTUNITY"
    elif pd.notna(r["competitor_avg"]) and r["avg_net"] > r["competitor_avg"] * 1.05:
        rec = "⚠️  ABOVE MARKET — MONITOR"
    elif r["avg_margin"] < 0.45:
        rec = "🔴 MARGIN PRESSURE"
    else:
        rec = "— HOLD PRICING"

    gap_str = f"{r['gap_pct']:>+.1f}%" if pd.notna(r["gap_pct"]) else "  N/A"
    print(f"\n  {r['product_name']}")
    print(f"    Net Price: ${r['avg_net']:.4f}  |  Comp Avg: {'${:.4f}'.format(r['competitor_avg']) if pd.notna(r['competitor_avg']) else 'N/A':>8}  |  Gap: {gap_str}")
    print(f"    Margin: {r['avg_margin']*100:.1f}%  |  Volume: {r['volume']:,.0f}  |  2% Uplift: ${r['est_2pct_increase']:,.0f}")
    print(f"    → {rec}")


# ============================================================
# 6. EXPORT SUMMARY TABLES
# ============================================================
print("\n\n📊 6. EXPORTING ANALYSIS TABLES...")

qtr.to_csv(f"{OUTPUT_DIR}/quarterly_kpi_summary.csv", index=False)
fam.to_csv(f"{OUTPUT_DIR}/product_family_analysis.csv", index=False)
dist.to_csv(f"{OUTPUT_DIR}/distributor_scorecard.csv", index=False)
promo_summary.to_csv(f"{OUTPUT_DIR}/promotion_roi.csv", index=False)
prod_summary.to_csv(f"{OUTPUT_DIR}/pricing_recommendations.csv", index=False)

# Monthly trend for dashboard
monthly = txn.groupby("month").agg(
    net_revenue=("net_revenue", "sum"),
    volume=("total_lenses", "sum"),
    avg_discount=("discount_pct", "mean"),
    avg_margin=("margin_pct", "mean"),
    rebate_spend=("rebate_amount", "sum"),
).reset_index()
monthly["asp"] = monthly["net_revenue"] / monthly["volume"]
monthly.to_csv(f"{OUTPUT_DIR}/monthly_trend.csv", index=False)

print(f"  ✅ 6 summary tables exported to {OUTPUT_DIR}/")

print("\n" + "=" * 65)
print("  ANALYSIS COMPLETE")
print("=" * 65)
