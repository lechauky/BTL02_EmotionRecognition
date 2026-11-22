"""Vòng lặp huấn luyện tự viết bằng PyTorch.

Mỗi epoch:  model.train() -> với từng batch: tăng cường dữ liệu -> forward -> loss -> zero_grad -> backward -> step
            model.eval() + torch.no_grad() -> đánh giá trên valid (PublicTest)
Callback (tương đương bài mẫu Keras): ModelCheckpoint (lưu khi val_loss giảm), CSVLogger (history.csv),
EarlyStopping (patience), ReduceLROnPlateau. Dùng mixed precision (AMP) khi có GPU.
"""
import os
import random
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from .data import augment_batch


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def make_optimizer(model, cfg):
    p = model.parameters()
    if cfg["optimizer"] == "sgd":
        return torch.optim.SGD(p, lr=cfg["lr"], momentum=cfg["momentum"], weight_decay=cfg["weight_decay"], nesterov=True)
    if cfg["optimizer"] == "adamw":
        return torch.optim.AdamW(p, lr=cfg["lr"], weight_decay=cfg["weight_decay"] or 1e-2)
    return torch.optim.Adam(p, lr=cfg["lr"], weight_decay=cfg["weight_decay"])


@torch.no_grad()
def evaluate_loader(model, loader, criterion=None, tta=False):
    """Trả về (loss trung bình, accuracy, nhãn thật, xác suất dự đoán)."""
    model.eval()
    criterion = criterion or nn.CrossEntropyLoss()
    tot, n, ys, ps = 0.0, 0, [], []
    for x, y in loader:
        with torch.autocast(device_type=x.device.type, enabled=x.device.type == "cuda"):
            logits = model(x)
            if tta:                                          # test-time augmentation: trung bình với ảnh lật ngang
                logits = (logits.float().softmax(1) + model(torch.flip(x, dims=[3])).float().softmax(1)).log()
        logits = logits.float()
        tot += criterion(logits, y).item() * len(y)
        n += len(y)
        ys.append(y.cpu())
        ps.append(logits.softmax(1).cpu())
    y = torch.cat(ys).numpy()
    p = torch.cat(ps).numpy()
    return tot / n, float((p.argmax(1) == y).mean()), y, p


def train_model(model, loaders, cfg, run_dir, logger=None, verbose=True):
    device = next(model.parameters()).device
    set_seed(cfg["seed"])
    opt = make_optimizer(model, cfg)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=cfg["lr_factor"], patience=cfg["lr_patience"],
                                                       min_lr=cfg["min_lr"])
    criterion = nn.CrossEntropyLoss(label_smoothing=cfg["label_smoothing"])
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")
    ckpt = os.path.join(run_dir, "checkpoints", "best.pt")
    best, best_epoch, wait, hist = float("inf"), 0, 0, []
    t0 = time.time()
    for epoch in range(1, cfg["epochs"] + 1):
        te = time.time()
        model.train()
        tl, tc, tn = 0.0, 0, 0
        for x, y in loaders["train"]:
            x = augment_batch(x, cfg["augment"])
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                out = model(x)                                   # 1. forward
                loss = criterion(out, y)                         # 2. loss
            opt.zero_grad(set_to_none=True)                      # 3. xóa gradient cũ
            scaler.scale(loss).backward()                        # 4. lan truyền ngược
            scaler.step(opt)                                     # 5. cập nhật trọng số
            scaler.update()
            tl += loss.item() * len(y)
            tc += (out.argmax(1) == y).sum().item()
            tn += len(y)
        vl, va, _, _ = evaluate_loader(model, loaders["valid"])
        lr = opt.param_groups[0]["lr"]
        row = {"epoch": epoch, "train_loss": tl / tn, "train_acc": tc / tn, "val_loss": vl, "val_acc": va,
               "lr": lr, "epoch_time_s": time.time() - te}
        hist.append(row)
        pd.DataFrame(hist).to_csv(os.path.join(run_dir, "history.csv"), index=False)   # CSVLogger
        if logger:
            logger.log(row)
        improved = vl < best - 1e-4
        if improved:                                             # ModelCheckpoint(save_best_only, monitor=val_loss)
            best, best_epoch, wait = vl, epoch, 0
            torch.save({"model": model.state_dict(), "cfg": cfg, "epoch": epoch, "val_loss": vl, "val_acc": va}, ckpt)
        else:
            wait += 1
        if verbose:
            print(f"epoch {epoch:3d} | train loss {tl / tn:.4f} acc {tc / tn:.4f} | val loss {vl:.4f} acc {va:.4f} | "
                  f"lr {lr:.1e} | {time.time() - te:.1f}s {'*' if improved else ''}", flush=True)
        sched.step(vl)                                           # ReduceLROnPlateau
        if wait >= cfg["early_stopping"]:                        # EarlyStopping
            if verbose:
                print(f"Dừng sớm ở epoch {epoch} (val_loss không giảm {wait} epoch).")
            break
    state = torch.load(ckpt, map_location=device)
    model.load_state_dict(state["model"])
    return pd.DataFrame(hist), {"best_epoch": best_epoch, "epochs_run": len(hist), "train_time_s": time.time() - t0}
