#!/bin/bash
# OCR every page of the ICD-9-CM book into TSV (word boxes) for parsing
S=/mnt/user-data/uploads/S0034.pdf
OUT=/home/claude/src/ocr9
N=$(pdfinfo "$S" | awk '/^Pages/{print $2}')
doit() {
  p=$1; f=$(printf "%s/p%03d" "$OUT" "$p")
  [ -s "$f.tsv" ] && return
  pdftoppm -f $p -l $p -r 300 -gray -png -singlefile "$S" "$f" && tesseract "$f.png" "$f" -l eng --psm 4 tsv >/dev/null 2>&1
}
export -f doit; export S OUT
seq 1 $N | xargs -P 2 -I{} bash -c 'doit {}'
echo DONE > $OUT/_done
