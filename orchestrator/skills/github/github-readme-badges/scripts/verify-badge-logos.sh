#!/bin/bash
# Verifica se logos shields.io realmente renderizam (não confia em HTTP 200).
# Uso: ./verify-badge-logos.sh react users fastapi ...
# Saída: ✅ = logo renderiza (width >= 33), ❌ = sem logo (width 15 = só texto).
# Base: largura do SVG — com logo o badge fica largo (>=33), sem logo fica ~15.
for logo in "$@"; do
  w=$(curl -s "https://img.shields.io/badge/-t-000?logo=$logo&logoColor=white" | grep -o 'width="[0-9]*"' | head -1)
  wnum=${w#width=\"}; wnum=${wnum%\"}
  if [ "$wnum" -gt 20 ] 2>/dev/null; then
    echo "$logo: ✅ logo (width=$wnum)"
  else
    echo "$logo: ❌ sem logo (width=$wnum) — retorna 200 mas não renderiza"
  fi
done
