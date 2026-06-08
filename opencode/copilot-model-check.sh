#!/usr/bin/env bash
#
# copilot-model-check.sh — probe which GitHub Copilot models actually work in
# opencode, and optionally sync the provider whitelist in opencode.json.
#
# Why probe at all? The only reliable signal for "can I use this model" is to
# actually call it. models.dev lists the *candidates*, but three things only
# surface at call time:
#   * "not supported"                -> blocked by your Copilot plan / policy
#   * "not available for integrator" -> not exposed to the opencode integration
#   * empty reply                    -> flaky reasoning model (retry to confirm)
#
# So we send a tiny prompt to every candidate and classify the result. Models
# that answer are WORKING; the rest are blocked or flaky.
#
# Requires: opencode, curl, python3 (all on PATH).
#
set -uo pipefail

PROVIDER="github-copilot"
PROMPT="Say hello"
RETRIES=3
TIMEOUT=90
WRITE=0
CONFIG="${HOME}/.config/opencode/opencode.json"
MODELS_API="https://models.dev/api.json"

usage() {
  cat >&2 <<'EOF'
copilot-model-check.sh — probe which Copilot models work in opencode.

Usage:
  copilot-model-check.sh [options]

Options:
  --write           Update provider.<provider>.whitelist in the opencode config.
  --provider ID     Provider to probe (default: github-copilot).
  --prompt TEXT     Prompt sent to each model (default: "Say hello").
  --retries N       Attempts before marking a model flaky (default: 3).
  --timeout S       Per-call timeout in seconds (default: 90).
  --config PATH     Config file to update (default: ~/.config/opencode/opencode.json).
  -h, --help        Show this help.

Examples:
  copilot-model-check.sh                 # report + paste-ready whitelist
  copilot-model-check.sh --write         # also rewrite opencode.json
  copilot-model-check.sh --retries 2 --timeout 60
EOF
  exit 0
}

while [ $# -gt 0 ]; do
  case "$1" in
    --write)    WRITE=1 ;;
    --provider) PROVIDER="${2:?--provider needs a value}"; shift ;;
    --prompt)   PROMPT="${2:?--prompt needs a value}"; shift ;;
    --retries)  RETRIES="${2:?--retries needs a value}"; shift ;;
    --timeout)  TIMEOUT="${2:?--timeout needs a value}"; shift ;;
    --config)   CONFIG="${2:?--config needs a value}"; shift ;;
    -h|--help)  usage ;;
    *) echo "unknown argument: $1 (try --help)" >&2; exit 1 ;;
  esac
  shift
done

for bin in opencode curl python3; do
  command -v "$bin" >/dev/null 2>&1 || { echo "error: '$bin' not found in PATH" >&2; exit 1; }
done

echo "Fetching candidate models for '$PROVIDER' from models.dev ..." >&2
MODELS=$(curl -fsSL "$MODELS_API" | PROVIDER="$PROVIDER" python3 -c '
import sys, json, os
prov = os.environ["PROVIDER"]
data = json.load(sys.stdin)
p = data.get(prov)
if not p:
    sys.stderr.write("error: provider %r not present in models.dev\n" % prov)
    sys.exit(1)
print("\n".join(sorted(p.get("models", {}))))
') || { echo "error: failed to fetch model list" >&2; exit 1; }

total=$(printf '%s\n' "$MODELS" | grep -c . || true)
echo "Probing $total models (prompt: \"$PROMPT\", retries: $RETRIES, timeout: ${TIMEOUT}s)" >&2
echo >&2

# Neutralise any existing whitelist/blacklist while probing. Otherwise opencode
# filters the registry down to the already-whitelisted models and every other
# candidate fails locally with "Model not found" before ever reaching the
# provider API -- which would both hide blocked models and produce false
# "working" results. We inject a final-scope config that whitelists *all*
# candidates, so each probe reaches the real provider and returns its true
# verdict ("not supported" / a real reply / etc.).
OPENCODE_CONFIG_CONTENT=$(PROVIDER="$PROVIDER" python3 -c '
import sys, json, os
models = [l.strip() for l in sys.stdin if l.strip()]
prov = os.environ["PROVIDER"]
print(json.dumps({
    "$schema": "https://opencode.ai/config.json",
    "provider": {prov: {"whitelist": models}},
}))
' <<< "$MODELS")
export OPENCODE_CONFIG_CONTENT

# Strip ANSI colours, the "> build · model" header line, and blank lines so we
# are left with just the model's actual reply (or its error).
clean() { sed -E 's/\x1b\[[0-9;]*m//g' | grep -vE '^[[:space:]]*>' | grep -vE '^[[:space:]]*$'; }

probe_once() {
  local model="$1" body
  # NB: redirect stdin from /dev/null. `opencode run` reads stdin, and without
  # this it would consume the rest of the caller's `while read` here-string,
  # silently aborting the loop after the first model.
  body=$(timeout "$TIMEOUT" opencode run --pure -m "$PROVIDER/$model" "$PROMPT" </dev/null 2>&1 | clean)
  if printf '%s' "$body" | grep -qiE 'model not found'; then
    # opencode filtered this model out of the registry (whitelist/blacklist
    # still active). The probe never reached the provider, so this is not a
    # trustworthy verdict -- surface it instead of silently passing.
    echo "DELISTED"
  elif printf '%s' "$body" | grep -qiE 'not supported'; then
    echo "BLOCKED_POLICY"
  elif printf '%s' "$body" | grep -qiE 'not available for integrator'; then
    echo "BLOCKED_INTEGRATOR"
  elif printf '%s' "$body" | grep -qiE '[[:alnum:]]'; then
    echo "OK"
  else
    echo "EMPTY"
  fi
}

working=(); blocked=(); flaky=(); delisted=()
processed=0

while IFS= read -r m; do
  [ -n "$m" ] || continue
  processed=$((processed + 1))
  result="EMPTY"
  for _ in $(seq 1 "$RETRIES"); do
    result=$(probe_once "$m")
    [ "$result" = "EMPTY" ] || break
  done
  case "$result" in
    OK)                 working+=("$m"); printf '  \033[32m✓ working\033[0m   %s\n' "$m" >&2 ;;
    BLOCKED_POLICY)     blocked+=("$m"); printf '  \033[31m✗ blocked\033[0m   %s  (not supported by your plan)\n' "$m" >&2 ;;
    BLOCKED_INTEGRATOR) blocked+=("$m"); printf '  \033[31m✗ blocked\033[0m   %s  (not available for integrator)\n' "$m" >&2 ;;
    DELISTED)           delisted+=("$m"); printf '  \033[35m! delisted\033[0m  %s  (filtered out locally; whitelist override failed)\n' "$m" >&2 ;;
    EMPTY)              flaky+=("$m");   printf '  \033[33m? flaky\033[0m     %s  (empty after %s tries)\n' "$m" "$RETRIES" >&2 ;;
  esac
done <<< "$MODELS"

echo >&2
printf 'Summary: %d working, %d blocked, %d flaky, %d delisted\n' \
  "${#working[@]}" "${#blocked[@]}" "${#flaky[@]}" "${#delisted[@]}" >&2
echo >&2

if [ "${#working[@]}" -gt 0 ]; then
  whitelist_json=$(printf '%s\n' "${working[@]}" | python3 -c '
import sys, json
print(json.dumps([l.strip() for l in sys.stdin if l.strip()], indent=2))
')
else
  whitelist_json="[]"
fi

echo "Paste-ready whitelist for provider.$PROVIDER:"
echo "$whitelist_json"

if [ "$WRITE" -eq 1 ]; then
  echo >&2
  if [ "$processed" -ne "$total" ]; then
    echo "Refusing to write: only probed $processed of $total candidates (incomplete run)." >&2
    echo "Your config was left untouched. Re-run the probe to completion first." >&2
    exit 1
  fi
  if [ "${#working[@]}" -eq 0 ]; then
    echo "Refusing to write: zero working models detected (likely a transient failure)." >&2
    echo "Your config was left untouched." >&2
    exit 1
  fi
  if [ "${#delisted[@]}" -gt 0 ]; then
    echo "Refusing to write: ${#delisted[@]} model(s) were delisted locally, meaning the" >&2
    echo "whitelist override did not take effect and verdicts are unreliable." >&2
    echo "Your config was left untouched." >&2
    exit 1
  fi
  echo "Updating $CONFIG ..." >&2
  WL="$whitelist_json" PROVIDER="$PROVIDER" CONFIG="$CONFIG" python3 <<'PY'
import json, os, sys
path = os.environ["CONFIG"]
provider = os.environ["PROVIDER"]
whitelist = json.loads(os.environ["WL"])
try:
    with open(path) as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"$schema": "https://opencode.ai/config.json"}
data.setdefault("provider", {}).setdefault(provider, {})["whitelist"] = whitelist
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
print("Wrote %d models to provider.%s.whitelist" % (len(whitelist), provider), file=sys.stderr)
PY
  echo "Done. Restart opencode for the change to take effect." >&2
fi
