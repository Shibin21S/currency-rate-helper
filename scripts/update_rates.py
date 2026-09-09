#!/usr/bin/env python3
"""Fetch live Bank of Canada baseline rates and regenerate index.html with
estimated bank buy/sell rates, derived from each bank's published markup.

Bank-specific rates are never scraped live (TD, CIBC, RBC, Scotiabank, and
BMO all compute their displayed rate with a JavaScript calculator, so no
plain-text rate exists in their page content). Instead this script applies
each bank's publicly documented typical markup to the live Bank of Canada
baseline, and labels every resulting number "Estimated".
"""

import datetime
import json
import sys
import urllib.error
import urllib.request

CURRENCIES = ["USD", "GBP", "EUR", "JPY", "INR"]

# Published typical markup for each bank, applied to the BoC baseline.
BANKS = [
    ("TD", 0.0264),
    ("CIBC", 0.0300),
    ("RBC", 0.0275),
    ("Scotiabank", 0.0288),
    ("BMO", 0.0275),
]

# Presentation-only data: each bank's real public brand color and a short
# initialism, used for a small colored pill next to its rates. This is not
# their logo or any trademarked artwork, just their brand color.
BANK_STYLE = {
    "TD": {"color": "#008A00", "initials": "TD"},
    "CIBC": {"color": "#C8102E", "initials": "CIBC"},
    "RBC": {"color": "#0051A5", "initials": "RBC"},
    "Scotiabank": {"color": "#EC111A", "initials": "SB"},
    "BMO": {"color": "#0079C1", "initials": "BMO"},
}

CURRENCY_SYMBOLS = {
    "USD": "$",
    "GBP": "£",
    "EUR": "€",
    "JPY": "¥",
    "INR": "₹",
}

VALET_URL = "https://www.bankofcanada.ca/valet/observations/FX{code}CAD/json?recent=1"


def fetch_baseline(currency):
    """Fetch the most recent BoC observation for a currency. Returns None
    (never a guessed number) if the API call fails or has no data."""
    url = VALET_URL.format(code=currency)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"  {currency}: FAILED to fetch ({exc})")
        return None

    observations = data.get("observations", [])
    if not observations:
        print(f"  {currency}: no observations returned")
        return None

    obs = observations[-1]
    key = f"FX{currency}CAD"
    if key not in obs:
        print(f"  {currency}: unexpected response shape, skipping")
        return None

    return {"date": obs["d"], "rate": float(obs[key]["v"])}


def format_rate(value, currency):
    # Small-value currencies (JPY, INR) need more decimal places to stay
    # meaningfully precise per unit of CAD.
    return f"{value:.6f}" if currency in ("JPY", "INR") else f"{value:.4f}"


def build_row(currency, info):
    baseline = info["rate"]
    baseline_str = format_rate(baseline, currency)

    buys = {}
    cells = []
    for bank, markup in BANKS:
        buy = baseline * (1 + markup)
        sell = baseline * (1 - markup)
        buys[bank] = buy
        cells.append((bank, buy, sell))

    best_bank = min(buys, key=buys.get)

    cell_html = ""
    for bank, buy, sell in cells:
        class_attr = ' class="winner"' if bank == best_bank else ""
        style = BANK_STYLE[bank]
        cell_html += (
            f'        <td{class_attr}>\n'
            f'          <span class="bank-pill" style="background-color: {style["color"]}">'
            f'{style["initials"]}</span>\n'
            f'          <div class="rate-values">Buy {format_rate(buy, currency)} / '
            f'Sell {format_rate(sell, currency)} '
            f'<span class="est-tag">(Estimated)</span></div>\n'
            f'        </td>\n'
        )

    symbol = CURRENCY_SYMBOLS.get(currency, "")

    return f"""      <tr>
        <td class="currency-cell">{currency}<span class="currency-symbol">{symbol}</span></td>
        <td class="baseline-cell">{baseline_str} <span class="est-tag">(as of {info['date']})</span></td>
{cell_html}        <td><span class="best-deal-badge">{best_bank}</span></td>
      </tr>"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Currency Rate Helper</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>

<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="index.html">Currency Rate Helper</a>
    <nav class="nav-links">
      <a href="index.html" class="active">Home</a>
      <a href="about.html">About</a>
      <a href="faq.html">FAQ</a>
      <a href="contact.html">Contact</a>
    </nav>
  </div>
</header>

<main class="page">

  <h1>Currency Rate Helper</h1>
  <p class="subtitle">Best Deals across TD, CIBC, RBC, Scotiabank, and BMO</p>

  <div class="notice">
    <p><strong>Last updated:</strong> {run_date}</p>
    <p>
      Bank of Canada baseline is <strong>live, real data</strong>, fetched
      automatically from the Bank of Canada Valet API. Bank-specific rates
      are <strong>ESTIMATED</strong> using each bank's publicly documented
      typical markup percentage, since bank websites use JavaScript
      calculators that can't be scraped for a live number. This is a
      standard, transparent method used by real currency comparison tools
      when live rates aren't accessible.
    </p>
  </div>

  <div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>Currency</th>
        <th>BoC Baseline (live)</th>
        <th>TD</th>
        <th>CIBC</th>
        <th>RBC</th>
        <th>Scotiabank</th>
        <th>BMO</th>
        <th>Best Deal</th>
      </tr>
    </thead>
    <tbody>
{table_rows}
    </tbody>
  </table>
  </div>
  <p class="table-note">
    "Buy" = estimated CAD cost to buy 1 unit of that currency from the bank.
    "Sell" = estimated CAD you'd receive selling 1 unit back to the bank.
    Best Deal = the bank with the lowest estimated buy rate for that currency.
    The highlighted cell in each row shows the winning bank's rates. Each
    baseline is labeled with the date of the Bank of Canada observation it
    came from, which may lag by a day on weekends and holidays when no new
    rate is published.
  </p>

  <footer>
    <p>
      Bank markups used for these estimates (published, typical rates):
      TD 2.64% &middot; CIBC 3.0% &middot; RBC 2.75% &middot; Scotiabank 2.88% &middot; BMO 2.75%.
    </p>
    <p>
      Estimates are derived entirely from the live Bank of Canada baseline
      and each bank's published markup &mdash; no bank-specific number on
      this page is a live, scraped rate.
    </p>
    <p>
      This page is regenerated automatically once a day by a GitHub Actions
      workflow.
    </p>
  </footer>

</main>

</body>
</html>
"""


def main():
    print("Fetching Bank of Canada baseline rates...")
    results = {}
    skipped = []
    for currency in CURRENCIES:
        info = fetch_baseline(currency)
        if info is None:
            skipped.append(currency)
            continue
        results[currency] = info
        print(f"  {currency}: {info['rate']} (as of {info['date']})")

    if not results:
        print("No currencies fetched successfully. Leaving index.html unchanged.")
        sys.exit(1)

    if skipped:
        print(f"Skipped (no data available): {', '.join(skipped)}")

    table_rows = "\n".join(build_row(c, results[c]) for c in CURRENCIES if c in results)
    run_date = datetime.datetime.now(datetime.timezone.utc).strftime("%B %d, %Y (UTC)")

    html = HTML_TEMPLATE.format(run_date=run_date, table_rows=table_rows)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("index.html regenerated.")


if __name__ == "__main__":
    main()
