#!/usr/bin/env bash
set -euo pipefail

: "${GEMINI_API_KEY:?Set GEMINI_API_KEY environment variable first}" 

MODEL="${1:-gemini-1.5-flash}"
PROMPT="${2:-Say 'pong' and nothing else.}"

# Build JSON body safely
escaped_prompt=$(printf '%s' "$PROMPT" | python3 - <<'PY'
import json,sys
print(json.dumps(sys.stdin.read()))
PY
)

BODY=$(cat <<JSON
{"contents":[{"parts":[{"text":$escaped_prompt}]}]}
JSON
)

URL="https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${GEMINI_API_KEY}"

resp_file=$(mktemp)
http_code=$(curl -sS -X POST \
  -H "Content-Type: application/json" \
  -d "$BODY" \
  -w "%{http_code}" \
  -o "$resp_file" \
  "$URL" || true)

if [[ "$http_code" != "200" ]]; then
  echo "ERROR: HTTP $http_code" >&2
  cat "$resp_file" >&2
  rm -f "$resp_file"
  exit 1
fi

if command -v jq >/dev/null 2>&1; then
  text=$(jq -r '.candidates[0].content.parts[0].text // empty' "$resp_file")
  if [[ -z "$text" ]]; then
    echo "Unexpected response:" >&2
    cat "$resp_file" >&2
    rm -f "$resp_file"
    exit 1
  fi
  echo "OK: $text"
else
  echo "OK (raw body below; install 'jq' to parse):"
  cat "$resp_file"
fi

rm -f "$resp_file"
