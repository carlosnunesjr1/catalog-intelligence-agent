#!/usr/bin/env bash
# Gravação REAL do vídeo do hackathon — 5 minutos máximo
# Requisitos: Xvfb :99 up, MCP :8791 up, narração pt-BR separada
set -e
cd /root/catalog-intelligence-agent
OUT=/tmp/demo-hackathon.mp4
rm -f "$OUT"

# Verifica serviços
echo "=== verificando serviços ===" 
curl -sS --max-time 6 -o /dev/null -w "MCP :8791 -> %{http_code}\n" http://localhost:8791/mcp 2>/dev/null || echo "MCP falhou"
curl -sS --max-time 6 -o /dev/null -w "Studio :3000 -> %{http_code}\n" http://localhost:3000/health 2>/dev/null || echo "Studio falhou"

# ffmpeg em background (capture 5 min = 300s, mas vamos cortar depois)
DISPLAY=:99 ffmpeg -y -f x11grab -r 25 -s 1280x800 -i :99.0+0,0 \
  -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p -t 300 "$OUT" > /tmp/ffmpeg-final.log 2>&1 &
FFPID=$!
echo "[rec] ffmpeg=$FFPID grava 5min..."

# browser demo (drive_real.py abre produto + chama MCP)
DISPLAY=:99 timeout 280 python3 scripts/drive_real.py &
BPID=$!
echo "[rec] browser=$BPID"

# aguarda browser terminar (drive_real.py tem sleeps ~95s)
wait $BPID 2>/dev/null || true
echo "[rec] browser fim"

sleep 3
kill $FFPID 2>/dev/null || true
wait $FFPID 2>/dev/null || true
echo "[rec] finalizado"

# verifica tamanho/duração
ls -la "$OUT" | awk '{print "size:", $5}'
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT" 2>/dev/null