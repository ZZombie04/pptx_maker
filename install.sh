#!/usr/bin/env sh
# pptx_maker 2.0 연결 (macOS/Linux)
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3 || command -v python)"
[ -z "$PY" ] && { echo "파이썬 3.9 이상이 필요합니다"; exit 1; }
export PYTHONPATH="$DIR"
"$PY" -c "import PIL" 2>/dev/null || echo "[선택] Pillow 권장: $PY -m pip install --user pillow"
"$PY" -m pptx_maker doctor
printf "테마 글꼴 22종(무료)을 설치할까요? [Y/n] "
read -r ANS || ANS=y
if [ "$ANS" = "n" ] || [ "$ANS" = "N" ]; then
  "$PY" -m pptx_maker setup
else
  "$PY" -m pptx_maker setup --fonts
fi
echo "AI 프로그램을 다시 시작하면 pptx_maker 도구와 스킬이 보입니다."
