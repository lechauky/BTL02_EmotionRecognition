"""Mô hình: các CNN tự thiết kế (theo 4 mô hình trong bài mẫu, viết lại bằng PyTorch) và mô hình học chuyển giao.

Mỗi khối: [Conv3×3 (padding=same) -> BatchNorm -> Kích hoạt] × n  ->  MaxPool 2×2  ->  Dropout
Bộ phân loại: Flatten -> Linear(fc) [-> BatchNorm1d] -> Kích hoạt -> Dropout -> Linear(7)   (softmax nằm trong CrossEntropyLoss)
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

# (danh sách khối: mỗi khối là list số kênh của các tầng conv), số nơ-ron FC
SPECS = {
    "small": ([[64, 64], [128, 128, 256, 256]], 1024),
    "medium": ([[64, 64], [128, 128, 128], [256, 256, 256]], 1024),
    "medium01": ([[64, 64, 64], [128, 128, 128, 128], [256, 256, 256, 256]], 1024),
    "large": ([[64] * 4, [128] * 4, [256] * 4, [512] * 4], 2048),
}


def make_act(name):
    return {"relu": nn.ReLU(inplace=True), "leakyrelu": nn.LeakyReLU(0.1, inplace=True),
            "elu": nn.ELU(inplace=True), "sigmoid": nn.Sigmoid()}[name]


class FERCNN(nn.Module):
    def __init__(self, model="medium", activation="relu", batchnorm=True, dropout_conv=0.2, dropout_fc=0.5,
                 in_ch=1, n_classes=7, image_size=48, **_):
        super().__init__()
        blocks, fc = SPECS[model]
        layers, c = [], in_ch
        for bi, chans in enumerate(blocks, 1):
            for li, o in enumerate(chans, 1):
                layers.append(nn.Conv2d(c, o, 3, padding=1, bias=not batchnorm))
                if batchnorm:
                    layers.append(nn.BatchNorm2d(o))
                layers.append(make_act(activation))
                c = o
            layers += [nn.MaxPool2d(2), nn.Dropout(dropout_conv)]
        self.features = nn.Sequential(*layers)
        s = image_size // 2 ** len(blocks)
        head = [nn.Flatten(), nn.Linear(c * s * s, fc, bias=not batchnorm)]
        if batchnorm:
            head.append(nn.BatchNorm1d(fc))
        self.classifier = nn.Sequential(*head, make_act(activation), nn.Dropout(dropout_fc), nn.Linear(fc, n_classes))

    def forward(self, x):
        return self.classifier(self.features(x))


class TransferNet(nn.Module):
    """ResNet18 / VGG16-BN tiền huấn luyện ImageNet. Ảnh xám 48×48 được phóng lên image_size và lặp thành 3 kênh."""

    def __init__(self, model="resnet18", pretrained=True, n_classes=7, image_size=96, **_):
        super().__init__()
        import torchvision.models as tvm
        self.image_size = image_size
        if model == "resnet18":
            net = tvm.resnet18(weights=tvm.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None)
            net.fc = nn.Linear(net.fc.in_features, n_classes)
        else:
            net = tvm.vgg16_bn(weights=tvm.VGG16_BN_Weights.IMAGENET1K_V1 if pretrained else None)
            net.avgpool = nn.AdaptiveAvgPool2d(1)
            net.classifier = nn.Sequential(nn.Linear(512, 512), nn.ReLU(True), nn.Dropout(0.5), nn.Linear(512, n_classes))
        self.net = net
        # chuẩn hóa ImageNet áp lên ảnh đã chuẩn hóa theo FER (xấp xỉ, đủ cho fine-tune)
        self.register_buffer("m", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer("s", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

    def forward(self, x):
        if x.shape[-1] != self.image_size:
            x = F.interpolate(x, size=self.image_size, mode="bilinear", align_corners=False)
        x = x.repeat(1, 3, 1, 1) * 0.255 + 0.507          # về lại [0,1] (mean/std của FER train)
        return self.net((x - self.m) / self.s)


def build_model(cfg):
    if cfg["model"] in SPECS:
        return FERCNN(**cfg)
    return TransferNet(**cfg)


def count_params(m):
    return sum(p.numel() for p in m.parameters())


def last_conv(m):
    convs = [x for x in m.modules() if isinstance(x, nn.Conv2d)]
    return convs[0], convs[-1]


def summary(model, image_size=48):
    """Tóm tắt từng tầng: tên, loại, kích thước đầu ra, số tham số (giống model.summary() của Keras)."""
    rows, hooks = [], []

    def hook(name):
        def f(mod, inp, out):
            n = sum(p.numel() for p in mod.parameters(recurse=False))
            rows.append((name, mod.__class__.__name__, tuple(out.shape[1:]), n))
        return f

    for name, mod in model.named_modules():
        if len(list(mod.children())) == 0:
            hooks.append(mod.register_forward_hook(hook(name)))
    model.eval()
    with torch.no_grad():
        model(torch.zeros(1, 1, 48, 48, device=next(model.parameters()).device))
    for h in hooks:
        h.remove()
    lines = [f"{'Tầng':32s} {'Loại':14s} {'Đầu ra':20s} {'Tham số':>10s}", "-" * 80]
    lines += [f"{n:32s} {t:14s} {str(s):20s} {p:>10,d}" for n, t, s, p in rows]
    lines += ["-" * 80, f"Tổng số tham số: {count_params(model):,d}"]
    return "\n".join(lines)
