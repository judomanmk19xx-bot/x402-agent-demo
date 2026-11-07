# Company Research Job — example workflow

`company_research_job.py` chains the three live endpoints behind the
Company Research Job offer, end-to-end, for one company:

| step | endpoint | price |
|---|---|---|
| websearch | POST https://api.mekongtradeintel.com/websearch/ | $0.010 |
| enrich | POST https://api.mekongtradeintel.com/enrich/ | $0.020 |
| brief | POST https://api.mekongtradeintel.com/brief/ | $0.050 |

Run (trial is free under the fleet's per-IP daily quota):

```
python3 company_research_job.py --company "Coinbase" --domain coinbase.com --geo US --out result.json
```

Verified live 2026-10-31: all three steps HTTP 200 trial-served, $0.00
spent, real data in every section — see `output-sample.json` (full raw
responses) and the sprint REPORT.md. The script always prints its cost
accounting: chain list $0.08, this run $0.00 (trial), job price $1.50 as
one payment (single-payment endpoint in launch — design in REPORT.md).

`--paid` prints the per-step paid curl equivalents; the script itself
holds no wallet key and spends nothing.

## Single-payment job endpoint — LIVE (2026-10-31)

```
curl -X POST "https://api.mekongtradeintel.com/companyresearch/" \
  -H "Content-Type: application/json" \
  -d '{"company":"Coinbase","domain":"coinbase.com","geo":"US"}'
```

$1.50 in USDC on Base (x402 v2, exact scheme). First call per day is
trial-served free. Offer page: https://api.mekongtradeintel.com/tools/company-research-job.html

## Complementary data sources

Registry pulls underneath the synthesis layer, from a fellow x402 seller:

- **AgentReader** (Axiom Works) — keyless UK Companies House / KYB /
  SEC EDGAR / EU VAT / web-to-markdown over x402 (Base USDC). Every GET
  has a free `?preview=1` with the same JSON shape, handy for wiring a
  registry step into a research pipeline before paying:
  `GET https://api.axiomworks.co.uk/uk-company-lite?number=00445790&preview=1`
  Spec: https://api.axiomworks.co.uk/.well-known/x402 · MCP:
  https://api.axiomworks.co.uk/mcp

Our job stays the synthesis layer on top: web signals + footprint +
narrative briefing as one finished report.
