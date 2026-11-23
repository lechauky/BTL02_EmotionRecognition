"""Quản lý thực nghiệm: đặt tên, thư mục riêng cho mỗi lần chạy, metadata, sổ đăng ký (registry), W&B (tùy chọn).

Quy tắc đặt tên (mỗi lần chạy một thư mục, không ghi đè):
    exps/<nhóm>/<mã>_<dữ liệu>_<mô hình>_<tối ưu>_<thời điểm>/
    ví dụ  exps/A/A2_fer-std_medium-relu-bn_adam-1e-3_261123-1430/
      config.json      cấu hình đầy đủ của lần chạy
      meta.json        ai chạy, ngày giờ, máy/GPU, phiên bản, lệnh, commit git, phiên bản thứ mấy của mã này
      history.csv      loss/accuracy train-valid và lr từng epoch
      metrics.json     kết quả: epoch tốt nhất, accuracy/loss/F1 trên valid và test
      model_summary.txt, figures/*.png, README.md (tóm tắt + liên kết)
      checkpoints/best.pt   (không đưa lên GitHub; chép lên Google Drive)
"""
import datetime as dt
import glob
import json
import os
import platform
import subprocess
import sys

import pandas as pd

from . import config as C
from .experiments import EXPERIMENTS, GROUP_TITLES


def slug(cfg):
    data = "fer-" + {"none": "noaug", "standard": "std", "strong": "strong"}[cfg["augment"]]
    model = cfg["model"]
    if cfg["model"] in ("resnet18", "vgg16bn"):
        model += "-pre" if cfg["pretrained"] else "-scratch"
    else:
        model += f"-{cfg['activation']}" + ("-bn" if cfg["batchnorm"] else "-nobn")
        if cfg["dropout_conv"] == 0 and cfg["dropout_fc"] == 0:
            model += "-nodrop"
    opt = f"{cfg['optimizer']}-{cfg['lr']:g}" + (f"-ls{cfg['label_smoothing']:g}" if cfg["label_smoothing"] else "")
    return data, model, opt


def make_run_dir(key, cfg, author, note=""):
    group = EXPERIMENTS[key][0] if key in EXPERIMENTS else "X"
    now = C.now()
    data, model, opt = slug(cfg)
    run_id = f"{key}_{data}_{model}_{opt}_{now:%y%m%d-%H%M}"
    d = os.path.join(C.EXPS_DIR, group, run_id)
    os.makedirs(os.path.join(d, "figures"), exist_ok=True)
    os.makedirs(os.path.join(d, "checkpoints"), exist_ok=True)
    version = 1
    for mf in glob.glob(os.path.join(C.EXPS_DIR, group, f"{key}_*", "metrics.json")):
        try:
            version += 0 if json.load(open(mf)).get("quick") else 1
        except Exception:
            pass
    meta = {
        "run_id": run_id, "key": key, "group": group, "group_title": GROUP_TITLES.get(group, ""),
        "version": f"v{version}", "description": EXPERIMENTS.get(key, ("", "", {}))[1],
        "author": author or C.GROUP_OWNER.get(group, ""), "note": note,
        "start": now.isoformat(timespec="seconds"), "command": " ".join([os.path.basename(sys.argv[0])] + sys.argv[1:]),
        **env_info(),
    }
    json.dump(cfg, open(os.path.join(d, "config.json"), "w"), indent=2)
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=2, ensure_ascii=False)
    return d, meta


def env_info():
    import torch
    gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=C.ROOT, capture_output=True,
                                text=True, timeout=5).stdout.strip()
    except Exception:
        commit = ""
    colab = "google.colab" in sys.modules or os.path.exists("/content")
    return {"device": gpu, "platform": ("Google Colab, " if colab else "") + f"{platform.system()} {platform.release()}",
            "python": platform.python_version(), "torch": torch.__version__, "git_commit": commit}


def finish(d, meta, metrics):
    meta["end"] = C.now().isoformat(timespec="seconds")
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=2, ensure_ascii=False)
    json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
    write_readme(d, meta, metrics)


def links(meta):
    rel = f"exps/{meta['group']}/{meta['run_id']}"
    gh = f"{C.GITHUB_REPO}/tree/{C.GITHUB_BRANCH}/{rel}" if C.GITHUB_REPO else ""
    return rel, gh


def write_readme(d, meta, m):
    cfg = json.load(open(os.path.join(d, "config.json")))
    rel, gh = links(meta)
    figs = sorted(os.listdir(os.path.join(d, "figures")))
    lines = [f"# {meta['run_id']}", "",
             f"- **Thực nghiệm:** {meta['key']} – {meta['description']} (nhóm {meta['group']}: {meta['group_title']})",
             f"- **Phiên bản:** {meta['version']} · **Người chạy:** {meta['author']} · **Thời gian:** {meta['start']} → {meta.get('end', '')}",
             f"- **Máy:** {meta['platform']}, {meta['device']}, Python {meta['python']}, PyTorch {meta['torch']}"
             + (f", commit `{meta['git_commit']}`" if meta.get("git_commit") else ""),
             f"- **Lệnh:** `{meta['command']}`", "",
             "## Kết quả", "",
             "| Chỉ số | Valid (PublicTest) | Test (PrivateTest) |", "|---|---|---|",
             f"| Accuracy | {m['valid_acc']:.4f} | {m['test_acc']:.4f} |",
             f"| Loss | {m['valid_loss']:.4f} | {m['test_loss']:.4f} |",
             f"| Macro-F1 | {m['valid_f1']:.4f} | {m['test_f1']:.4f} |", "",
             f"Epoch tốt nhất (val_loss nhỏ nhất): **{m['best_epoch']}** / {m['epochs_run']} epoch · "
             f"{m['n_params']:,d} tham số · {m['train_time_s'] / 60:.1f} phút", "",
             "## Cấu hình", "", "```json", json.dumps(cfg, indent=2), "```", "",
             "## Hình", ""] + [f"![{f}](figures/{f})" for f in figs]
    if C.DRIVE_WEIGHTS_URL:
        lines += ["", f"Trọng số: `checkpoints/best.pt` – bản lưu trên Google Drive: {C.DRIVE_WEIGHTS_URL}"]
    open(os.path.join(d, "README.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


def scan():
    """Quét mọi exps/*/*/metrics.json -> DataFrame (1 dòng / lần chạy) và ghi exps/registry.csv."""
    rows = []
    for mf in sorted(glob.glob(os.path.join(C.EXPS_DIR, "*", "*", "metrics.json"))):
        d = os.path.dirname(mf)
        try:
            meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
            cfg = json.load(open(os.path.join(d, "config.json")))
            m = json.load(open(mf))
        except Exception as e:
            print("bỏ qua", d, e)
            continue
        rel, gh = links(meta)
        rows.append({**{k: meta.get(k, "") for k in ("run_id", "key", "group", "version", "author", "description",
                                                     "start", "end", "device", "platform", "python", "torch",
                                                     "git_commit", "command", "note")},
                     **{f"cfg_{k}": v for k, v in cfg.items()}, **m, "folder": rel, "github": gh})
    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(["start", "run_id"]).reset_index(drop=True)
        # phiên bản v1, v2, … của mỗi mã chỉ tính các lần chạy chính thức (không tính --quick), theo thứ tự thời gian
        off = ~df["quick"].astype(bool)
        df.loc[off, "version"] = "v" + (df[off].groupby("key").cumcount() + 1).astype(str)
        df.loc[~off, "version"] = "quick"
        df.to_csv(C.REGISTRY_CSV, index=False)
    return df


class WandbLogger:
    """Ghi lên Weights & Biases nếu bật --wandb (tùy chọn)."""

    def __init__(self, mode, meta, cfg):
        self.run = None
        if mode in ("online", "offline"):
            try:
                import wandb
                self.run = wandb.init(project=os.environ.get("WANDB_PROJECT", "btl02-fer2013"), mode=mode,
                                      group=meta["group"], job_type=meta["key"], name=meta["run_id"],
                                      tags=[meta["key"], meta["version"], meta["author"]], config={**cfg, **meta})
            except Exception as e:
                print("[wandb] tắt:", e)

    def log(self, row):
        if self.run:
            self.run.log(row, step=row["epoch"])

    def finish(self, metrics):
        if self.run:
            self.run.summary.update(metrics)
            url = self.run.url
            self.run.finish()
            return url
        return ""
