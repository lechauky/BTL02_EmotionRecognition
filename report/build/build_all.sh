#!/bin/bash
# build_all.sh <exps_dir> <outdir>  — dựng báo cáo (2 lượt để có mục lục) + slide + citations.json
set -e
SK=/root/.claude/skills/synced/117df563-f264-4049-ae4c-3cab3fda8068_99847f63-6dff-451b-a159-3f0f90f5ee03
B=/home/claude/fer/build; O=$2; mkdir -p $O
python3 $B/collect.py $1 $O/data.json
python3 $B/charts.py $O/data.json $O && CHART_DIR=$O PPTX_SKILL=$SK/pptx node $B/slides.js $O/data.json $O/slides.pptx $O/cit_slides.json
rm -f $O/toc.json
node $B/report.js $O/data.json $O/report.docx $O/cit_report.json
(cd $O && python3 $SK/docx/scripts/office/soffice.py --headless --convert-to pdf report.docx >/dev/null 2>&1)
python3 $B/toc.py $O/report.pdf $O/report.docx.heads.json $O/toc.json
TOC_JSON=$O/toc.json node $B/report.js $O/data.json $O/report.docx $O/cit_report.json
zip -d $O/report.docx '*/' >/dev/null 2>&1 || true
(cd $O && python3 $SK/docx/scripts/office/soffice.py --headless --convert-to pdf report.docx >/dev/null 2>&1 && python3 $SK/pptx/scripts/office/soffice.py --headless --convert-to pdf slides.pptx >/dev/null 2>&1)
python3 $B/toc.py $O/report.pdf $O/report.docx.heads.json $O/toc2.json
python3 - "$O" <<'PY'
import json,sys
o=sys.argv[1]; a=json.load(open(o+"/toc.json")); b=json.load(open(o+"/toc2.json"))
print("mục lục ổn định" if a==b else "MỤC LỤC LỆCH: "+str({k:(a.get(k),b.get(k)) for k in a if a.get(k)!=b.get(k)}))
c=json.load(open(o+"/cit_report.json"))+json.load(open(o+"/cit_slides.json"))
json.dump(c,open(o+"/citations.json","w"),ensure_ascii=False,indent=1); print("citations:",len(c))
PY
pdfinfo $O/report.pdf | grep Pages; pdfinfo $O/slides.pdf | grep Pages
