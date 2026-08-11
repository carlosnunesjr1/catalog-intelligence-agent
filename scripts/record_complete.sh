#!/usr/bin/env bash
# Grava a demo COMPLETA (cada funcionalidade) — ~4-5 min
set -e
cd /root/catalog-intelligence-agent
OUT=/tmp/demo-completa.mp4
rm -f "$OUT"

# verifica serviços
echo "=== MCP :8791 ==="
curl -sS --max-time 6 -o /dev/null -w "%{http_code}" http://localhost:8791/mcp 2>/dev/null || echo "MCP DOWN"

# ffmpeg captura ~6min (360s)
LIBGL_ALWAYS_SOFTWARE=1 DISPLAY=:99 ffmpeg -y -f x11grab -r 25 -s 1280x800 -i :99.0+0,0 \
  -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p -t 380 "$OUT" > /tmp/ffmpeg-completa.log 2>&1 &
FFPID=$!
echo "[rec] ffmpeg=$FFPID"

# browser demo completa
LIBGL_ALWAYS_SOFTWARE=1 DISPLAY=:99 timeout 360 python3 scripts/drive_complete.py > /tmp/drive_complete.out 2>&1
echo "[rec] browser fim (rc=$?)"

sleep 3
kill $FFPID 2>/dev/null || true
wait $FFPID 2>/dev/null || true
echo "[rec] finalizado"
ls -la "$OUT" | awk '{print "size:", $5}'
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT" 2>/dev/null
