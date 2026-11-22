"""Dữ liệu FER2013: đọc csv, cache npz, tăng cường dữ liệu trên GPU, DataLoader.

fer2013.csv có 3 cột: emotion (0..6), pixels (2304 số 0..255 cách nhau bởi dấu cách), Usage
(Training 28.709 ảnh / PublicTest 3.589 / PrivateTest 3.589).
Quy ước của nhóm (giống bài mẫu):  Training -> train,  PublicTest -> valid (chọn mô hình, early stopping),
PrivateTest -> test (chỉ dùng để báo cáo kết quả cuối).
"""
import glob
import math
import os
import tarfile

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from . import config as C


def find_source(data_dir=None):
    d = data_dir or C.DATA_DIR
    for pat in ("fer2013.csv", "*/fer2013.csv", "**/fer2013.csv", "icml_face_data.csv"):
        hits = glob.glob(os.path.join(d, pat), recursive=True)
        if hits:
            return hits[0]
    zips = glob.glob(os.path.join(d, "fer2013*.zip")) + glob.glob(os.path.join(d, "**/fer2013*.zip"), recursive=True)
    if zips:
        import zipfile
        print("Giải nén", zips[0])
        with zipfile.ZipFile(zips[0]) as z:
            z.extractall(d)
        return find_source(d)
    tars = glob.glob(os.path.join(d, "fer2013*.tar.gz")) + glob.glob(os.path.join(d, "**/fer2013*.tar.gz"), recursive=True)
    if tars:
        print("Giải nén", tars[0])
        with tarfile.open(tars[0]) as t:
            t.extractall(d)
        return find_source(d)
    raise FileNotFoundError(
        f"Không thấy fer2013.csv / fer2013.csv.zip / fer2013.tar.gz trong {d}. Tải từ Kaggle: "
        "https://www.kaggle.com/datasets/deadskull7/fer2013")


def prepare(data_dir=None, force=False):
    """Đọc csv -> data/fer2013.npz (uint8). Trả về dict split -> (x[N,48,48], y[N])."""
    d = data_dir or C.DATA_DIR
    cache = os.path.join(d, "fer2013.npz")
    if os.path.exists(cache) and not force:
        z = np.load(cache)
        return {s: (z[f"x_{s}"], z[f"y_{s}"]) for s in C.SPLITS}
    import pandas as pd
    src = find_source(d)
    df = pd.read_csv(src)
    df.columns = [c.strip().lower() for c in df.columns]           # icml_face_data.csv có cột " pixels"
    px = np.stack([np.asarray(p.split(), dtype=np.uint8) for p in df["pixels"]]).reshape(-1, 48, 48)
    y = df["emotion"].to_numpy(np.int64)
    usage = df["usage"].str.strip().to_numpy()
    out = {s: (px[usage == u], y[usage == u]) for s, u in C.SPLITS.items()}
    np.savez_compressed(cache, **{f"x_{s}": v[0] for s, v in out.items()}, **{f"y_{s}": v[1] for s, v in out.items()})
    return out


def train_stats(x_train):
    x = x_train.astype(np.float32) / 255.0
    return float(x.mean()), float(x.std())


def to_tensor(x, mean, std):
    return ((torch.from_numpy(x).float() / 255.0 - mean) / std).unsqueeze(1)   # N,1,48,48


AUG = {
    "none": None,
    "standard": dict(rot=10, shift=0.10, zoom=0.10, flip=True, erase=0.0),   # như bài mẫu
    "strong": dict(rot=20, shift=0.15, zoom=0.15, flip=True, erase=0.5),
}


def augment_batch(x, mode):
    """Tăng cường ngẫu nhiên từng ảnh trong batch, làm trực tiếp trên GPU bằng affine_grid (nhanh hơn PIL)."""
    p = AUG[mode]
    if p is None:
        return x
    n = x.shape[0]
    dev = x.device
    ang = (torch.rand(n, device=dev) * 2 - 1) * math.radians(p["rot"])
    sc = 1 + (torch.rand(n, device=dev) * 2 - 1) * p["zoom"]
    tx, ty = [(torch.rand(n, device=dev) * 2 - 1) * p["shift"] * 2 for _ in range(2)]
    flip = torch.where(torch.rand(n, device=dev) < 0.5, -1.0, 1.0) if p["flip"] else torch.ones(n, device=dev)
    cos, sin = torch.cos(ang) / sc, torch.sin(ang) / sc
    theta = torch.stack([torch.stack([cos * flip, -sin, tx], 1), torch.stack([sin * flip, cos, ty], 1)], 1)
    grid = F.affine_grid(theta, x.shape, align_corners=False)
    out = F.grid_sample(x, grid, mode="bilinear", padding_mode="border", align_corners=False)
    if p["erase"] > 0:                                    # random erasing: xóa 1 ô chữ nhật
        h = x.shape[-1]
        for i in torch.nonzero(torch.rand(n, device=dev) < p["erase"]).flatten().tolist():
            eh, ew = np.random.randint(h // 8, h // 3, size=2)
            y0, x0 = np.random.randint(0, h - eh), np.random.randint(0, h - ew)
            out[i, :, y0:y0 + eh, x0:x0 + ew] = 0.0
    return out


def make_loaders(data, batch_size, device, limit=None, seed=42):
    """DataLoader trên tensor đã nằm sẵn trong bộ nhớ thiết bị (GPU): đọc dữ liệu không còn là nút thắt."""
    mean, std = train_stats(data["train"][0])
    loaders = {}
    for s, (x, y) in data.items():
        if limit:
            x, y = x[:limit if s == "train" else limit // 4], y[:limit if s == "train" else limit // 4]
        ds = TensorDataset(to_tensor(x, mean, std).to(device), torch.from_numpy(y).to(device))
        g = torch.Generator().manual_seed(seed)
        loaders[s] = DataLoader(ds, batch_size=batch_size, shuffle=(s == "train"), generator=g if s == "train" else None)
    return loaders, (mean, std)
