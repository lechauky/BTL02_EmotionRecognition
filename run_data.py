"""Bước 1 – Chuẩn bị và khảo sát dữ liệu FER2013.

    python run_data.py
Đọc data/fer2013.csv (hoặc giải nén fer2013.tar.gz) -> data/fer2013.npz, vẽ hình vào exps/_data/:
histogram số ảnh theo lớp ở 3 tập, ảnh mẫu, ảnh mẫu theo từng lớp; ghi thống kê vào exps/_data/data_stats.json.
"""
import json
import os

import numpy as np

from src import config as C
from src import data as D
from src import visualize as V


def main():
    data = D.prepare()
    os.makedirs(C.FIG_DIR, exist_ok=True)
    mean, std = D.train_stats(data["train"][0])
    stats = {"mean": mean, "std": std, "image_shape": list(data["train"][0].shape[1:])}
    for s, (x, y) in data.items():
        cnt = np.bincount(y, minlength=7)
        stats[s] = {"n": int(len(y)), "per_class": {c: int(n) for c, n in zip(C.CLASSES, cnt)},
                    "ratio": {c: round(float(n / len(y)), 4) for c, n in zip(C.CLASSES, cnt)}}
        print(f"{C.SPLITS[s]:12s} ({s}): {len(y):6d} ảnh  ", dict(zip(C.CLASSES, cnt.tolist())))
    json.dump(stats, open(os.path.join(C.FIG_DIR, "data_stats.json"), "w"), indent=2)
    V.plot_class_hist(data, os.path.join(C.FIG_DIR, "histogram_data.png"))
    V.plot_samples(*data["train"], os.path.join(C.FIG_DIR, "training_images.png"), title="Ảnh mẫu tập Training")
    V.plot_samples(*data["valid"], os.path.join(C.FIG_DIR, "validating_images.png"), title="Ảnh mẫu tập PublicTest")
    V.plot_per_class_samples(*data["train"], os.path.join(C.FIG_DIR, "samples_per_class.png"))
    # minh họa tăng cường dữ liệu
    import torch
    x = D.to_tensor(data["train"][0][:8], mean, std)
    rows = [x] + [D.augment_batch(x, "standard") for _ in range(2)] + [D.augment_batch(x, "strong") for _ in range(2)]
    imgs = torch.cat(rows).squeeze(1).numpy() * std + mean
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(5, 8, figsize=(10, 6.6))
    for k, ax in enumerate(axes.flat):
        ax.imshow(imgs[k], cmap="gray", vmin=0, vmax=1), ax.set_xticks([]), ax.set_yticks([])
    for r, t in enumerate(["gốc", "standard", "standard", "strong", "strong"]):
        axes[r, 0].set_ylabel(t, fontsize=9)
    fig.suptitle("Tăng cường dữ liệu: hàng 1 ảnh gốc, hàng 2–3 'standard', hàng 4–5 'strong'")
    fig.tight_layout()
    V.save(fig, os.path.join(C.FIG_DIR, "augmentation.png"))
    print("Đã lưu hình và thống kê vào", C.FIG_DIR)


if __name__ == "__main__":
    main()
