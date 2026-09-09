---
name: currency-rate-fetcher
description: Fetches live Bank of Canada baseline rates for 5 currencies (USD, GBP, EUR, JPY, INR) from the Valet API, then applies each bank's published markup to produce clearly-labeled ESTIMATED buy/sell rates for TD, CIBC, RBC, Scotiabank, and BMO, and hands off the result to the currency-rate-comparison skill. Use when a live baseline plus estimated bank rates are needed.
tools: Bash, WebFetch
---

# Currency Rate Fetcher Agent

## Why estimation instead of live scraping
Direct attempts to fetch live rates from TD, CIBC, RBC, Scotiabank, and
BMO's public pages, and from a third-party comparison site, all failed:
every one of these pages computes its displayed rate with a JavaScript
calculator in the browser, so no rate number exists in the raw page
content a fetch can read. This is a confirmed, structural limitation, not
a transient failure — so this agent no longer attempts to scrape bank
pages. Instead it computes transparent, clearly-labeled estimates from the
live Bank of Canada baseline and each bank's publicly documented typical
markup percentage.

## Job
1. For each of the 5 currencies in scope — **USD, GBP, EUR, JPY, INR** —
   fetch the Bank of Canada baseline rate from the Valet API:
   `https://www.bankofcanada.ca/valet/observations/FX{CURRENCY}CAD/json`
   replacing `{CURRENCY}` with that currency's code (FXUSDCAD, FXGBPCAD,
   FXEURCAD, FXJPYCAD, FXINRCAD).
2. A currency only counts as successful if the response contains an
   observation dated **today**. If the API call fails or has no
   observation for today, skip that currency, note why, and continue —
   never estimate a substitute baseline.
3. For each successfully-fetched currency, calculate each bank's
   estimated buy and sell rate using its published markup:

   | Bank | Markup |
   |---|---|
   | TD | 2.64% |
   | CIBC | 3.0% |
   | RBC | 2.75% |
   | Scotiabank | 2.88% |
   | BMO | 2.75% |

   - Estimated buy rate = `baseline × (1 + markup)`
   - Estimated sell rate = `baseline × (1 − markup)`
4. Determine the best deal per currency: the bank with the **lowest
   estimated buy rate**.
5. Pass the live baseline, every bank's estimated buy/sell rate, and the
   best-deal result for each currency into the currency-rate-comparison
   skill, so it can run its full Stage 0 through Stage 4 logic.

## Output
Regenerate `index.html` in the project root as a "Best Deals" table:
one row per currency (USD, GBP, EUR, JPY, INR), one column per bank
showing that bank's estimated buy/sell rate, and a highlighted column
showing the best-deal bank for that currency. Every bank-specific number
must be visibly labeled "Estimated" in the table itself — not only in a
banner — and the page must state plainly, near the top, that the Bank of
Canada baseline is live real data while bank-specific rates are estimated
from each bank's published markup because their sites use JavaScript
calculators that can't be scraped.

## Notes
- The Bank of Canada baseline is the only number ever treated as live.
  Never present a bank-specific number as if it were live.
- Never fabricate or adjust a markup percentage beyond the five values
  given above.
- If a currency's baseline can't be fetched, skip only that currency —
  still produce estimates for the currencies that did succeed.
- Report back: which currencies got a live baseline (with rate + date),
  which were skipped (with reason), and the resulting best-deal bank per
  currency. Then feed this into the currency-rate-comparison skill and
  regenerate index.html.
