#!/usr/bin/env bash
# =============================================================================
# verify-kit.sh — independent verification kit for the
# Mekong Trade Intelligence x402 API fleet (https://api.mekongtradeintel.com)
#
# What it checks:
#   1. PAYWALL SHAPE (public, no key needed): two sample endpoints must return
#      HTTP 402 with a standard x402 v2 body: x402Version==2, accepts[0] on
#      Base (eip155:8453), USDC asset, correct payTo (agent wallet), and the
#      bazaar extension block present.
#   2. CDP PREFLIGHT (needs CDP_API_KEY_ID + CDP_API_KEY_SECRET env, free at
#      https://portal.cdp.coinbase.com): POST api.cdp.coinbase.com
#      /platform/v2/x402/validate for the sample URLs — every preflight check
#      must PASS and bazaarExtension must be present. Skipped (not failed) if
#      the env vars are absent.
#   3. ON-CHAIN SETTLEMENT (public, no key needed): a sample settlement tx must
#      be a successful Base transaction whose receipt contains a USDC Transfer
#      event INTO the agent wallet. Default tx is our own self-test settlement;
#      pass your own TX_HASH as $1 to check your payment.
#
# Any real failure exits non-zero with a clear message. A check is never
# reported as passed when it did not run or did not succeed.
# =============================================================================
set -u

USDC_BASE="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
AGENT_WALLET="0x198f3895551B309fF5C5F59e690FB0823d10EA93"
AGENT_WALLET_PADDED="0x000000000000000000000000198f3895551b309ff5c5f59e690fb0823d10ea93"
TRANSFER_TOPIC="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
RPCS="https://mainnet.base.org https://base-mainnet.public.blastapi.io https://1rpc.io/base"

PROBES="https://api.mekongtradeintel.com/weather/|GET
https://api.mekongtradeintel.com/websearch/|GET"

# Sample settlement tx (our own self-test; organic buyer payments can be
# checked by passing a different hash as $1).
TX_HASH="${1:-0x625f2bcc2cb514587f29636a1a3f935d4329e1313169241a042e0da3635ffa1f}"

FAIL=0
PASS_COUNT=0
SKIP_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT+1)); echo "  [PASS] $1"; }
fail() { FAIL=$((FAIL+1)); echo "  [FAIL] $1"; }
skip() { SKIP_COUNT=$((SKIP_COUNT+1)); echo "  [SKIP] $1"; }
info() { echo "  $1"; }

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[FAIL] required tool missing: $1" >&2
    exit 2
  fi
}
need curl
need python3

echo "=== verify-kit: Mekong Trade Intelligence x402 fleet ==="
echo "time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# ---------------------------------------------------------------- check 1 ---
echo "[1/3] paywall shape (HTTP 402, x402 v2, bazaar extension)"
while IFS='|' read -r url method; do
  [ -z "$url" ] && continue
  tmp="$(mktemp)"
  code="$(curl -s -m 30 -o "$tmp" -w '%{http_code}' -X "$method" "$url" || echo 'curl-error')"
  info "GET $url -> HTTP $code"
  if [ "$code" != "402" ]; then
    fail "$url: expected HTTP 402, got $code"
    rm -f "$tmp"
    continue
  fi
  ok="$(python3 - "$tmp" "$USDC_BASE" "$AGENT_WALLET" <<'PYEOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    print("FAIL: 402 body is not JSON: " + str(e)); sys.exit(0)
usdc, wallet = sys.argv[2].lower(), sys.argv[3].lower()
problems = []
if d.get("x402Version") != 2:
    problems.append("x402Version != 2 (got %r)" % d.get("x402Version"))
acc = (d.get("accepts") or [{}])[0]
if acc.get("scheme") != "exact":
    problems.append("accepts[0].scheme != exact (got %r)" % acc.get("scheme"))
if str(acc.get("network")) not in ("eip155:8453", "8453"):
    problems.append("accepts[0].network not Base (got %r)" % acc.get("network"))
if str(acc.get("asset", "")).lower() != usdc:
    problems.append("accepts[0].asset not USDC-on-Base (got %r)" % acc.get("asset"))
if str(acc.get("payTo", "")).lower() != wallet:
    problems.append("accepts[0].payTo != agent wallet (got %r)" % acc.get("payTo"))
ext = d.get("extensions") or {}
if "bazaar" not in ext:
    problems.append("extensions.bazaar missing")
if problems:
    for p in problems: print("FAIL: " + p)
else:
    print("OK: amount=%s asset=USDC payTo=%s bazaar=present" % (acc.get("amount"), acc.get("payTo")))
PYEOF
)"
  rm -f "$tmp"
  case "$ok" in
    OK:*) pass "$url: ${ok#OK: }" ;;
    *)    fail "$url: $ok" ;;
  esac
done <<EOF_PROBES
$PROBES
EOF_PROBES
echo ""

# ---------------------------------------------------------------- check 2 ---
echo "[2/3] CDP /x402/validate preflight"
if [ -z "${CDP_API_KEY_ID:-}" ] || [ -z "${CDP_API_KEY_SECRET:-}" ]; then
  skip "CDP_API_KEY_ID/CDP_API_KEY_SECRET not set — create a free key at https://portal.cdp.coinbase.com and export both to run this check."
elif ! command -v node >/dev/null 2>&1; then
  skip "node not installed — CDP check needs node for the EdDSA JWT signature."
else
  nodefile="$(mktemp /tmp/verify-kit-cdp-XXXX.mjs)"
  cat > "$nodefile" <<'NODEEOF'
// Embedded CDP /x402/validate caller. Reads KEYID/KEYSECRET/URL from env.
import crypto from "crypto";
const keyId = process.env.CDP_KEYID, keySecret = process.env.CDP_KEYSECRET, url = process.env.CDP_URL;
const b64u = (o) => Buffer.from(typeof o === "string" ? o : JSON.stringify(o)).toString("base64url");
const now = Math.floor(Date.now() / 1000);
const uri = "POST api.cdp.coinbase.com/platform/v2/x402/validate";
const signingInput = `${b64u({ alg: "EdDSA", typ: "JWT", kid: keyId })}.${b64u({ iss: "cdp", sub: keyId, aud: ["cdp_service"], uri, exp: now + 120, nbf: now - 5 })}`;
const seed = Buffer.from(keySecret, "base64").subarray(0, 32);
const key = crypto.createPrivateKey({ key: Buffer.concat([Buffer.from("302e020100300506032b657004220420", "hex"), seed]), format: "der", type: "pkcs8" });
const jwt = `${signingInput}.${crypto.sign(null, Buffer.from(signingInput), key).toString("base64url")}`;
const res = await fetch("https://api.cdp.coinbase.com/platform/v2/x402/validate", {
  method: "POST",
  headers: { "Content-Type": "application/json", "Authorization": "Bearer " + jwt },
  body: JSON.stringify({ resource: url }),
});
const j = await res.json().catch(() => ({}));
const checks = (j.preflight || []).map(c => ({ check: c.check, passed: !!c.passed, severity: c.severity }));
console.log(JSON.stringify({ http: res.status, checks, bazaar: !!j.bazaarExtension }));
NODEEOF
  cdp_failed=0
  while IFS='|' read -r url method; do
    [ -z "$url" ] && continue
    out="$(CDP_KEYID="$CDP_API_KEY_ID" CDP_KEYSECRET="$CDP_API_KEY_SECRET" CDP_URL="$url" node "$nodefile" 2>/dev/null || echo '{"http":0}')"
    res="$(python3 - "$out" <<'PYEOF'
import json, sys
try:
    j = json.loads(sys.argv[1])
except Exception as e:
    print("FAIL: CDP response not JSON: " + str(e)); sys.exit(0)
if j.get("http") != 200:
    print("FAIL: CDP HTTP %s" % j.get("http")); sys.exit(0)
bad = [c["check"] for c in j.get("checks", []) if not c.get("passed")]
if bad:
    print("FAIL: preflight failed: " + ", ".join(bad)); sys.exit(0)
if not j.get("bazaar"):
    print("FAIL: bazaarExtension absent"); sys.exit(0)
print("OK: %d preflight checks passed, bazaarExtension present" % len(j.get("checks", [])))
PYEOF
)"
    case "$res" in
      OK:*) pass "$url: ${res#OK: }" ;;
      *)    fail "$url: $res"; cdp_failed=1 ;;
    esac
  done <<EOF_PROBES2
$PROBES
EOF_PROBES2
  rm -f "$nodefile"
fi
echo ""

# ---------------------------------------------------------------- check 3 ---
echo "[3/3] on-chain settlement (Base)"
info "tx: $TX_HASH"
rpc_ok=""
receipt=""
for rpc in $RPCS; do
  resp="$(curl -s -m 30 -X POST "$rpc" -H 'Content-Type: application/json' \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getTransactionReceipt\",\"params\":[\"$TX_HASH\"]}" || true)"
  if python3 -c "import json,sys; r=json.load(sys.stdin).get('result'); sys.exit(0 if r else 1)" >/dev/null 2>&1 <<<"$resp"; then
    rpc_ok="$rpc"; receipt="$resp"; break
  fi
done
if [ -z "$rpc_ok" ]; then
  fail "no Base RPC responded with a receipt for $TX_HASH (tried: $RPCS)"
else
  info "rpc: $rpc_ok"
  ok3="$(python3 - "$receipt" "$AGENT_WALLET_PADDED" "$USDC_BASE" "$TRANSFER_TOPIC" <<'PYEOF'
import json, sys
j = json.loads(sys.argv[1])
r = j.get("result")
if not r:
    print("FAIL: receipt missing"); sys.exit(0)
if r.get("status") != "0x1":
    print("FAIL: tx status != 0x1 (failed on-chain)"); sys.exit(0)
wallet, usdc, topic = sys.argv[2].lower(), sys.argv[3].lower(), sys.argv[4].lower()
hit = False
for log in r.get("logs", []):
    topics = [t.lower() for t in log.get("topics", [])]
    if (log.get("address", "").lower() == usdc and len(topics) >= 3
            and topics[0] == topic and topics[2] == wallet):
        hit = True
        amt = int(log.get("data", "0x0"), 16) / 1e6
        print("OK: status=0x1, USDC Transfer of %.6f into agent wallet, block=%s" % (amt, int(r.get("blockNumber","0x0"),16)))
        break
if not hit:
    print("FAIL: no USDC Transfer log into agent wallet in receipt")
PYEOF
)"
  case "$ok3" in
    OK:*) pass "settlement: ${ok3#OK: }" ;;
    *)    fail "settlement: $ok3" ;;
  esac
fi
echo ""
echo "=== result: FAILURES=$FAIL (skipped=$SKIP_COUNT) ==="
if [ "$FAIL" -ne 0 ]; then
  echo "VERIFICATION FAILED — do not trust the fleet on these points until fixed."
  exit 1
fi
echo "VERIFICATION PASSED — all checks that ran succeeded."
