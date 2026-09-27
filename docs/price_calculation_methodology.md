# Price Calculation Methodology (`FAIR_PRICE_ENGINE_V1`)

SIH 26090 — Mathematical Formulas & Deterministic Logic

---

## 1. Mathematical Arithmetic Standards

All monetary calculations in `FAIR_PRICE_ENGINE_V1` use Python's `decimal.Decimal` module:
- Arithmetic: Arbitrary precision base-10 mathematics.
- Rounding: `ROUND_HALF_UP` to 2 decimal places (`Decimal('0.01')`).
- Zero Floating-Point Error: Avoids IEEE 754 rounding imprecisions (e.g., `0.1 + 0.2` is strictly `0.30`).

---

## 2. Step 1: Production Cost Build-Up

### A. Raw Materials
$$\text{Line Item Total}_i = (\text{Quantity}_i \times \text{Unit Cost}_i)$$
$$\text{Total Material Cost} = \sum_{i=1}^{M} \text{Line Item Total}_i$$

### B. Skilled Labor
- **Hourly Mode (`HOURLY_RATE`)**:
  $$\text{Total Labor Cost} = \text{Production Hours} \times \text{Hourly Wage Rate}$$
- **Stated Total Mode (`TOTAL_STATED`)**:
  $$\text{Total Labor Cost} = \text{Artisan Stated Labor Cost}$$

### C. Direct Packaging & Transport
$$\text{Direct Logistics} = \text{Packaging Cost} + \text{Transport Cost} + \text{Other Incidental Costs}$$

### D. Overhead Allocation
- **`PER_PRODUCT` Basis**:
  $$\text{Allocated Overhead Batch} = \text{Overhead Cost} \times \text{Batch Quantity}$$
- **`PER_BATCH` or `MONTHLY_ALLOCATION` Basis**:
  $$\text{Allocated Overhead Batch} = \text{Overhead Cost}$$

### E. Total Batch & Unit Production Cost
$$\text{Total Production Cost} = \text{Total Material Cost} + \text{Total Labor Cost} + \text{Direct Logistics} + \text{Allocated Overhead Batch}$$

$$\text{Unit Production Cost} = \frac{\text{Total Production Cost}}{\text{Batch Quantity}}$$

---

## 3. Step 2: Cost-Plus Margin Baseline

$$\text{Cost Baseline Price} = \text{Unit Production Cost} \times \left(1 + \frac{\text{Desired Margin Percentage}}{100}\right)$$

---

## 4. Step 3: Order Statistics on Market Observations

When valid, comparable observations $N \ge 3$ exist, observations are sorted:
$$P_0 \le P_1 \le \dots \le P_{N-1}$$

- **Minimum**: $P_{\min} = P_0$
- **Maximum**: $P_{\max} = P_{N-1}$
- **Median ($P_{50}$)**:
  - If $N$ is odd: $P_{N // 2}$
  - If $N$ is even: $\frac{P_{N // 2 - 1} + P_{N // 2}}{2}$
- **Interquartile Range ($Q_1, Q_3$)**:
  - $Q_1 = \text{percentile}(0.25)$
  - $Q_3 = \text{percentile}(0.75)$

---

## 5. Step 4: Fair Price Synthesis

### Case A: Insufficient Market Evidence ($N < 3$)
When $N < 3$:
- $\text{Status} = \text{INSUFFICIENT\_MARKET\_EVIDENCE}$
- $\text{Analysis Type} = \text{COST\_ONLY\_BASELINE}$
- $\text{Floor Price} = \text{Unit Production Cost}$
- $\text{Recommended Price} = \text{Cost Baseline Price}$
- $\text{Price Range} = [\text{Cost Baseline Price}, \text{Cost Baseline Price} \times 1.15]$ (clearly identified as margin projection, not market range).

### Case B: Sufficient Market Evidence ($N \ge 3$)
When $N \ge 3$:
- $\text{Status} = \text{SUFFICIENT\_MARKET\_EVIDENCE}$
- $\text{Analysis Type} = \text{FAIR\_PRICE\_ANALYSIS}$
- **Floor Price**:
  $$\text{Floor Price} = \max(\text{Unit Production Cost}, \min(\text{Cost Baseline Price}, Q_1))$$
  *Safety Guarantee: Guarantees the artisan is never recommended a floor price below their unit production cost.*
- **Recommended Price**:
  $$\text{Recommended Price} = \max(\text{Cost Baseline Price}, P_{\text{median}})$$
- **Fair Retail Range**:
  $$\text{Fair Range Low} = \max(\text{Cost Baseline Price}, Q_1)$$
  $$\text{Fair Range High} = \max(\text{Cost Baseline Price} \times 1.25, Q_3)$$
