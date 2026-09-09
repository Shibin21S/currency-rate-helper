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
        cell_html += (
            f'        <td{class_attr}>Buy {format_rate(buy, currency)} / '
            f'Sell {format_rate(sell, currency)} '
            f'<span class="est-tag">(Estimated)</span></td>\n'
        )

    return f"""      <tr>
        <td>{currency}</td>
        <td class="baseline-cell">{baseline_str} <span class="est-tag">(as of {info['date']})</span></td>
{cell_html}        <td class="best-deal">{best_bank}</td>
      </tr>"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Currency Rate Helper</title>
<style>
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    background-color: #fafafa;
    color: #2b2b2b;
    max-width: 900px;
    margin: 40px auto;
    padding: 0 20px;
    line-height: 1.5;
  }}
  h1 {{
    font-size: 1.6em;
    margin-bottom: 4px;
  }}
  .subtitle {{
    color: #666;
    margin-top: 0;
    margin-bottom: 24px;
  }}
  .notice {{
    background-color: #f0f0f0;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 14px 18px;
    margin-bottom: 28px;
  }}
  .notice p {{
    margin: 4px 0;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16px;
    font-size: 0.92em;
  }}
  th, td {{
    text-align: left;
    padding: 10px 10px;
    border-bottom: 1px solid #ddd;
    vertical-align: top;
  }}
  th {{
    background-color: #f0f0f0;
    font-weight: normal;
    color: #444;
  }}
  .baseline-cell {{
    font-weight: bold;
  }}
  .est-tag {{
    color: #888;
    font-size: 0.82em;
  }}
  .winner {{
    background-color: #eef3ec;
    font-weight: bold;
  }}
  .best-deal {{
    font-weight: bold;
  }}
  .table-wrap {{
    overflow-x: auto;
  }}
  .table-note {{
    color: #777;
    font-size: 0.85em;
    margin-top: -4px;
    margin-bottom: 28px;
  }}
  footer {{
    font-size: 0.85em;
    color: #888;
    border-top: 1px solid #ddd;
    padding-top: 14px;
  }}
</style>
</head>
<body>

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
