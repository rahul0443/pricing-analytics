# 📊 Contact Lens Pricing & Promotion Analytics

### [🔗 Live Dashboard →](https://rahul0443.github.io/pricing-analytics)

An end-to-end pricing analytics project modeled on CooperVision's product portfolio, U.S. distributor network, and rebate programs. Built to demonstrate pricing analytics capabilities for the Strategic Pricing team.

> **All data is synthetic.** Product names, distributor names, and pricing tiers are modeled on publicly available information. No real CooperVision financials are used.

---

## 🎯 What This Project Does

Simulates the data infrastructure and analytics a pricing analyst works with daily:

- **52,000 transactions** across 15 SKUs, 9 distributors, 7 rebate campaigns
- **Star schema data model** (fact + dimension tables) designed for scalable reporting
- **10 production SQL queries** for KPIs, pricing matrices, promo ROI, and concentration analysis
- **Python analysis pipeline** generating automated summary reports
- **Interactive dashboard** with 5 tabs — hosted live via GitHub Pages

---

## 🏗 Project Structure

```
├── index.html                  ← Interactive dashboard (GitHub Pages)
├── 01_data_generation.py       ← Synthetic data generation (52K transactions)
├── 02_sql_analysis.sql         ← 10 production-grade SQL queries
├── 03_python_analysis.py       ← Python analysis pipeline + reporting
│
├── data/                       ← Generated datasets
│   ├── fact_transactions.csv   ← 52,000 transaction records
│   ├── dim_products.csv        ← 15 SKUs (MyDay, Biofinity, clariti, MiSight, Avaira, Proclear)
│   ├── dim_distributors.csv    ← 9 authorized distributors (ABB Optical, Walman, Henry Schein, etc.)
│   ├── dim_promotions.csv      ← 7 rebate campaigns
│   ├── dim_contracts.csv       ← Distributor contract terms
│   └── dim_competitors.csv     ← 12 competitor products (J&J, Alcon, Bausch+Lomb)
│
├── outputs/                    ← Analysis results
│   ├── quarterly_kpi_summary.csv
│   ├── product_family_analysis.csv
│   ├── distributor_scorecard.csv
│   ├── promotion_roi.csv
│   ├── pricing_recommendations.csv
│   └── monthly_trend.csv
│
└── README.md
```

---

## 📈 Key Analyses

| Analysis | Description | Tools |
|---|---|---|
| **Quarterly KPIs** | Revenue, ASP, discount depth, margin, rebate spend by quarter | SQL, Python |
| **Product Pricing Matrix** | List vs net vs competitor benchmark for every SKU | SQL, Dashboard |
| **Distributor Scorecard** | Volume share, price index, contract status, HHI concentration | SQL, Python |
| **Promotion ROI** | Rebate spend vs incremental revenue per campaign | SQL, Dashboard |
| **Pricing Recommendations** | Price increase opportunities with estimated $ impact | Python, Dashboard |

---

## 💡 Key Findings

1. **MyDay sphere: 9% below competitor pricing** → $70K revenue opportunity from a 3-5% increase
2. **clariti 1 day: 39% gap to competitor average** → largest pricing headroom in the portfolio
3. **Avaira Trial promo: 0.9x ROI** → rebate cost exceeds incremental revenue, recommend discontinuing
4. **ABB Optical: 34% volume share** → HHI = 2,126 (moderate concentration risk)
5. **MiSight: 23% rebate redemption** → lowest rate, pediatric channel needs simpler digital flow

---

## 🛠 How to Run

```bash
# Generate synthetic data
python 01_data_generation.py

# Run analysis pipeline
python 03_python_analysis.py

# Open dashboard
open index.html
```

SQL queries in `02_sql_analysis.sql` can be run against the CSVs loaded into any SQL database.

---

## 🧰 Skills Demonstrated

**Data Engineering** — Synthetic data generation, dimensional modeling (star schema), ETL design  
**SQL** — Window functions, CTEs, conditional aggregation, HHI index, price indexing  
**Python** — pandas, NumPy, automated reporting, data validation  
**Visualization** — Interactive Chart.js dashboard, KPI cards, comparison charts  
**Business Analytics** — Pricing strategy, promotion ROI, competitor benchmarking, distributor concentration  
**Domain Knowledge** — Contact lens industry, distributor channel economics, rebate mechanics

---

## 👤 Author

**Rahul Muddhapuram**  
MS Data Science, Analytics & Engineering — Arizona State University  
[LinkedIn](https://linkedin.com/in/rahulmuddhapuram) · [GitHub](https://github.com/rahul0443) · rmuddhap@asu.edu
