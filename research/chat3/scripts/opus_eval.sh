#!/bin/bash
# Reproduce the Opus/MP3 round-trip evaluation.
# usage: opus_eval.sh <fixture_dir> <transcribe-cli> <model.gguf>
# <fixture_dir> must contain clean 16 kHz mono WAVs named NN_clean.wav.
set -eu
SRC=${1:?fixture dir}
CLI=${2:?transcribe-cli}
MODEL=${3:?model.gguf}
OUT=${OUT:-out}
mkdir -p "$OUT/enc" "$OUT/dec"
for f in "$SRC"/*_clean.wav; do
  b=$(basename "$f" .wav)
  for br in 16 20 24; do
    ffmpeg -y -loglevel error -i "$f" -c:a libopus -b:a ${br}k -vbr off -ac 1 -ar 48000 "$OUT/enc/${b}_opus${br}k.ogg"
  done
  ffmpeg -y -loglevel error -i "$f" -c:a libmp3lame -b:a 64k -ac 1 -ar 16000 "$OUT/enc/${b}_mp3_64k.mp3"
done
for f in "$OUT"/enc/*; do
  n=$(basename "$f")
  ffmpeg -y -loglevel error -i "$f" -ac 1 -ar 16000 "$OUT/dec/${n%.*}.wav"
done
for v in opus16k opus20k opus24k mp3_64k; do
  ls "$OUT"/dec/*_${v}.wav | sort > "$OUT/$v.list"
  "$CLI" -m "$MODEL" --backend metal -l en -q --batch "$OUT/$v.list" --batch-jsonl > "$OUT/cli_$v.jsonl"
done
echo "encoded $(ls "$OUT/enc" | wc -l | tr -d ' ') variants; transcripts in $OUT/cli_*.jsonl"
echo "run: python3 research/chat3/scripts/wer.py <gold.csv> <transcript.jsonl>"
