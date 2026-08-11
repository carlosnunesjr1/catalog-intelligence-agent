#!/usr/bin/env bash
# Monta o vídeo de apresentação: slides com zoom + narração pt-BR + legendas.
set -e
cd /root/catalog-intelligence-agent/video-assets

AUDIO=/tmp/narracao_ptbr.mp3
SRT=legendas.srt
OUT=/tmp/video-final.mp4

# Duração do áudio
DUR=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$AUDIO")
echo "== narração: ${DUR}s =="

# Cenas: [arquivo, peso] — peso proporcional ao tempo de cada fala
SCENES=(
  "00-intro.png 1.0"
  "05-print-loja.png 1.0"
  "02-connections.png 0.8"
  "03-agent.png 0.8"
  "01-chat-score.png 1.2"
  "04-monitor.png 0.9"
  "01-chat-score.png 1.0"
)

# Soma pesos
TOTAL=0
for s in "${SCENES[@]}"; do
  w=$(echo "$s" | awk '{print $2}')
  TOTAL=$(echo "$TOTAL + $w" | bc -l)
done
echo "== pesos: $TOTAL =="

mkdir -p clips
i=1
for s in "${SCENES[@]}"; do
  img=$(echo "$s" | awk '{print $1}')
  w=$(echo "$s" | awk '{print $2}')
  dur=$(echo "$DUR * $w / $TOTAL" | bc -l)
  # zoom leve (Ken Burns) — entrada 1.0 → 1.08, pano lento
  ffmpeg -y -v error -loop 1 -i "$img" -t "$dur" \
    -vf "scale=1400:788:force_original_aspect_ratio=increase,crop=1400:788,zoompan=z='min(zoom+0.0006,1.12)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=25" \
    -r 25 -c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p "clips/c$i.mp4"
  echo "clip $i: $img (${dur}s)"
  i=$((i+1))
done

# Concatena clips
printf "file '%s'\n" clips/c*.mp4 > concat.txt

# Junta: vídeo (slides) + áudio (narração pt-BR), sem legendas
ffmpeg -y -v error -f concat -safe 0 -i concat.txt -i "$AUDIO" \
  -c:v libx264 -preset fast -crf 21 -pix_fmt yuv420p \
  -c:a aac -b:a 128k -shortest -movflags +faststart "$OUT"

echo "== VÍDEO FINAL: $OUT =="
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$OUT"