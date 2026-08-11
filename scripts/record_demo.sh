#!/usr/bin/env bash
# Gravação REAL de tela no :99 (Xvfb) — browser + terminal com MCP ao vivo.
# Não é slide. É demonstração interativa gravada frame a frame.
set -e
DISPLAY=:99
OUT=/root/catalog-intelligence-agent/demo-real.mp4
W=1280
H=800
FPS=25

# 1) inicia ffmpeg x11grab em background (grava a tela :99)
ffmpeg -y -f x11grab -r $FPS -s ${W}x${H} -i :99.0+0,0 \
  -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p \
  -movflags +faststart "$OUT" &
FFPID=$!
echo "[rec] ffmpeg PID=$FFPID"
sleep 2

# 2) abre o browser Camoufox (headful) no :99 mostrando produto real
DISPLAY=:99 python3 /root/catalog-intelligence-agent/scripts/drive_real.py &
BROWSERPID=$!
echo "[rec] browser PID=$BROWSERPID"

# 3) roda o enrich ao vivo em terminal visível (gnome-terminal/xterm no :99)
# usa xterm para aparecer na gravação
DISPLAY=:99 xterm -geometry 100x30+50+420 -e \
  "cd /root/catalog-intelligence-agent && python3 scripts/live_enrich.py; read" &
TERMPID=$!

# aguarda a demonstração (tempo da narração ~78s + margem)
sleep 95

# encerra
kill $TERMPID 2>/dev/null || true
kill $BROWSERPID 2>/dev/null || true
sleep 1
kill $FFPID 2>/dev/null || true
wait $FFPID 2>/dev/null || true
echo "[rec] finalizado: $OUT"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT"
