"""Hình vẽ: khảo sát dữ liệu, đường học, ma trận nhầm lẫn, ca đúng/sai, bộ lọc tích chập và bản đồ đặc trưng."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402

from . import config as C  # noqa: E402

BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 110})


def save(fig, path):
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_class_hist(data, path):
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.8), sharey=False)
    names = {"train": "Training (train)", "valid": "PublicTest (valid)", "test": "PrivateTest (test)"}
    for ax, (s, (_, y)) in zip(axes, data.items()):
        cnt = np.bincount(y, minlength=7)
        b = ax.bar(range(7), cnt, color=BLUE)
        ax.bar_label(b, fontsize=8)
        ax.set_xticks(range(7), C.CLASSES, rotation=35)
        ax.set_title(f"{names[s]} – {len(y):,} ảnh")
    axes[0].set_ylabel("Số ảnh")
    fig.tight_layout()
    save(fig, path)


def plot_samples(x, y, path, rows=4, cols=8, title=None, pred=None, seed=0):
    idx = np.random.default_rng(seed).choice(len(x), rows * cols, replace=False)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 1.45, rows * 1.65))
    for ax, i in zip(axes.flat, idx):
        ax.imshow(x[i], cmap="gray", vmin=0, vmax=255)
        t = C.CLASSES[y[i]] if pred is None else f"T:{C.CLASSES[y[i]]}\nP:{C.CLASSES[pred[i]]}"
        ax.set_title(t, fontsize=8, color="k" if pred is None or pred[i] == y[i] else "#c0392b")
        ax.axis("off")
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    save(fig, path)


def plot_per_class_samples(x, y, path, n=8, seed=0):
    rng = np.random.default_rng(seed)
    fig, axes = plt.subplots(7, n, figsize=(n * 1.2, 7 * 1.3))
    for c in range(7):
        idx = rng.choice(np.where(y == c)[0], n, replace=False)
        for j, i in enumerate(idx):
            ax = axes[c, j]
            ax.imshow(x[i], cmap="gray", vmin=0, vmax=255)
            ax.set_xticks([]), ax.set_yticks([])
            if j == 0:
                ax.set_ylabel(C.CLASSES[c], fontsize=9, rotation=0, ha="right", va="center")
    fig.tight_layout()
    save(fig, path)


def plot_history(hist, path, best_epoch=None, title=""):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.8))
    a1.plot(hist["epoch"], hist["train_loss"], color=BLUE, label="train")
    a1.plot(hist["epoch"], hist["val_loss"], color=ORANGE, label="valid")
    a2.plot(hist["epoch"], hist["train_acc"], color=BLUE, label="train")
    a2.plot(hist["epoch"], hist["val_acc"], color=ORANGE, label="valid")
    for a, t in ((a1, "Loss (cross-entropy)"), (a2, "Accuracy")):
        if best_epoch:
            a.axvline(best_epoch, color=GREY, ls="--", lw=1)
        a.set_xlabel("epoch"), a.set_title(t), a.legend(frameon=False)
    if best_epoch:
        r = hist[hist["epoch"] == best_epoch].iloc[0]
        a2.annotate(f"best epoch {best_epoch}\nval_acc {r['val_acc']:.3f}", (best_epoch, r["val_acc"]),
                    xytext=(8, -30), textcoords="offset points", fontsize=8, color=GREY)
    if title:
        fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    save(fig, path)


def plot_confusion(cm, path, title=""):
    cmn = cm / cm.sum(1, keepdims=True)
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    for i in range(7):
        for j in range(7):
            ax.text(j, i, f"{cmn[i, j]:.2f}\n({cm[i, j]})", ha="center", va="center", fontsize=7,
                    color="white" if cmn[i, j] > 0.55 else "black")
    ax.set_xticks(range(7), C.CLASSES, rotation=35), ax.set_yticks(range(7), C.CLASSES)
    ax.set_xlabel("Dự đoán"), ax.set_ylabel("Nhãn thật"), ax.set_title(title or "Ma trận nhầm lẫn (chuẩn hóa theo hàng)")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    save(fig, path)


def plot_cases(x, y, p, path, correct, n=24, seed=0, title=""):
    pred = p.argmax(1)
    pool = np.where((pred == y) == correct)[0]
    idx = np.random.default_rng(seed).choice(pool, min(n, len(pool)), replace=False)
    cols = 8
    rows = int(np.ceil(len(idx) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 1.5, rows * 1.8))
    for ax in axes.flat:
        ax.axis("off")
    for ax, i in zip(axes.flat, idx):
        ax.imshow(x[i], cmap="gray", vmin=0, vmax=255)
        ax.set_title(f"T:{C.CLASSES[y[i]]}\nP:{C.CLASSES[pred[i]]} {p[i, pred[i]]:.2f}", fontsize=7,
                     color=GREEN if correct else "#c0392b")
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    save(fig, path)


def _grid(w, path, title, ncol=16):
    n = w.shape[0]
    rows = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(rows, ncol, figsize=(ncol * 0.62, rows * 0.66))
    for ax in np.atleast_1d(axes).flat:
        ax.axis("off")
    for i, ax in zip(range(n), np.atleast_1d(axes).flat):
        f = w[i]
        ax.imshow((f - f.min()) / (f.max() - f.min() + 1e-8), cmap="gray", interpolation="nearest")
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    save(fig, path)


def plot_filters(model, path_first, path_last):
    """Bộ lọc 3×3 của tầng tích chập đầu tiên và cuối cùng.
    Tầng cuối có C_in kênh vào: hiển thị trung bình theo kênh vào (mỗi ô là 1 bộ lọc)."""
    from .models import last_conv
    c0, cl = last_conv(model)
    w0 = c0.weight.detach().float().cpu().numpy()
    wl = cl.weight.detach().float().cpu().numpy()
    _grid(w0.mean(1), path_first, f"Bộ lọc tầng conv đầu tiên ({w0.shape[0]} bộ lọc {w0.shape[2]}×{w0.shape[3]})")
    _grid(wl.mean(1)[:128], path_last, f"Bộ lọc tầng conv cuối ({wl.shape[0]} bộ lọc {wl.shape[2]}×{wl.shape[3]}×{wl.shape[1]}, "
                                       f"hiển thị {min(128, wl.shape[0])} bộ lọc, trung bình theo kênh vào)")


@torch.no_grad()
def plot_feature_maps(model, x_img, mean, std, path, title=""):
    """Bản đồ đặc trưng (feature map) đầu ra của tầng conv cuối cho một ảnh: thấy rõ hơn bộ lọc 'nhìn' vào đâu."""
    from .models import last_conv
    _, cl = last_conv(model)
    out = {}
    h = cl.register_forward_hook(lambda m, i, o: out.setdefault("a", o.detach().float().cpu()))
    dev = next(model.parameters()).device
    t = ((torch.from_numpy(x_img).float() / 255 - mean) / std)[None, None].to(dev)
    model.eval()
    model(t)
    h.remove()
    a = out["a"][0].numpy()
    order = np.argsort(-a.mean((1, 2)))[:31]
    fig, axes = plt.subplots(4, 8, figsize=(12, 6.2))
    axes[0, 0].imshow(x_img, cmap="gray")
    axes[0, 0].set_title("ảnh vào", fontsize=8)
    for ax, k in zip(axes.flat[1:], order):
        ax.imshow(a[k], cmap="viridis")
        ax.set_title(f"kênh {k}", fontsize=7)
    for ax in axes.flat:
        ax.axis("off")
    fig.suptitle(title or f"31 bản đồ đặc trưng mạnh nhất của tầng conv cuối ({a.shape[1]}×{a.shape[2]})", fontsize=10)
    fig.tight_layout()
    save(fig, path)


def plot_compare(df, metric_cols, labels, path, title, ylabel="Accuracy"):
    fig, ax = plt.subplots(figsize=(max(6, 1.1 * len(df) + 2), 3.8))
    w = 0.8 / len(metric_cols)
    colors = [BLUE, ORANGE, GREEN]
    for k, (c, lab) in enumerate(zip(metric_cols, labels)):
        b = ax.bar(np.arange(len(df)) + (k - (len(metric_cols) - 1) / 2) * w, df[c], w, label=lab, color=colors[k])
        ax.bar_label(b, fmt="%.3f", fontsize=7)
    ax.set_xticks(range(len(df)), df["label"], rotation=0)
    lo = max(0, df[metric_cols].min().min() - 0.08)
    ax.set_ylim(lo, min(1, df[metric_cols].max().max() + 0.05))
    ax.set_ylabel(ylabel), ax.set_title(title), ax.legend(frameon=False, ncol=len(metric_cols))
    fig.tight_layout()
    save(fig, path)
