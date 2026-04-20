"""
CooperVision Pricing & Promotion Analytics — Data Generation
=============================================================
Generates synthetic transactional pricing data modeled on CooperVision's
actual product portfolio, authorized distributor network, and rebate programs.

Author: Rahul Muddhapuram
Date:   April 2026

NOTE: All data is synthetic. No real CooperVision financials are used.
Product names, distributor names, and pricing tiers are modeled on
publicly available information (retail pricing, rebate offers, product catalogs).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

# ============================================================
# 1. PRODUCT MASTER TABLE
# ============================================================
# Modeled on CooperVision's actual product families with realistic
# wholesale list pricing (estimated from public retail/rebate data)

products = pd.DataFrame([
    # product_id, product_name, family, lens_type, replacement, list_price_per_lens, cogs_per_lens
    ("SKU-001", "MyDay 90pk",             "MyDay",     "Sphere",    "Daily",    1.17, 0.42),
    ("SKU-002", "MyDay Toric 90pk",       "MyDay",     "Toric",     "Daily",    1.42, 0.51),
    ("SKU-003", "MyDay Multifocal 90pk",  "MyDay",     "Multifocal","Daily",    1.58, 0.57),
    ("SKU-004", "Biofinity 6pk",          "Biofinity", "Sphere",    "Monthly",  6.17, 2.10),
    ("SKU-005", "Biofinity Toric 6pk",    "Biofinity", "Toric",     "Monthly",  7.50, 2.55),
    ("SKU-006", "Biofinity Multifocal 6pk","Biofinity","Multifocal","Monthly",  9.17, 3.12),
    ("SKU-007", "Biofinity XR Toric 6pk", "Biofinity", "Toric XR",  "Monthly", 8.33, 2.83),
    ("SKU-008", "clariti 1 day 90pk",     "clariti",   "Sphere",    "Daily",    0.78, 0.28),
    ("SKU-009", "clariti 1 day Toric 90pk","clariti",  "Toric",     "Daily",    0.95, 0.34),
    ("SKU-010", "clariti 1 day MF 90pk",  "clariti",   "Multifocal","Daily",    1.06, 0.38),
    ("SKU-011", "MiSight 1 day 90pk",     "MiSight",   "Myopia Mgmt","Daily",  1.89, 0.68),
    ("SKU-012", "Avaira Vitality 6pk",    "Avaira",    "Sphere",    "Bi-weekly",3.33, 1.13),
    ("SKU-013", "Avaira Vitality Toric 6pk","Avaira",  "Toric",     "Bi-weekly",4.17, 1.42),
    ("SKU-014", "Proclear 1 day 90pk",    "Proclear",  "Sphere",    "Daily",    0.89, 0.32),
    ("SKU-015", "Proclear Multifocal 6pk","Proclear",  "Multifocal","Monthly",  8.33, 2.83),
], columns=["product_id","product_name","family","lens_type","replacement","list_price_per_lens","cogs_per_lens"])


# ============================================================
# 2. DISTRIBUTOR MASTER TABLE
# ============================================================
# Based on CooperVision's publicly listed U.S. Authorized Distributors

distributors = pd.DataFrame([
    ("DIST-01", "ABB Optical Group",       "Tier 1", "Southeast",  0.34),
    ("DIST-02", "Walman Optical",          "Tier 1", "Midwest",    0.22),
    ("DIST-03", "Henry Schein",            "Tier 1", "Northeast",  0.18),
    ("DIST-04", "Diversified Ophthalmics", "Tier 2", "South",      0.11),
    ("DIST-05", "Crystal Vision",          "Tier 2", "West",       0.05),
    ("DIST-06", "Firestone Optics",        "Tier 2", "Central",    0.04),
    ("DIST-07", "Nassau Lens Co",          "Tier 2", "Northeast",  0.03),
    ("DIST-08", "The Newton Group",        "Tier 3", "Southeast",  0.02),
    ("DIST-09", "Precision Optical",       "Tier 3", "West",       0.01),
], columns=["distributor_id","distributor_name","tier","region","market_share"])

# Discount tiers: Tier 1 gets better pricing
discount_tiers = {"Tier 1": (0.13, 0.18), "Tier 2": (0.10, 0.15), "Tier 3": (0.08, 0.12)}


# ============================================================
# 3. PROMOTION / REBATE MASTER TABLE
# ============================================================
# Modeled on CooperVision's actual rebate programs (publicly advertised)

promotions = pd.DataFrame([
    ("PROMO-01", "New Wearer Reward",     ["Biofinity","MyDay"],   "New Fit",    225, "2025-07-01","2025-12-31"),
    ("PROMO-02", "Repurchase Reward",     ["Biofinity","MyDay"],   "Repurchase", 200, "2025-07-01","2025-12-31"),
    ("PROMO-03", "Annual Supply Bonus",   ["clariti","MyDay"],     "Annual",     100, "2025-10-01","2025-12-31"),
    ("PROMO-04", "MiSight New Fit",       ["MiSight"],             "New Fit",     150, "2025-09-01","2025-12-31"),
    ("PROMO-05", "Biofinity XR Launch",   ["Biofinity"],           "New Fit",      50, "2025-10-01","2025-12-31"),
    ("PROMO-06", "clariti Switch",        ["clariti"],             "Switch",      75, "2025-08-01","2025-11-30"),
    ("PROMO-07", "Avaira Vitality Trial", ["Avaira"],              "New Fit",      50, "2025-07-01","2025-12-31"),
], columns=["promo_id","promo_name","eligible_families","promo_type","reward_amount","start_date","end_date"])

promotions["start_date"] = pd.to_datetime(promotions["start_date"])
promotions["end_date"] = pd.to_datetime(promotions["end_date"])


# ============================================================
# 4. GENERATE TRANSACTION DATA
# ============================================================
# ~50,000 transactions over 12 months (Jan-Dec 2025)

print("Generating 50,000+ transactions...")

n_transactions = 52000
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 12, 31)

records = []
for i in range(n_transactions):
    txn_id = f"TXN-{i+1:06d}"

    # Date — weighted toward Q3/Q4 (back-to-school, holiday = higher contact lens sales)
    month_weights = [6, 6, 7, 7, 8, 8, 9, 10, 10, 11, 11, 12]  # relative
    month = np.random.choice(range(1,13), p=np.array(month_weights)/sum(month_weights))
    day = np.random.randint(1, 29)
    txn_date = datetime(2025, month, day)

    # Product — weighted by market share (dailies dominate)
    prod_weights = [15, 6, 3, 12, 8, 5, 2, 14, 5, 3, 4, 5, 3, 8, 3]
    prod_idx = np.random.choice(len(products), p=np.array(prod_weights)/sum(prod_weights))
    prod = products.iloc[prod_idx]

    # Distributor — weighted by market share
    dist_probs = distributors["market_share"].values
    dist_idx = np.random.choice(len(distributors), p=dist_probs)
    dist = distributors.iloc[dist_idx]

    # Quantity (boxes) — daily lenses sold in larger quantities
    if prod["replacement"] == "Daily":
        qty = np.random.choice([2, 4, 6, 8], p=[0.15, 0.40, 0.30, 0.15])
    else:
        qty = np.random.choice([1, 2, 4], p=[0.25, 0.50, 0.25])

    # Discount — based on distributor tier + some randomness
    tier = dist["tier"]
    disc_min, disc_max = discount_tiers[tier]
    discount_pct = np.random.uniform(disc_min, disc_max)

    # Seasonal price adjustments (slight increase in H2)
    if month >= 7:
        price_adj = 1.0 + np.random.uniform(0.01, 0.03)
    else:
        price_adj = 1.0

    list_price = prod["list_price_per_lens"] * price_adj
    net_price = list_price * (1 - discount_pct)
    cogs = prod["cogs_per_lens"]

    # Revenue and margin
    lenses_per_box = 90 if prod["replacement"] == "Daily" else 6
    total_lenses = qty * lenses_per_box
    gross_revenue = list_price * total_lenses
    net_revenue = net_price * total_lenses
    total_cogs = cogs * total_lenses
    gross_margin = net_revenue - total_cogs
    margin_pct = gross_margin / net_revenue if net_revenue > 0 else 0

    # Rebate — check if eligible
    rebate_amount = 0
    rebate_promo_id = None
    for _, promo in promotions.iterrows():
        if (prod["family"] in promo["eligible_families"]
            and promo["start_date"] <= pd.Timestamp(txn_date) <= promo["end_date"]):
            # Redemption probability varies by promo type
            redemption_rates = {"New Fit": 0.45, "Repurchase": 0.52, "Annual": 0.40, "Switch": 0.35}
            rate = redemption_rates.get(promo["promo_type"], 0.30)
            if np.random.random() < rate:
                rebate_amount = promo["reward_amount"]
                rebate_promo_id = promo["promo_id"]
            break  # only one promo per transaction

    records.append({
        "transaction_id": txn_id,
        "transaction_date": txn_date.strftime("%Y-%m-%d"),
        "product_id": prod["product_id"],
        "product_name": prod["product_name"],
        "family": prod["family"],
        "lens_type": prod["lens_type"],
        "replacement": prod["replacement"],
        "distributor_id": dist["distributor_id"],
        "distributor_name": dist["distributor_name"],
        "distributor_tier": dist["tier"],
        "region": dist["region"],
        "quantity_boxes": qty,
        "lenses_per_box": lenses_per_box,
        "total_lenses": total_lenses,
        "list_price_per_lens": round(list_price, 4),
        "discount_pct": round(discount_pct, 4),
        "net_price_per_lens": round(net_price, 4),
        "cogs_per_lens": round(cogs, 4),
        "gross_revenue": round(gross_revenue, 2),
        "net_revenue": round(net_revenue, 2),
        "total_cogs": round(total_cogs, 2),
        "gross_margin": round(gross_margin, 2),
        "margin_pct": round(margin_pct, 4),
        "rebate_amount": rebate_amount,
        "rebate_promo_id": rebate_promo_id,
    })

transactions = pd.DataFrame(records)

# Add derived columns
transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"])
transactions["month"] = transactions["transaction_date"].dt.month
transactions["quarter"] = transactions["transaction_date"].dt.quarter
transactions["month_name"] = transactions["transaction_date"].dt.strftime("%b")


# ============================================================
# 5. CONTRACT TABLE
# ============================================================

contracts = pd.DataFrame([
    ("CTR-001", "DIST-01", "ABB Optical Group",       "2024-07-01", "2026-06-30", "Active",          0.155, 5000000),
    ("CTR-002", "DIST-02", "Walman Optical",          "2024-04-01", "2026-03-31", "Active",          0.145, 3200000),
    ("CTR-003", "DIST-03", "Henry Schein",            "2024-10-01", "2026-09-30", "Active",          0.140, 2800000),
    ("CTR-004", "DIST-04", "Diversified Ophthalmics", "2024-05-01", "2026-04-30", "Renewal Pending", 0.125, 1500000),
    ("CTR-005", "DIST-05", "Crystal Vision",          "2025-01-01", "2026-12-31", "Active",          0.115, 700000),
    ("CTR-006", "DIST-06", "Firestone Optics",        "2025-03-01", "2027-02-28", "Active",          0.110, 500000),
    ("CTR-007", "DIST-07", "Nassau Lens Co",          "2024-09-01", "2025-08-31", "Expired",         0.105, 400000),
    ("CTR-008", "DIST-08", "The Newton Group",        "2025-06-01", "2027-05-31", "Active",          0.100, 250000),
    ("CTR-009", "DIST-09", "Precision Optical",       "2025-01-01", "2026-12-31", "Active",          0.095, 150000),
], columns=["contract_id","distributor_id","distributor_name","start_date","end_date",
            "status","contracted_discount","annual_volume_commitment"])

contracts["start_date"] = pd.to_datetime(contracts["start_date"])
contracts["end_date"] = pd.to_datetime(contracts["end_date"])


# ============================================================
# 6. COMPETITOR PRICING TABLE
# ============================================================

competitors = pd.DataFrame([
    ("Acuvue Oasys 1-Day",    "J&J Vision",       "Sphere",    "Daily",   1.22),
    ("Acuvue Oasys 1-Day Ast","J&J Vision",       "Toric",     "Daily",   1.45),
    ("Acuvue Moist MF",       "J&J Vision",       "Multifocal","Daily",   1.50),
    ("Dailies Total1",        "Alcon",             "Sphere",    "Daily",   1.28),
    ("Dailies Total1 Toric",  "Alcon",             "Toric",     "Daily",   1.52),
    ("Air Optix plus HG",     "Alcon",             "Sphere",    "Monthly", 5.83),
    ("Air Optix for Ast",     "Alcon",             "Toric",     "Monthly", 7.17),
    ("Air Optix MF",          "Alcon",             "Multifocal","Monthly", 8.83),
    ("Biotrue ONEday",        "Bausch + Lomb",     "Sphere",    "Daily",   0.83),
    ("Biotrue ONEday Ast",    "Bausch + Lomb",     "Toric",     "Daily",   1.00),
    ("Ultra",                 "Bausch + Lomb",     "Sphere",    "Monthly", 5.50),
    ("Ultra for Astigmatism", "Bausch + Lomb",     "Toric",     "Monthly", 6.67),
], columns=["product_name","manufacturer","lens_type","replacement","est_wholesale_price"])


# ============================================================
# 7. SAVE ALL DATA
# ============================================================

output_dir = "/home/claude/coopervision-project/data"
os.makedirs(output_dir, exist_ok=True)

products.to_csv(f"{output_dir}/dim_products.csv", index=False)
distributors.to_csv(f"{output_dir}/dim_distributors.csv", index=False)
promotions.to_csv(f"{output_dir}/dim_promotions.csv", index=False)
contracts.to_csv(f"{output_dir}/dim_contracts.csv", index=False)
competitors.to_csv(f"{output_dir}/dim_competitors.csv", index=False)
transactions.to_csv(f"{output_dir}/fact_transactions.csv", index=False)

print(f"\n✅ Data generation complete!")
print(f"   Transactions: {len(transactions):,} rows")
print(f"   Products:     {len(products)} SKUs across {products['family'].nunique()} families")
print(f"   Distributors: {len(distributors)} authorized distributors")
print(f"   Promotions:   {len(promotions)} active campaigns")
print(f"   Contracts:    {len(contracts)} distributor contracts")
print(f"   Competitors:  {len(competitors)} benchmark products")
print(f"\n   Files saved to: {output_dir}/")

# Quick validation
print(f"\n📊 Quick Validation:")
print(f"   Total Net Revenue:     ${transactions['net_revenue'].sum():,.0f}")
print(f"   Avg Net Price/Lens:    ${transactions['net_revenue'].sum() / transactions['total_lenses'].sum():.4f}")
print(f"   Avg Margin:            {transactions['margin_pct'].mean():.1%}")
print(f"   Total Rebate Payout:   ${transactions['rebate_amount'].sum():,.0f}")
print(f"   Rebate Transactions:   {(transactions['rebate_amount'] > 0).sum():,} ({(transactions['rebate_amount'] > 0).mean():.1%})")
