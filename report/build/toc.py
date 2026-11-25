"""Tìm số trang của từng đề mục trong PDF đã dựng -> toc.json"""
import json, sys, subprocess, re
heads = json.load(open(sys.argv[2]))
pages = subprocess.run(["pdftotext", "-layout", sys.argv[1], "-"], capture_output=True, text=True).stdout.split("\f")
norm = lambda x: re.sub(r"\s+", " ", x).strip()
out, start = {"__order": heads}, 2
for h in heads:
    for i in range(start, len(pages)):
        if any(norm(l) == norm(h) for l in pages[i].splitlines()):
            out[h] = i + 1; start = i; break
json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False)
print(sum(1 for h in heads if h in out), "/", len(heads))
