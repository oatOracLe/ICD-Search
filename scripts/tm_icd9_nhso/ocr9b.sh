#!/bin/bash
# Re-OCR tabular pages with grey box fills removed (threshold), so codes on grey are read
OUT=/home/claude/src/ocr9b
doit() {
  p=$1; f=$(printf "%03d" "$p")
  [ -s "$OUT/p$f.tsv" ] && return
  python3 -c "
import cv2,sys
im=cv2.imread('/home/claude/src/ocr9/p$f.png',0)
_,b=cv2.threshold(im,140,255,cv2.THRESH_BINARY)
cv2.imwrite('$OUT/p$f.png',b)"
  tesseract "$OUT/p$f.png" "$OUT/p$f" -l eng --psm 4 tsv >/dev/null 2>&1 && rm -f "$OUT/p$f.png"
}
export -f doit; export OUT
seq 11 282 | xargs -P 2 -I{} bash -c 'doit {}'
echo DONE > $OUT/_done
