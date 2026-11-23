#!/bin/bash
# render.sh <project dir> [<project dir> ...]: renders the reel (MP4) and the graphics-only overlay (ProRes 4444 MOV
# with alpha) for each project, then the 540x960 poster from frame 0. 2 workers: other renders share this machine.
# MP4_ONLY=1 skips the overlay MOV (use after a sound-level change: the overlay has no sound).
for P in "$@"; do
  cd "$P" || continue
  S=$(basename "$P")
  mkdir -p renders
  echo "== $S mp4"
  npx --yes hyperframes@0.9.83 render . -o "renders/$S.mp4" --workers 2 --fps 30 --quiet 2>&1 | tail -3
  if [ -z "$MP4_ONLY" ]; then
    echo "== $S overlays mov"
    npx --yes hyperframes@0.9.83 render overlays --format mov -o "$P/renders/$S-overlays.mov" --workers 2 --fps 30 --quiet 2>&1 | tail -3
  fi
  ffmpeg -v error -y -i "renders/$S.mp4" -vf "select=eq(n\,0),scale=540:960" -frames:v 1 -q:v 3 renders/poster.jpg
  ls -la renders
done
