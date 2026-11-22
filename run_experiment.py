"""Bước 2 – Chạy thực nghiệm. Mỗi lần chạy tạo một thư mục riêng trong exps/<nhóm>/ (xem src/tracking.py).

    python run_experiment.py --exp A2                    # một thực nghiệm
    python run_experiment.py --group B --author "Lê Châu Kỳ"   # cả nhóm B
    python run_experiment.py --exp A2 --quick            # chạy thử nhanh (2.000 ảnh, 2 epoch) để kiểm tra code
    python run_experiment.py --list                      # xem danh sách thực nghiệm
Tùy chọn: --epochs N, --seed S, --note "...", --wandb online|offline
"""
import argparse
import json
import os
import shutil

import torch

from src import config as C
from src import data as D
from src import evaluate as E
from src import tracking as T
from src import visualize as V
from src.experiments import EXPERIMENTS, keys_of_group
from src.models import build_model, count_params, summary
from src.train import evaluate_loader, get_device, set_seed, train_model


def run_one(key, data, args):
    group, desc, override = EXPERIMENTS[key]
    cfg = {**C.BASELINE, **override}
    if args.epochs:
        cfg["epochs"] = args.epochs
    if args.seed is not None:
        cfg["seed"] = args.seed
    if args.quick:
        cfg["epochs"] = args.epochs or 2
    run_dir, meta = T.make_run_dir(key, cfg, args.author, (args.note + " [quick]" if args.quick else args.note).strip())
    print(f"\n=== {key}: {desc}\n    thư mục: {run_dir}\n    người chạy: {meta['author']} | {meta['device']} | {meta['version']}")
    device = get_device()
    set_seed(cfg["seed"])
    loaders, (mean, std) = D.make_loaders(data, cfg["batch_size"], device, limit=(args.limit or 2000) if args.quick else None, seed=cfg["seed"])
    model = build_model(cfg).to(device)
    open(os.path.join(run_dir, "model_summary.txt"), "w", encoding="utf-8").write(f"{desc}\n\n{model}\n\n{summary(model)}\n")
    logger = T.WandbLogger(args.wandb, meta, cfg)
    hist, info = train_model(model, loaders, cfg, run_dir, logger=logger)

    res = {}
    for s in ("valid", "test"):
        loss, acc, y, p = evaluate_loader(model, loaders[s])
        m = E.metrics(y, p)
        res[s] = (loss, m, y, p)
        open(os.path.join(run_dir, f"classification_report_{s}.txt"), "w").write(m["report_txt"])
    fig = lambda n: os.path.join(run_dir, "figures", n)  # noqa: E731
    V.plot_history(hist, fig("training_curves.png"), info["best_epoch"], title=meta["run_id"])
    V.plot_confusion(res["valid"][1]["cm"], fig("confusion_valid.png"), f"{key} – ma trận nhầm lẫn PublicTest (valid)")
    V.plot_confusion(res["test"][1]["cm"], fig("confusion_test.png"), f"{key} – ma trận nhầm lẫn PrivateTest (test)")
    V.plot_filters(model, fig("filters_first_conv.png"), fig("filters_last_conv.png"))
    xt = data["test"][0][: len(res["test"][2])]
    if cfg["model"] not in ("resnet18", "vgg16bn"):
        V.plot_feature_maps(model, xt[0], mean, std, fig("feature_maps_last_conv.png"))
    V.plot_cases(xt, res["test"][2], res["test"][3], fig("wrong_cases.png"), correct=False, title=f"{key} – ca dự đoán SAI (PrivateTest)")
    V.plot_cases(xt, res["test"][2], res["test"][3], fig("true_cases.png"), correct=True, title=f"{key} – ca dự đoán ĐÚNG (PrivateTest)")

    metrics = {**info, "n_params": count_params(model),
               "valid_loss": res["valid"][0], "valid_acc": res["valid"][1]["acc"], "valid_f1": res["valid"][1]["f1"],
               "test_loss": res["test"][0], "test_acc": res["test"][1]["acc"], "test_f1": res["test"][1]["f1"],
               "train_acc_last": float(hist["train_acc"].iloc[-1]),
               "train_acc_at_best": float(hist.loc[hist["epoch"] == info["best_epoch"], "train_acc"].iloc[0]),
               "per_class_test": E.per_class_table(res["test"][1]["report"]),
               "confusion_test": res["test"][1]["cm"].tolist(), "quick": bool(args.quick)}
    metrics["wandb_url"] = logger.finish({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
    T.finish(run_dir, meta, metrics)
    if C.WEIGHTS_DIR:                                    # chép trọng số lên Google Drive (khi chạy Colab)
        dst = os.path.join(C.WEIGHTS_DIR, meta["group"], meta["run_id"])
        os.makedirs(dst, exist_ok=True)
        shutil.copy(os.path.join(run_dir, "checkpoints", "best.pt"), dst)
    print(f"--> {key}: valid acc {metrics['valid_acc']:.4f} | test acc {metrics['test_acc']:.4f} | "
          f"best epoch {info['best_epoch']} | {info['train_time_s'] / 60:.1f} phút")
    del model
    torch.cuda.empty_cache()
    return run_dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", nargs="*", default=[])
    ap.add_argument("--group", nargs="*", default=[])
    ap.add_argument("--author", default=None, help="người chạy (mặc định: người phụ trách nhóm thực nghiệm)")
    ap.add_argument("--note", default="")
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--quick", action="store_true", help="chạy thử: 2.000 ảnh (--limit), 2 epoch; không vào nhật ký chính thức")
    ap.add_argument("--limit", type=int, default=None, help="số ảnh train khi --quick")
    ap.add_argument("--wandb", default="off", choices=["off", "online", "offline"])
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.list:
        for k, (g, d, o) in EXPERIMENTS.items():
            print(f"{k:3s} [{g}] {d}  {o}")
        return
    keys = list(args.exp) + [k for g in args.group for k in keys_of_group(g)]
    if not keys:
        ap.error("chọn --exp hoặc --group")
    data = D.prepare()
    for k in keys:
        run_one(k, data, args)
    df = T.scan()
    print(f"\nĐã ghi {len(df)} lần chạy vào {os.path.relpath(C.REGISTRY_CSV, C.ROOT)}")
    try:
        from make_log import build
        build()
    except Exception as e:
        print("(chưa dựng được file Excel:", e, ")")


if __name__ == "__main__":
    main()
