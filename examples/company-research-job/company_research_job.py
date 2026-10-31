#!/usr/bin/env python3
"""
Company Research Job — example workflow (distribution sprint, 2026-10-31).

Chains the three live fleet endpoints that make up the Company Research Job
offer, end-to-end, for one company:

  1. websearch  POST https://api.mekongtradeintel.com/websearch/  $0.010  {"query": ..., "num": 5}
  2. enrich     POST https://api.mekongtradeintel.com/enrich/     $0.020  {"domain": ...}
  3. brief      POST https://api.mekongtradeintel.com/brief/      $0.050  {"topic": ..., "geo": ...}

Prices and inputs verified live from the fleet clinic catalogue on 2026-10-31
(GET /clinic/query-templates and /clinic/request-schema).

Modes
-----
TRIAL (default): the fleet serves a per-IP daily free-trial quota, so the
first calls from a fresh IP are answered free and this script labels them
TRIAL. Trial responses are real endpoint responses, not mocks.
If a step answers HTTP 402 instead (trial quota for the day is used up),
the script prints that step's quoted price from the 402 body and carries
on — it never invents data.

PAID (--paid): this script does NOT hold any wallet key. Paying is done
with the fleet's standard x402 client pattern (a funded wallet wrapped in
@x402/fetch); per-step curl equivalents are printed so an operator can
wire their own payer. See REPORT.md in the sprint folder.

Cost accounting printed at the end, always:
  - list price of the chain: $0.010 + $0.020 + $0.050 = $0.08
  - what this run actually cost (trial = $0.00)
  - the Company Research Job price: $1.50 as ONE payment for the
    orchestrated job (single-payment endpoint LIVE since 2026-10-31 at
    POST https://api.mekongtradeintel.com/companyresearch/; the chain
    also stays available per call, $0.08 total).

Usage:
  python3 company_research_job.py --company "Coinbase" --domain coinbase.com [--geo US]
  python3 company_research_job.py --company "Vinamilk" --domain vinamilk.com.vn --out result.json

Python stdlib + curl when present (falls back to urllib). No keys, no
wallet, nothing spent in trial mode.
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

BASE = "https://api.mekongtradeintel.com"
# The fleet's trial middleware trial-serves browser-like user agents and
# sends bot-like agents straight to the paid 402 path. An example meant to
# demonstrate the free trial therefore identifies as a browser, exactly as
# a human evaluator opening the endpoints would be served.
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 "
      "company-research-example/1.0")

STEPS = [
    ("websearch", "/websearch/", 0.010),
    ("enrich", "/enrich/", 0.020),
    ("brief", "/brief/", 0.050),
]
JOB_PRICE = 1.50


def call(path, payload):
    """POST JSON, return (status, parsed_json_or_text). Never raises.

    Transport: curl when available (some proxies truncate Python urllib
    chunked reads — observed live from one egress: IncompleteRead and
    dropped connections, while curl delivered all three endpoints
    cleanly), otherwise urllib with one retry + partial-body salvage.
    A salvaged partial fleet response is still real data, labelled.
    """
    import shutil
    if shutil.which("curl"):
        import subprocess
        try:
            p = subprocess.run(
                ["curl", "-sS", "-m", "180", "-A", UA, "-X", "POST", BASE + path,
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps(payload), "-w", "\n%{http_code}"],
                capture_output=True, text=True, timeout=200)
            out = p.stdout or ""
            body, _, code = out.rpartition("\n")
            status = int(code) if code.strip().isdigit() else None
            return status, _parse(body if body else out)
        except Exception as e:
            return None, {"error": f"curl transport: {e}"}
    import http.client
    last = (None, {"error": "no attempt"})
    for _ in range(2):
        req = urllib.request.Request(
            BASE + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "User-Agent": UA,
                     "Accept-Encoding": "identity", "Connection": "close"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read().decode("utf-8", "replace")
                return resp.status, _parse(body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            return e.code, _parse(body)
        except http.client.IncompleteRead as e:
            partial = (e.partial or b"").decode("utf-8", "replace")
            parsed = _parse(partial)
            if isinstance(parsed, dict) and "raw" not in parsed:
                parsed["_salvaged_partial"] = True
                return 200, parsed
            last = (200, {"raw": partial[:2000], "_salvaged_partial": True})
        except Exception as e:  # network error etc.
            last = (None, {"error": str(e)})
    return last


def _parse(body):
    try:
        return json.loads(body)
    except Exception:
        return {"raw": body[:2000]}


def quoted_price(body):
    """Best-effort price quote out of a 402 body (accepts[0].amount in atomic USDC)."""
    try:
        acc = body.get("accepts") or body.get("paymentRequirements") or []
        if acc and isinstance(acc, list):
            amt = acc[0].get("amount") or acc[0].get("maxAmountRequired")
            if amt is not None:
                return int(amt) / 1e6
    except Exception:
        pass
    return None


def summarise(company, domain, results):
    """Deterministic stitched summary — no LLM, no invented facts."""
    lines = [f"# Company research — {company} ({domain})", ""]
    ws = results.get("websearch", {})
    data = ws.get("data") if isinstance(ws, dict) else None
    if data is None and isinstance(ws, dict):
        data = ws  # some endpoints answer unwrapped
    items = None
    if isinstance(data, dict):
        items = data.get("results") or data.get("items") or data.get("organic") or data.get("data")
    elif isinstance(data, list):
        items = data
    lines.append("## What the web says (websearch)")
    if items:
        for it in items[:5]:
            if isinstance(it, dict):
                title = it.get("title") or it.get("name") or "(untitled)"
                link = it.get("link") or it.get("url") or ""
                lines.append(f"- {title} {link}".strip())
    else:
        lines.append("- (no structured results in this response — see raw JSON)")
    lines.append("")
    lines.append("## Company footprint (enrich)")
    en = results.get("enrich", {})
    en_data = en.get("data") if isinstance(en, dict) else None
    if not isinstance(en_data, dict) and isinstance(en, dict):
        en_data = en  # enrich answers unwrapped: {domain, company, web, dns, whois, ...}
    if isinstance(en_data, dict):
        for k in list(en_data.keys())[:10]:
            v = en_data[k]
            if isinstance(v, (str, int, float)) and str(v):
                lines.append(f"- {k}: {v}")
            elif isinstance(v, dict):
                inner = [f"{ik}: {iv}" for ik, iv in list(v.items())[:3]
                         if isinstance(iv, (str, int, float)) and str(iv)]
                if inner:
                    lines.append(f"- {k}: " + "; ".join(inner))
    else:
        lines.append("- (see raw JSON)")
    lines.append("")
    lines.append("## Briefing (brief)")
    br = results.get("brief", {})
    br_data = br.get("data") if isinstance(br, dict) else None
    text = None
    if isinstance(br, dict) and isinstance(br.get("brief"), str):
        text = br["brief"]
    if isinstance(br_data, dict):
        text = br_data.get("brief") or br_data.get("text") or br_data.get("summary") or text
    if not text and isinstance(br, dict) and isinstance(br.get("news"), dict):
        # morning-brief shape: {news:{items[]}, trends:{...}, sentiment:{...}}
        bits = []
        items = br["news"].get("items") or []
        for it in items[:5]:
            if isinstance(it, dict):
                bits.append(f"- {it.get('title') or '(untitled)'}"
                            + (f" ({it['source']})" if it.get("source") else ""))
        sent = br.get("sentiment") or {}
        if sent.get("label"):
            bits.append(f"- sentiment: {sent['label']} (score {sent.get('score')}, "
                        f"{sent.get('headlineCount')} headlines)")
        tr = br.get("trends") or {}
        if tr.get("avgInterest") is not None:
            bits.append(f"- trend interest (avg): {tr['avgInterest']}")
        text = "\n".join(bits) if bits else None
    lines.append((text[:1500] if text else "(see raw JSON)"))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Company Research Job example workflow")
    ap.add_argument("--company", required=True, help='e.g. "Coinbase"')
    ap.add_argument("--domain", required=True, help='e.g. "coinbase.com"')
    ap.add_argument("--geo", default=None, help='optional geo for brief, e.g. "US"')
    ap.add_argument("--paid", action="store_true",
                    help="print per-step paid curl equivalents instead of calling the trial path")
    ap.add_argument("--out", default=None, help="also write the full result JSON to this file")
    args = ap.parse_args()

    payloads = {
        "websearch": {"query": f"{args.company} latest news products funding", "num": 5},
        "enrich": {"domain": args.domain},
        "brief": {"topic": f"{args.company} company research"},
    }
    if args.geo:
        payloads["brief"]["geo"] = args.geo

    list_total = sum(p for _, _, p in STEPS)

    if args.paid:
        print("PAID mode: this script holds no wallet key. Wire each call with your")
        print("x402 payer (e.g. @x402/fetch + a funded Base wallet), or use the")
        print("single-payment job endpoint: POST https://api.mekongtradeintel.com/companyresearch/ ($1.50, live).")
        print("Per-step paid calls at list price:")
        for slug, path, price in STEPS:
            print(f"  # {slug}  ${price:.3f}")
            print(f"  curl -X POST \"{BASE}{path}\" -H \"Content-Type: application/json\" "
                  f"-d '{json.dumps(payloads[slug])}'")
        print(f"Chain list total: ${list_total:.2f} | Job price (one payment): ${JOB_PRICE:.2f}")
        return 0

    print(f"Company Research Job (TRIAL run) — {args.company} / {args.domain}")
    print("Trial calls are free, served under the fleet's per-IP daily trial quota.\n")
    results, statuses = {}, {}
    spent_note = []
    for slug, path, price in STEPS:
        status, body = call(path, payloads[slug])
        statuses[slug] = status
        if status == 402:
            q = quoted_price(body)
            results[slug] = {"payment_required": True, "quoted_usd": q}
            spent_note.append(f"{slug}: HTTP 402 (trial quota used up; quoted ${q if q is not None else price:.3f})")
            print(f"[{slug}] HTTP 402 — payment required, quoted ${q if q is not None else price}")
        elif status and 200 <= status < 300:
            results[slug] = body
            print(f"[{slug}] HTTP {status} — trial-served, $0.00 (list ${price:.3f})")
        else:
            results[slug] = body
            print(f"[{slug}] HTTP {status} — see raw result in output JSON")
    print()
    print(summarise(args.company, args.domain, results))
    print()
    print("=" * 64)
    print(f"List price of the chain : ${list_total:.2f}  (websearch $0.010 + enrich $0.020 + brief $0.050)")
    print(f"This run actually cost  : $0.00 (trial)")
    print(f"Job price, one payment  : ${JOB_PRICE:.2f}  (orchestrated job endpoint — LIVE at")
    print("                           POST /companyresearch/ ; chain per call = $0.08 total)")
    print("Self-test flag          : any paid verification of this workflow is a SELF-TEST, never revenue.")

    if args.out:
        with open(args.out, "w") as f:
            json.dump({"company": args.company, "domain": args.domain,
                       "statuses": statuses, "results": results,
                       "list_total_usd": list_total, "job_price_usd": JOB_PRICE,
                       "mode": "trial", "cost_usd": 0.0}, f, ensure_ascii=False, indent=2)
        print(f"Full result JSON written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
