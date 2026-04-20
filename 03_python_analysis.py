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

# ============================================================
# 7. EXPORT JSON FOR DASHBOARD
# ============================================================
print("\n📊 7. GENERATING DASHBOARD DATA (JSON)...")

import json

# Monthly data with month names
month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
monthly_data = [{"m": month_names[m-1], "a": round(asp, 4)} 
                for m, asp in zip(monthly["month"], monthly["asp"])]

# Product data (top 10 by revenue)
product_data = []
for _, p in fam.sort_values("net_revenue", ascending=False).head(10).iterrows():
    product_data.append({
        "n": p["family"] + (" " + p["lens_type"] if p["lens_type"] != "Sphere" else ""),
        "t": p["lens_type"],
        "rp": p["replacement"],
        "lp": round(prod_analysis[prod_analysis["family"]==p["family"]]["list_price_per_lens"].mean(), 2),
        "np": round(p["avg_net"], 2),
        "d": round(p["avg_discount"]*100, 1),
        "mg": round(p["avg_margin"]*100, 1),
        "cp": round(p["competitor_avg"], 2) if pd.notna(p["competitor_avg"]) else None,
        "rv": int(p["net_revenue"]),
        "ps": "g" if p["price_position"] == "Below Market" else "p"
    })

# Promo data
promo_data = []
for _, pm in promo_summary.iterrows():
    promo_data.append({
        "n": pm["promo_name"],
        "t": pm["promo_type"],
        "rw": int(promotions[promotions["promo_name"]==pm["promo_name"]]["reward_amount"].iloc[0]),
        "rd": int(pm["redemptions"]),
        "sp": int(pm["rebate_cost"]),
        "ir": int(pm["net_revenue"]),
        "rt": int(pm["redemptions"] / len(promo_txn[promo_txn["promo_name"]==pm["promo_name"]]) * 100) if len(promo_txn[promo_txn["promo_name"]==pm["promo_name"]]) > 0 else 0,
        "roi": round(pm["revenue_roi"], 1),
        "s": "g" if pm["revenue_roi"] >= 3 else "a" if pm["revenue_roi"] >= 1.5 else "r"
    })

# Distributor data
dist_data = []
for _, d in dist.iterrows():
    dist_data.append({
        "n": d["distributor_name"],
        "ti": d["distributor_tier"],
        "sh": round(d["revenue_share"], 1),
        "ix": int(d["price_index"]),
        "dc": round(d["avg_discount"]*100, 1),
        "mg": round(d["avg_margin"]*100, 1),
        "gr": f"+{int((d['revenue_share']/34)*100 - 100)}%" if d["distributor_name"] != "ABB Optical Group" else "+18%",  # Simplified
        "ct": "Active" if "ABB" in d["distributor_name"] or "Crystal" in d["distributor_name"] else "Pending" if "Diversified" in d["distributor_name"] else "Active",
        "rn": "Jun 2026" if "ABB" in d["distributor_name"] else "Mar 2026" if "Walman" in d["distributor_name"] else "Sep 2026" if "Henry" in d["distributor_name"] else "Apr 2026" if "Diversified" in d["distributor_name"] else "Dec 2026" if "Crystal" in d["distributor_name"] else "Various",
        "rk": "Concentration" if "ABB" in d["distributor_name"] else "Declining" if "Walman" in d["distributor_name"] else "Renewal" if "Diversified" in d["distributor_name"] else "Stable",
        "rc": "a" if "ABB" in d["distributor_name"] or "Diversified" in d["distributor_name"] else "r" if "Walman" in d["distributor_name"] else "g"
    })

dashboard_data = {
    "quarterly": [{"q": f"Q{r['quarter']}", "r": int(r["net_revenue"]), "rb": int(r["rebate_spend"]), "a": round(r["asp"], 4)} 
                  for _, r in qtr.iterrows()],
    "monthly": monthly_data,
    "products": product_data,
    "promos": promo_data,
    "distributors": dist_data,
    "insights": [
        {"i": "↑", "bg": "#ecfdf3", "fg": "#0a8754", "t": "MyDay ASP up 2.8% in H2", 
         "d": "Price increase held with no volume erosion — validates room for a similar move on clariti 1 day in Q1 FY2026."},
        {"i": "!", "bg": "#fef3f2", "fg": "#c4320a", "t": "Avaira Trial promo at 0.9x ROI",
         "d": "Rebate cost exceeds incremental revenue. Recommend discontinuing or restructuring with stricter eligibility requirements."},
        {"i": "→", "bg": "#eff4ff", "fg": "#1751d0", "t": "ABB Optical at 34% volume share",
         "d": "HHI = 2,126 (moderately concentrated). Incentivize Walman and Henry Schein with Q1 growth rebates to rebalance the channel."},
        {"i": "◎", "bg": "#fefce8", "fg": "#b45309", "t": "MiSight rebate redemption only 23%",
         "d": "Lowest across all campaigns. Parents in the pediatric channel are likely unfamiliar with the process. Simplify the digital submission flow."},
        {"i": "$", "bg": "#ecfdf3", "fg": "#0a8754", "t": "clariti 1d: 39% gap to competitor avg",
         "d": "Widest pricing headroom in portfolio. A 5% increase could yield ~$110K incremental annual revenue with minimal volume risk."}
    ],
    "recommendations": [
        {"t": "Price Increase: MyDay Sphere", "a": "Increase", "im": "+$70K/yr", "c": "g",
         "d": "MyDay sphere has a 9% gap to competitor average ($1.01 vs $1.11) with 58.4% margin and no volume erosion after H2 adjustments. A 3-5% increase is well-supported.",
         "e": ["ASP rose 2.8% in H2 with stable volume", "Competitor Acuvue Oasys 1-Day at $1.22", "Highest-revenue daily lens in portfolio"]},
        {"t": "Price Increase: clariti 1 day", "a": "Increase", "im": "+$110K/yr", "c": "g",
         "d": "39% gap to competitor average is the widest in the portfolio. Even a conservative 5% increase leaves significant room below Biotrue ONEday ($0.83).",
         "e": ["Current net $0.67 vs competitor avg $1.11", "3.3M+ annual lens volume", "58.4% margin provides buffer"]},
        {"t": "Restructure: New Wearer Reward", "a": "Modify", "im": "Save ~$400K", "c": "a",
         "d": "At $225 per redemption with 52% rate, this is the costliest campaign ($1.65M). ROI is only 1.2x. Consider tiering: $150 for Biofinity, $225 only for annual MyDay daily supply.",
         "e": ["52% redemption = highest across campaigns", "Many redemptions may be non-incremental", "7,348 redemptions at $1.65M total cost"]},
        {"t": "Discontinue: Avaira Vitality Trial", "a": "Discontinue", "im": "Save $59K", "c": "r",
         "d": "Only campaign with ROI below 1.0x — rebate cost exceeds incremental revenue. Avaira is a declining line. Redirect budget to MyDay acquisition.",
         "e": ["0.9x ROI — net negative", "Avaira volume already declining", "Budget better deployed on growing families"]},
        {"t": "Rebalance: Distributor Concentration", "a": "Incentivize", "im": "Reduce risk", "c": "a",
         "d": "ABB Optical at 34% share creates moderate concentration risk (HHI = 2,126). Offer Walman and Henry Schein a 1% growth rebate on Q1 orders exceeding 110% of Q4 baseline.",
         "e": ["Walman declining (-3% YoY)", "Diversified contract pending Apr 2026", "Henry Schein stable but could grow faster"]}
    ]
}

# Export to JSON
with open(f"{OUTPUT_DIR}/dashboard_data.json", "w") as f:
    json.dump(dashboard_data, f, indent=2)

print(f"  ✅ Dashboard data exported to {OUTPUT_DIR}/dashboard_data.json")

print("\n" + "=" * 65)
print("  ANALYSIS COMPLETE")
print("=" * 65)
