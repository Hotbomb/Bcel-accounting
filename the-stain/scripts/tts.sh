#!/bin/bash
# Thai TTS via edge-tts through the session proxy. Usage: tts.sh <character> "<thai text>" <out.mp3>
set -e
export SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
P="${HTTPS_PROXY:-$https_proxy}"
case "$1" in
  martin) V=th-TH-NiwatNeural;     PI=-6Hz;  R=-5% ;;
  dao)    V=th-TH-PremwadeeNeural; PI=-1Hz;  R=-5% ;;
  andy)   V=th-TH-NiwatNeural;     PI=-14Hz; R=-12% ;;
  do)     V=th-TH-NiwatNeural;     PI=+10Hz; R=+8% ;;
esac
for i in 1 2 3 4 5 6; do
  edge-tts ${P:+--proxy "$P"} --voice $V --pitch=$PI --rate=$R --text "$2" --write-media "$3" >/dev/null 2>&1 || true
  [ -s "$3" ] && exit 0
  sleep $((i*2))
done
echo "TTS FAILED: $1 $2" >&2; exit 1
