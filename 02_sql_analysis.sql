-- ============================================================
-- CooperVision Pricing & Promotion Analytics — SQL Analysis
-- ============================================================
-- Author: Rahul Muddhapuram
-- Date:   April 2026
--
-- This script demonstrates the SQL analysis layer for a
-- contact lens pricing analytics system. Written for
-- SQL Server / T-SQL syntax, adaptable to PostgreSQL.
--
-- Tables:  dim_products, dim_distributors, dim_promotions,
--          dim_contracts, dim_competitors, fact_transactions
-- ============================================================


-- ============================================================
-- 1. PRICING KPI SUMMARY BY QUARTER
-- ============================================================
-- Core metrics the Strategic Pricing team tracks

SELECT
    quarter,
    COUNT(DISTINCT transaction_id)          AS total_transactions,
    SUM(total_lenses)                       AS total_lenses_sold,
    ROUND(SUM(net_revenue), 0)              AS total_net_revenue,
    ROUND(SUM(gross_revenue), 0)            AS total_gross_revenue,
    ROUND(SUM(net_revenue) / NULLIF(SUM(total_lenses), 0), 4)
                                            AS avg_net_price_per_lens,
    ROUND(AVG(discount_pct) * 100, 1)       AS avg_discount_pct,
    ROUND(SUM(gross_margin), 0)             AS total_gross_margin,
    ROUND(AVG(margin_pct) * 100, 1)         AS avg_margin_pct,
    ROUND(SUM(rebate_amount), 0)            AS total_rebate_payout,
    ROUND(SUM(CASE WHEN rebate_amount > 0 THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 1)                      AS rebate_redemption_pct
FROM fact_transactions
GROUP BY quarter
ORDER BY quarter;


-- ============================================================
-- 2. PRODUCT FAMILY PRICING ANALYSIS
-- ============================================================
-- Shows list-to-net price gap and margin by product family
-- This is the analysis an intern would build for price reviews

SELECT
    p.family,
    p.lens_type,
    p.replacement,
    COUNT(t.transaction_id)                 AS txn_count,
    SUM(t.total_lenses)                     AS total_lenses,
    ROUND(SUM(t.net_revenue), 0)            AS net_revenue,
    ROUND(AVG(t.list_price_per_lens), 4)    AS avg_list_price,
    ROUND(AVG(t.net_price_per_lens), 4)     AS avg_net_price,
    ROUND(AVG(t.discount_pct) * 100, 1)     AS avg_discount_pct,
    ROUND(AVG(t.margin_pct) * 100, 1)       AS avg_margin_pct,
    -- Price position vs competitors
    c.avg_competitor_price,
    CASE
        WHEN AVG(t.net_price_per_lens) < c.avg_competitor_price * 0.97
            THEN 'Below Market'
        WHEN AVG(t.net_price_per_lens) > c.avg_competitor_price * 1.03
            THEN 'Above Market'
        ELSE 'At Market'
    END AS price_position
FROM fact_transactions t
JOIN dim_products p ON t.product_id = p.product_id
LEFT JOIN (
    SELECT lens_type, replacement,
           ROUND(AVG(est_wholesale_price), 4) AS avg_competitor_price
    FROM dim_competitors
    GROUP BY lens_type, replacement
) c ON p.lens_type = c.lens_type AND p.replacement = c.replacement
GROUP BY p.family, p.lens_type, p.replacement,
         c.avg_competitor_price
ORDER BY net_revenue DESC;


-- ============================================================
-- 3. MONTHLY NET SELLING PRICE TREND
-- ============================================================
-- Tracks price realization over time — critical for measuring
-- whether price increases are holding or eroding

SELECT
    month,
    month_name,
    ROUND(SUM(net_revenue) / NULLIF(SUM(total_lenses), 0), 4)
                                            AS avg_net_price,
    ROUND(SUM(gross_revenue) / NULLIF(SUM(total_lenses), 0), 4)
                                            AS avg_list_price,
    ROUND((1 - SUM(net_revenue) / NULLIF(SUM(gross_revenue), 0)) * 100, 1)
                                            AS realized_discount_pct,
    SUM(total_lenses)                       AS volume,
    ROUND(SUM(net_revenue), 0)              AS net_revenue
FROM fact_transactions
GROUP BY month, month_name
ORDER BY month;


-- ============================================================
-- 4. DISTRIBUTOR PRICING SCORECARD
-- ============================================================
-- Used by the team to manage price consistency across channels
-- and prepare for contract renewal negotiations

SELECT
    d.distributor_name,
    d.tier,
    d.region,
    COUNT(t.transaction_id)                 AS txn_count,
    ROUND(SUM(t.net_revenue), 0)            AS net_revenue,
    ROUND(SUM(t.net_revenue) * 100.0
        / SUM(SUM(t.net_revenue)) OVER(), 1) AS revenue_share_pct,
    ROUND(AVG(t.discount_pct) * 100, 1)     AS avg_discount_pct,
    ROUND(AVG(t.net_price_per_lens), 4)     AS avg_net_price,
    -- Price index: 100 = portfolio average
    ROUND(AVG(t.net_price_per_lens)
        / (SUM(SUM(t.net_revenue)) OVER()
        / NULLIF(SUM(SUM(t.total_lenses)) OVER(), 0)) * 100, 0)
                                            AS net_price_index,
    ROUND(AVG(t.margin_pct) * 100, 1)       AS avg_margin_pct,
    -- Contract info
    ct.status                               AS contract_status,
    ct.end_date                             AS contract_end_date,
    ROUND(ct.contracted_discount * 100, 1)  AS contracted_discount_pct
FROM fact_transactions t
JOIN dim_distributors d ON t.distributor_id = d.distributor_id
LEFT JOIN dim_contracts ct ON d.distributor_id = ct.distributor_id
GROUP BY d.distributor_name, d.tier, d.region,
         ct.status, ct.end_date, ct.contracted_discount
ORDER BY net_revenue DESC;


-- ============================================================
-- 5. PROMOTION ROI ANALYSIS
-- ============================================================
-- Measures the return on rebate investment — key for deciding
-- which campaigns to renew, modify, or discontinue

SELECT
    pr.promo_name,
    pr.promo_type,
    pr.reward_amount                         AS reward_per_redemption,
    -- Transaction metrics during promo period
    COUNT(t.transaction_id)                  AS total_txns,
    SUM(CASE WHEN t.rebate_amount > 0 THEN 1 ELSE 0 END)
                                             AS redeemed_txns,
    ROUND(SUM(CASE WHEN t.rebate_amount > 0 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0), 1)            AS redemption_rate_pct,
    -- Financial impact
    ROUND(SUM(t.net_revenue), 0)             AS total_net_revenue,
    ROUND(SUM(t.rebate_amount), 0)           AS total_rebate_cost,
    ROUND(SUM(t.net_revenue)
        / NULLIF(SUM(t.rebate_amount), 0), 1) AS revenue_to_rebate_ratio,
    ROUND(SUM(t.gross_margin), 0)            AS gross_margin_after_cogs,
    ROUND((SUM(t.gross_margin) - SUM(t.rebate_amount))
        / NULLIF(SUM(t.rebate_amount), 0), 1) AS net_promo_roi
FROM fact_transactions t
JOIN dim_promotions pr
    ON t.rebate_promo_id = pr.promo_id
GROUP BY pr.promo_name, pr.promo_type, pr.reward_amount
ORDER BY net_promo_roi DESC;


-- ============================================================
-- 6. DISCOUNT DEPTH DISTRIBUTION
-- ============================================================
-- Identifies if discount discipline is being maintained
-- Flags transactions with excessive discounting

SELECT
    CASE
        WHEN discount_pct < 0.10 THEN '< 10%'
        WHEN discount_pct < 0.13 THEN '10-13%'
        WHEN discount_pct < 0.15 THEN '13-15%'
        WHEN discount_pct < 0.18 THEN '15-18%'
        ELSE '18%+'
    END AS discount_band,
    COUNT(*)                                 AS txn_count,
    ROUND(COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER(), 1)           AS pct_of_total,
    ROUND(SUM(net_revenue), 0)              AS net_revenue,
    ROUND(AVG(margin_pct) * 100, 1)         AS avg_margin_pct
FROM fact_transactions
GROUP BY
    CASE
        WHEN discount_pct < 0.10 THEN '< 10%'
        WHEN discount_pct < 0.13 THEN '10-13%'
        WHEN discount_pct < 0.15 THEN '13-15%'
        WHEN discount_pct < 0.18 THEN '15-18%'
        ELSE '18%+'
    END
ORDER BY discount_band;


-- ============================================================
-- 7. Q-OVER-Q GROWTH BY PRODUCT FAMILY
-- ============================================================
-- Quarter-over-quarter comparison for pricing reviews

WITH quarterly AS (
    SELECT
        family,
        quarter,
        ROUND(SUM(net_revenue), 0)           AS net_revenue,
        SUM(total_lenses)                    AS volume,
        ROUND(SUM(net_revenue)
            / NULLIF(SUM(total_lenses), 0), 4) AS asp
    FROM fact_transactions
    GROUP BY family, quarter
)
SELECT
    curr.family,
    curr.quarter                             AS current_quarter,
    curr.net_revenue                         AS curr_revenue,
    prev.net_revenue                         AS prev_revenue,
    ROUND((curr.net_revenue - prev.net_revenue) * 100.0
        / NULLIF(prev.net_revenue, 0), 1)    AS revenue_growth_pct,
    curr.asp                                AS curr_asp,
    prev.asp                                AS prev_asp,
    ROUND((curr.asp - prev.asp) * 100.0
        / NULLIF(prev.asp, 0), 1)            AS asp_change_pct,
    curr.volume                             AS curr_volume,
    ROUND((curr.volume - prev.volume) * 100.0
        / NULLIF(prev.volume, 0), 1)         AS volume_growth_pct
FROM quarterly curr
LEFT JOIN quarterly prev
    ON curr.family = prev.family
    AND curr.quarter = prev.quarter + 1
WHERE curr.quarter > 1
ORDER BY curr.family, curr.quarter;


-- ============================================================
-- 8. DISTRIBUTOR CONCENTRATION RISK
-- ============================================================
-- Herfindahl-Hirschman Index (HHI) for distributor concentration

WITH dist_shares AS (
    SELECT
        distributor_name,
        ROUND(SUM(net_revenue) * 100.0
            / SUM(SUM(net_revenue)) OVER(), 2) AS share_pct
    FROM fact_transactions
    GROUP BY distributor_name
)
SELECT
    ROUND(SUM(share_pct * share_pct), 0)     AS hhi_index,
    -- HHI > 2500 = highly concentrated
    -- HHI 1500-2500 = moderately concentrated
    -- HHI < 1500 = competitive
    CASE
        WHEN SUM(share_pct * share_pct) > 2500 THEN 'HIGHLY CONCENTRATED'
        WHEN SUM(share_pct * share_pct) > 1500 THEN 'MODERATELY CONCENTRATED'
        ELSE 'COMPETITIVE'
    END AS concentration_level,
    MAX(share_pct)                           AS largest_share_pct
FROM dist_shares;


-- ============================================================
-- 9. MiSight PRICING DEEP-DIVE
-- ============================================================
-- MiSight is CooperVision's flagship myopia management lens
-- No direct competitor — strategic pricing is critical

SELECT
    month_name,
    month,
    COUNT(transaction_id)                    AS txn_count,
    SUM(total_lenses)                       AS lenses_sold,
    ROUND(AVG(net_price_per_lens), 4)       AS avg_net_price,
    ROUND(AVG(discount_pct) * 100, 1)       AS avg_discount_pct,
    ROUND(AVG(margin_pct) * 100, 1)         AS avg_margin_pct,
    SUM(CASE WHEN rebate_amount > 0 THEN 1 ELSE 0 END)
                                            AS rebate_redemptions,
    ROUND(SUM(rebate_amount), 0)            AS total_rebate_cost,
    ROUND(SUM(net_revenue), 0)              AS net_revenue
FROM fact_transactions
WHERE family = 'MiSight'
GROUP BY month_name, month
ORDER BY month;


-- ============================================================
-- 10. ACTIONABLE PRICING RECOMMENDATIONS
-- ============================================================
-- Identifies products where price increases may be possible
-- (high margin + below market) vs. products under margin pressure

SELECT
    p.product_name,
    p.family,
    ROUND(AVG(t.net_price_per_lens), 4)     AS current_avg_net,
    c.avg_competitor_price,
    ROUND((c.avg_competitor_price - AVG(t.net_price_per_lens))
        / NULLIF(c.avg_competitor_price, 0) * 100, 1)
                                            AS gap_to_competitor_pct,
    ROUND(AVG(t.margin_pct) * 100, 1)       AS current_margin_pct,
    SUM(t.total_lenses)                     AS annual_volume,
    -- Estimated revenue impact of 2% price increase
    ROUND(SUM(t.net_revenue) * 0.02, 0)     AS est_revenue_from_2pct_increase,
    CASE
        WHEN AVG(t.net_price_per_lens) < c.avg_competitor_price * 0.95
            AND AVG(t.margin_pct) > 0.55
            THEN '✅ PRICE INCREASE OPPORTUNITY'
        WHEN AVG(t.net_price_per_lens) > c.avg_competitor_price * 1.05
            THEN '⚠️ ABOVE MARKET — MONITOR VOLUME'
        WHEN AVG(t.margin_pct) < 0.45
            THEN '🔴 MARGIN PRESSURE — REVIEW DISCOUNTS'
        ELSE '— HOLD CURRENT PRICING'
    END AS recommendation
FROM fact_transactions t
JOIN dim_products p ON t.product_id = p.product_id
LEFT JOIN (
    SELECT lens_type, replacement,
           ROUND(AVG(est_wholesale_price), 4) AS avg_competitor_price
    FROM dim_competitors
    GROUP BY lens_type, replacement
) c ON p.lens_type = c.lens_type AND p.replacement = c.replacement
GROUP BY p.product_name, p.family, c.avg_competitor_price
ORDER BY est_revenue_from_2pct_increase DESC;
