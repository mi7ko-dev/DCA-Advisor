# MVP Calculation Contract

## Numeric and currency rules

Persisted quantities, prices, FX rates, fees, weights, and monetary amounts are
canonical decimal strings: optional leading minus sign, digits, and an optional
fractional part. Exponents, leading plus signs, separators, and surrounding
whitespace are rejected. Runtime arithmetic uses `decimal.Decimal` with a local
precision of 36 digits. Outputs retain deterministic decimal values; Markdown
presentation rounds money and percentages to two decimal places without changing
structured results.

Every price must match its listing's trading currency. An instrument's economic
currency remains separate metadata and is not inferred from its ticker, exchange,
or trading currency.

For valuation in the investor's base currency, SteadyFolio uses the latest supplied
price whose date is not later than the valuation date. For FX, it compares the
latest eligible direct and inverse observations and uses the newer observation;
an equal-date tie prefers the direct orientation. Conflicting values for the same
listing or currency-pair orientation on the same date are rejected instead of
being resolved by input order. The source ID for each used price and FX rate is
retained. No triangulation, live lookup, or assumed one-to-one conversion occurs.
Missing prices or FX rates fail the calculation explicitly.

## Portfolio analysis

For holding quantity `q`, listing price `p`, and applicable FX multiplier `f`:

```text
base value = q * p * f
current weight = instrument base value / total portfolio base value
drift = current weight - approved target weight
```

Positive drift means overweight and negative drift means underweight. With a zero
portfolio value, current weights are zero and the result contains an explicit
warning rather than dividing by zero.

Target weights accepted within the schema tolerance are normalized to sum exactly
to one before valuation, drift, contribution budgeting, and expected-weight
calculations. This prevents a tolerated rounding residual from becoming unallocated
cash or inconsistent drift.

The current weighted annual fee rate is:

```text
sum(current weight * instrument annual fee rate)
```

Direct concentration reports the maximum instrument weight, instruments above 20%,
and the Herfindahl index `sum(weight^2)`. These are directly observable indicators,
not look-through fund exposure or a complete risk model.

## Simple DCA

For contribution `C` and approved target weight `t[i]`, the ideal cash budget is:

```text
budget[i] = C * t[i]
```

Each budget is executed independently under its listing and fee constraints. The
method does not react to current drift.

## Drift-aware DCA

The objective is to reduce current target gaps with new purchases only. It does not
sell or rewrite the approved allocation.

For current total `V`, contribution `C`, current instrument value `v[i]`, and target
weight `t[i]`:

```text
hypothetical post-contribution total = V + C
positive gap[i] = max(0, t[i] * (V + C) - v[i])
budget[i] = C * positive gap[i] / sum(positive gaps)
```

If all positive gaps are zero, target weights are used as the budget basis. This is
an explainable buy-only heuristic, not an efficient-frontier optimizer. A strongly
overweight position may remain overweight when one contribution cannot correct the
portfolio without selling.

## Trade execution constraints

The plan supports:

- whole or fractional shares;
- a positive quantity increment;
- a minimum trade value;
- fixed, variable, and minimum estimated trade fees.

A listing's fractional-trading and quantity-increment fields are hard exchange or
broker constraints. A planning override may tighten them but cannot enable
fractional trading where the listing forbids it or use an incompatible increment.
Whole-share round lots such as 10 shares remain 10-share increments; they are not
collapsed to one share.

For a positive purchase value `x`, the estimated fee is the greater of the minimum
fee and `fixed fee + variable rate * x`, rounded upward to the nearest cent. Quantity
is always rounded down to the permitted increment. A line that cannot meet its
minimum trade value remains unexecuted and its cash remains residual.

An allocation target with normalized weight zero is not a purchase candidate and
does not require a listing or market price merely to produce a zero trade.

The following invariant is exact in structured output:

```text
sum(purchase values) + sum(estimated fees) + residual cash = contribution
```

Overspending and negative purchase quantities are rejected.

## Expected post-contribution weights

Residual cash remains in the portfolio, while fees leave it. Therefore:

```text
expected post-contribution value = current value + contribution - fees
expected instrument weight = (current instrument value + purchase value)
                             / expected post-contribution value
remaining drift = expected instrument weight - approved target weight
```

The plan is a proposal. It does not create an actual transaction, mutate a holding,
or change an approved target.

Each plan ID includes a deterministic SHA-256 fingerprint of its calculation
version, approved allocation, analysis, market inputs, contribution amount,
constraints, and preferred listings. Reordering equivalent input collections does
not change the ID, while a plan-defining input change does.

## MVP limitations

- Existing cash balances are not modeled as holdings.
- FX conversion supports supplied direct or inverse pairs only.
- Fees are scenarios from supplied assumptions, not broker quotes.
- Direct concentration does not look through ETF holdings.
- Taxes, spreads, price movement, market impact, settlement, and order execution are
  outside the Phase 3 MVP.
