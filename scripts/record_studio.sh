#!/usr/bin/env bash
# Grava o vídeo do DECO STUDIO (agente em ação) — ~4-5 min
set -e
cd /root/catalog-intelligence-agent
OUT=/tmp/video-studio.mp4
rm -f "$OUT"

echo "=== serviços ==="
curl -sS --max-time 6 -o /dev/null -w "MCP :8791 -> %{http_code}\n" http://localhost:8791/mcp 2>/dev/null || echo "MCP DOWN"
curl -sS --max-time 6 -o /dev/null -w "Studio :3000 -> %{http_code}\n" http://localhost:3000/health 2>/dev/null || echo "Studio DOWN"

# ffmpeg grava até 5min
LIBGL_ALWAYS_SOFTWARE=1 DISPLAY=:99 ffmpeg -y -f x11grab -r 25 -s 1280x800 -i :99.0+0,0 \
  -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p -t 320 "$OUT" > /tmp/ffmpeg-studio.log 2>&1 &
FFPID=$!
echo "[rec] ffmpeg=$FFPID"

LIBGL_ALWAYS_SOFTWARE=1 DISPLAY=:99 timeout 300 python3 scripts/drive_studio.py > /tmp/drive_studio.out 2>&1
echo "[rec] browser fim (rc=$?)"

sleep 3
kill $FFPID 2>/dev/null || true
wait $FFPID 2>/dev/null || true
echo "[rec] finalizado"
ls -la "$OUT" | awk '{print "size:", $5}'
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT" 2>/dev/null
