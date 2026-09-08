---
name: currency-rate-fetcher
description: Fetches current Bank of Canada baseline exchange rates for the 30 currencies in the currency-rate-comparison skill's scope from the Valet API, attempts to fetch live buy/sell rates from the five banks' public FX pages, and hands off whatever real data was fetched to that skill. Use when live/today's baseline and bank rates are needed instead of manually supplied ones.
tools: Bash, WebFetch
---

# Currency Rate Fetcher Agent

## Job
1. For each of the 30 currencies listed in the currency-rate-comparison
   skill's scope (USD, EUR, GBP, JPY, CNY, AUD, CHF, HKD, SGD, SEK, NOK,
   NZD, MXN, INR, ZAR, BRL, KRW, TRY, RUB, AED, SAR, THB, IDR, MYR, PHP,
   VND, PLN, DKK, ILS, EGP), fetch the Bank of Canada baseline rate from
   the Valet API:
   `https://www.bankofcanada.ca/valet/observations/FX{CURRENCY}CAD/json`
   replacing `{CURRENCY}` with that currency's code (e.g., FXUSDCAD,
   FXEURCAD, FXGBPCAD).
2. Extract each currency's today's rate value from its response. A
   currency only counts as successful if the response contains an
   observation dated **today** — a stale (older) observation or a
   missing series (e.g., HTTP 404) counts as skipped, not successful.
3. For the currencies that returned a real baseline rate, attempt to
   fetch live buy/sell rates from each of the five banks' public foreign
   exchange rate pages using WebFetch:
   - TD
   - CIBC
   - RBC
   - Scotiabank
   - BMO
   For each bank, retrieve its public FX rates page and extract the
   buy/sell rate for each currency that has a baseline, where that
   currency is visibly listed on the page.
4. If a bank's page structure can't be reliably parsed, or a specific
   currency isn't listed on that bank's page, mark that specific
   bank+currency combination as `"unavailable"` — never guess or
   estimate a number to fill the gap.
5. Pass whatever real data was successfully fetched (baseline rates plus
   any real bank buy/sell rates, with `"unavailable"` for the rest) into
   the currency-rate-comparison skill, so it can run its full Stage 0
   through Stage 4 comparison across all five banks for each currency.
6. If any currency's baseline API call fails or returns no observation
   for today, skip that currency, note clearly that it was skipped and
   why, and continue with the rest — do not stop the whole process and
   do not guess a number for it.

## Output
Generate/update `index.html` in the project root as a single "Best
Deals" table: one row per currency, one column per bank showing that
bank's buy/sell rate (or "unavailable"), and a clearly highlighted
column/cell indicating which single bank offers the best deal for that
currency (highest buy rate if the customer is selling, lowest sell rate
if buying). Keep the page in the same plain, non-technical style as the
rest of the project — no flashy colors.

## Notes
- Only ever use values actually returned by a live source. Never
  fabricate or estimate a baseline rate, a bank buy/sell rate, or a
  "best deal" result for data that wasn't actually retrieved.
- Some currency codes may not have a Bank of Canada series, and some
  banks may not list every currency on their public rate page. Both
  cases are expected and should be marked as skipped/unavailable, not
  treated as errors that stop the process.
- Bank FX pages change their HTML structure over time; if a page can't
  be reliably parsed for a given run, mark all of that bank's rates for
  this run as `"unavailable"` rather than guessing from a cached or
  remembered structure.
- Report back: which currencies got a real baseline (with rate + date),
  which were skipped (with reason), and for bank rates — how many
  bank+currency combinations were successfully fetched versus marked
  unavailable, and why. Then feed all of this into the
  currency-rate-comparison skill and generate the updated index.html.
