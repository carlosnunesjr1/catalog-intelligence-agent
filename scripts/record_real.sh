#!/usr/bin/env bash
# Gravação REAL de tela no :99 — browser Camoufox mostrando produto real + enrich ao vivo.
# Tudo num script: sobe ffmpeg, roda browser, aguarda, mata os dois no fim.
set -e
cd /root/catalog-intelligence-agent
OUT=demo-real.mp4
rm -f "$OUT"

# ffmpeg em background
DISPLAY=:99 ffmpeg -y -f x11grab -r 25 -s 1280x800 -i :99.0+0,0 \
  -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p -movflags +faststart "$OUT" &
FFPID=$!
echo "[rec] ffmpeg=$FFPID"

# browser demo (bloqueia ~95s internamente)
DISPLAY=:99 python3 scripts/drive_real.py &
BPID=$!
echo "[rec] browser=$BPID"

# aguarda o browser terminar (drive_real.py tem sleeps ~95s)
wait $BPID 2>/dev/null || true
echo "[rec] browser fim"

# encerra ffmpeg
sleep 2
kill $FFPID 2>/dev/null || true
wait $FFPID 2>/dev/null || true
echo "[rec] finalizado"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT"
