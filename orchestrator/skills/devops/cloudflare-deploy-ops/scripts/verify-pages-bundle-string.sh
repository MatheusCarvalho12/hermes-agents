#!/bin/bash
# Verify a feature's frontend code is actually served by a Cloudflare Pages production domain.
# Usage: bash verify-pages-bundle-string.sh <pages-domain> <unique-UI-string>
# Prints every asset containing the string. Lazy chunks matter: searches ALL assets, not just index.
set -e
DOMAIN="${1:?usage: $0 <pages-domain> <unique-ui-string>}"
NEEDLE="${2:?usage: $0 <pages-domain> <unique-ui-string>}"

HTML=$(curl -s --max-time 20 "https://$DOMAIN")
TOTAL=$(echo "$HTML" | grep -o '/assets/[^"]*\.js' | sort -u | wc -l | tr -d ' ')
echo "assets js: $TOTAL"
FOUND=0
for JS in $(echo "$HTML" | grep -o '/assets/[^"]*\.js' | sort -u); do
  HIT=$(curl -s --max-time 30 "https://$DOMAIN$JS" | grep -c "$NEEDLE" || true)
  if [ "$HIT" -gt 0 ]; then
    echo "ACHOU: $JS"
    FOUND=1
  fi
done
if [ "$FOUND" = "0" ]; then
  echo "NAO ACHOU '$NEEDLE' no ar" >&2
  exit 1
fi
