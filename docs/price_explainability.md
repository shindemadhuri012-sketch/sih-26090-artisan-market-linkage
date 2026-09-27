# Price Explainability & Traceability Framework

SIH 26090 — Transparent Economic Justification

---

## 1. Principles of Explainability

The platform guarantees that no price recommendation is ever output without an explicit, verifiable explanation of:
1. **Inputs Used**: Full audit trail of materials, hours, and costs.
2. **Provenance Distinction**: Explicit differentiation between `ARTISAN_PROVIDED`, `SOURCE_BACKED`, and `CALCULATED`.
3. **Mathematical Steps**: Exact numerical equations showing how intermediate and final values were produced.
4. **Comparability Justification**: Explaining why specific market observations were included or why market evidence was declared insufficient.
5. **Limitations**: Disclaiming economic assumptions and sales guarantees.

---

## 2. Structured Explanation Steps Format

Every `PriceAnalysis` record generates an ordered array of explanation steps (`explanation_steps`):

### Step 1: Input Data Sources & Provenance
Itemizes the origin of all cost inputs:
> *"Cost inputs are ARTISAN_PROVIDED. Materials count: 2. Labor method: HOURLY_RATE."*

### Step 2: Production Cost Build-Up
Provides the full direct and indirect build-up:
> *"Direct costs = Materials (₹2850.00) + Labor (₹2000.00 for 16.0 hrs @ ₹125.00/hr) + Packaging (₹150.00) + Transport (₹200.00) + Overhead (₹300.00) = Total ₹5500.00 for 1 unit(s). Unit cost = ₹5500.00."*

### Step 3: Cost-Plus Margin Baseline
Explains how the artisan's desired margin was applied:
> *"Applying stated artisan profit margin of 20.00% to unit production cost ₹5500.00 yields a Cost-Based Price Baseline of ₹6600.00."*

### Step 4: Market Evidence Assessment
- **If $N \ge 3$**:
  > *"Evaluated 4 comparable documented market observations from [Tribes India / TRIFED, CCIC]. Observed Median is ₹5500.00 with Interquartile Range (IQR) of ₹4800.00 – ₹6400.00."*
- **If $N < 3$**:
  > *"Found 0 comparable observations. Minimum requirement is 3 observations. Market evidence is insufficient to calculate a defensible market range without fabricating data."*

### Step 5: Fair Price Recommendation
Explains how the floor and recommended range were synthesized:
> *"Recommended Floor Price is ₹4500.00 (ensuring artisan never sells below unit production cost ₹4500.00). Suggested Fair Retail Range is ₹5625.00 – ₹7031.25, with a Recommended Fair Retail Price of ₹5625.00."*

### Step 6: Current Price Risk Warning (Contextual)
- **If Current Price $<$ Unit Cost**:
  > *"WARNING: Your current selling price (₹3800.00) is ₹700.00 below your unit production cost (₹4500.00). You are incurring a loss on each unit produced."*
- **If Current Price $<$ Recommended**:
  > *"Your current price (₹4800.00) is ₹825.00 below the recommended fair price (₹5625.00). Your work has room for higher value realization."*
