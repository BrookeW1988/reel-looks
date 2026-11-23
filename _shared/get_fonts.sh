#!/bin/bash
# get_fonts.sh: download the free fonts one look/format template needs into its assets/fonts/ folder.
#
# WHY this exists: fonts are NOT shipped in this repo (cleaner licensing, smaller download). Each template
# expects its fonts under exact file names, so this script saves every file under the name the template's
# build.py looks for. All fonts here are free Google Fonts under the SIL Open Font Licence (see FONTS.md).
# SF Pro (Just you / Full hooks) is Apple's font: it's copied from YOUR Mac, never downloaded or shared.
#
# USAGE:  bash get_fonts.sh <template-slug> <build-folder>
#   e.g.  bash _shared/get_fonts.sh pop-up-proof ~/Movies/Edits-builds/2026-11-23-pop-up-proof-pricing
#   (the build folder is wherever the skill copied the template to; the slug is a looks/ or formats/ folder name)
# Already-downloaded files are kept, so it's safe to run again.

set -euo pipefail

slug="${1:-}"
dest="${2:-}"
if [ -z "$slug" ] || [ -z "$dest" ]; then
  echo "usage: get_fonts.sh <template-slug> <build-folder>" >&2
  exit 1
fi

fonts="$dest/assets/fonts"
mkdir -p "$fonts"

GF="https://github.com/google/fonts/raw/main/ofl"          # Google Fonts' own repo (exact files)
FS="https://cdn.jsdelivr.net/fontsource/fonts"             # Fontsource: single-weight files of the same fonts

# get <file name the template expects> <url>
get() {
  if [ -s "$fonts/$1" ]; then
    echo "have  $1"
    return
  fi
  if curl -fsSL -o "$fonts/$1" "$2"; then
    echo "got   $1"
  else
    rm -f "$fonts/$1"
    echo "ERROR: couldn't download $1 from $2" >&2
    exit 1
  fi
}

# SF Pro lives on every Mac. Copy it for this build only (Apple's licence: don't share the file).
sf_pro() {
  if [ -f /System/Library/Fonts/SFNS.ttf ]; then
    cp -n /System/Library/Fonts/SFNS.ttf "$fonts/SFNS.ttf" 2>/dev/null || true
    echo "copied SF Pro from this Mac"
  else
    echo "SF Pro not found on this Mac: the template falls back to Inter ExtraBold"
  fi
}

case "$slug" in
  just-you)
    sf_pro
    get Inter-ExtraBold.ttf "$FS/inter@latest/latin-800-normal.ttf"
    get Inter-Bold.ttf      "$FS/inter@latest/latin-700-normal.ttf" ;;
  full)
    sf_pro
    get Inter-ExtraBold.ttf "$FS/inter@latest/latin-800-normal.ttf" ;;
  pop-up-proof)
    get Inter-Variable.ttf  "$GF/inter/Inter%5Bopsz,wght%5D.ttf"
    get DMMono-Medium.ttf   "$GF/dmmono/DMMono-Medium.ttf" ;;
  before-after-reveal)
    get BebasNeue-Regular.ttf   "$GF/bebasneue/BebasNeue-Regular.ttf"
    get Inter-Variable.ttf      "$GF/inter/Inter%5Bopsz,wght%5D.ttf"
    get JetBrainsMono-Medium.ttf "$FS/jetbrains-mono@latest/latin-500-normal.ttf" ;;
  pov-skit)
    get Poppins-SemiBold.ttf "$GF/poppins/Poppins-SemiBold.ttf" ;;
  codie-sanchez)
    get EBGaramond-VF.ttf        "$GF/ebgaramond/EBGaramond%5Bwght%5D.ttf"
    get EBGaramond-Italic-VF.ttf "$GF/ebgaramond/EBGaramond-Italic%5Bwght%5D.ttf"
    get Montserrat-VF.ttf        "$GF/montserrat/Montserrat%5Bwght%5D.ttf" ;;
  diary-of-a-ceo)
    # optional: makes the hook width exact (the build estimates without it)
    get Inter-Black.ttf "$FS/inter@latest/latin-900-normal.ttf" ;;
  iman-gadzhi)
    get Anton-Regular.ttf "$GF/anton/Anton-Regular.ttf"
    echo "Also run in the build folder: npx --yes hyperframes@0.9.83 add hw-write-title  (adds the Caveat pen + font)" ;;
  nana-del-rey)
    get InterTight-VariableFont_wght.ttf "$GF/intertight/InterTight%5Bwght%5D.ttf" ;;
  nick-saraev)
    get PlayfairDisplay-Italic.ttf "$GF/playfairdisplay/PlayfairDisplay-Italic%5Bwght%5D.ttf" ;;
  calm-luxury)
    get Newsreader-opsz-wght.ttf "$GF/newsreader/Newsreader%5Bopsz,wght%5D.ttf" ;;
  serialised-episode)
    get Archivo.ttf             "$GF/archivo/Archivo%5Bwdth,wght%5D.ttf"
    get ArchivoBlack-Regular.ttf "$GF/archivoblack/ArchivoBlack-Regular.ttf" ;;
  green-screen-proof)
    get SpaceGrotesk.ttf     "$GF/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf"
    get SpaceMono-Regular.ttf "$GF/spacemono/SpaceMono-Regular.ttf" ;;
  text-over-broll)
    get InstrumentSans.ttf "$GF/instrumentsans/InstrumentSans%5Bwdth,wght%5D.ttf" ;;
  timestamp-vlog)
    get JetBrainsMono.ttf          "$GF/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"
    get InstrumentSerif-Italic.ttf "$GF/instrumentserif/InstrumentSerif-Italic.ttf" ;;
  yes-but-split)
    get Anton-Regular.ttf "$GF/anton/Anton-Regular.ttf"
    get Inter-Bold.ttf    "$FS/inter@latest/latin-700-normal.ttf" ;;
  hormozi-classic|hormozi-2026|mariah-brunner)
    echo "$slug uses fonts HyperFrames loads by itself (Montserrat / Poppins / Inter). Nothing to download." ;;
  *)
    echo "ERROR: unknown template '$slug'" >&2
    exit 1 ;;
esac

echo "Fonts ready in $fonts"
