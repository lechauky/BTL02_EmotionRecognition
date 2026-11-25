"""Gom dữ liệu từ exps/ -> build/data.json để dựng báo cáo và slide (mọi con số lấy thẳng từ thư mục thực nghiệm)."""
import datetime as dt, glob, json, os, sys
import pandas as pd

EXPS = sys.argv[1]
OUT = sys.argv[2]
REPO = "https://github.com/lechauky/BTL02_EmotionRecognition"


def gh(rel):
    return f"{REPO}/tree/main/{rel}"


def blob(rel):
    return f"{REPO}/blob/main/{rel}"


def vn(s):
    """Giờ Việt Nam: bản cũ (B v1) ghi giờ UTC không múi giờ -> cộng 7 giờ."""
    if not s:
        return s
    t = dt.datetime.fromisoformat(s)
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(dt.timezone(dt.timedelta(hours=7))).isoformat(timespec="seconds")


runs = []
for mf in sorted(glob.glob(os.path.join(EXPS, "[ABCD]", "*", "metrics.json"))):
    d = os.path.dirname(mf)
    m = json.load(open(mf))
    if m.get("quick"):
        continue
    meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
    cfg = json.load(open(os.path.join(d, "config.json")))
    h = pd.read_csv(os.path.join(d, "history.csv"))
    rel = os.path.relpath(d, os.path.dirname(EXPS)).replace("\\", "/")
    figs = sorted(os.listdir(os.path.join(d, "figures"))) if os.path.isdir(os.path.join(d, "figures")) else []
    runs.append(dict(run_id=meta["run_id"], key=meta["key"], group=meta["group"], author=meta["author"],
                     description=meta["description"], start=vn(meta["start"]), end=vn(meta.get("end", "")),
                     device=meta.get("device", ""), commit=meta.get("git_commit", ""), cfg=cfg,
                     metrics={k: v for k, v in m.items() if not isinstance(v, (dict, list))},
                     per_class_test=m.get("per_class_test"), confusion_test=m.get("confusion_test"),
                     history=h.to_dict(orient="list"), folder=rel, url=gh(rel), dir=d,
                     figures={f[:-4]: os.path.join(d, "figures", f) for f in figs if f.endswith(".png")}))
runs.sort(key=lambda r: r["start"])
ver = {}
for r in runs:
    ver[r["key"]] = ver.get(r["key"], 0) + 1
    r["version"] = f"v{ver[r['key']]}"
latest = {}
for r in runs:
    latest[r["key"]] = r                       # phiên bản mới nhất của mỗi mã

fin = []
for ff in glob.glob(os.path.join(EXPS, "FINAL", "*", "final_result.json")):
    d = os.path.dirname(ff)
    f = json.load(open(ff, encoding="utf-8"))
    rel = os.path.relpath(d, os.path.dirname(EXPS)).replace("\\", "/")
    f.update(dir=d, folder=rel, url=gh(rel),
             figures={x[:-4]: os.path.join(d, x) for x in sorted(os.listdir(d)) if x.endswith(".png")})
    fin.append(f)
fin.sort(key=lambda f: f["evaluated_at"])
summary = {x[:-4]: os.path.join(EXPS, "_summary", x) for x in os.listdir(os.path.join(EXPS, "_summary")) if x.endswith(".png")}
datafig = {x[:-4]: os.path.join(EXPS, "_data", x) for x in os.listdir(os.path.join(EXPS, "_data")) if x.endswith(".png")}
stats = json.load(open(os.path.join(EXPS, "_data", "data_stats.json")))
json.dump(dict(runs=runs, latest=latest, final=fin[-1] if fin else None, summary=summary, datafig=datafig,
               stats=stats, repo=REPO), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(len(runs), "lần chạy;", len(latest), "mã;", "FINAL:", fin[-1]["run_id"] if fin else None)
