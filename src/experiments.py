"""Danh sách thực nghiệm. Mỗi thực nghiệm chỉ đổi MỘT yếu tố so với baseline (A2).

Nhóm A – Kiến trúc CNN (theo 4 mô hình của bài mẫu)
Nhóm B – Kỹ thuật huấn luyện (tăng cường dữ liệu, thuật toán tối ưu, label smoothing)
Nhóm C – Hàm kích hoạt và điều chuẩn (BatchNorm, Dropout)
Nhóm D – Học chuyển giao (transfer learning) từ ImageNet
"""
EXPERIMENTS = {
    # key: (nhóm, mô tả, thay đổi so với baseline)
    "A1": ("A", "SMALL CNN: 2 khối (2×64 | 2×128+2×256), FC1024", dict(model="small")),
    "A2": ("A", "MEDIUM CNN (baseline): 2×64, 3×128, 3×256, FC1024", dict()),
    "A3": ("A", "MEDIUM_01 CNN: 3×64, 4×128, 4×256, FC1024", dict(model="medium01")),
    "A4": ("A", "LARGE CNN: 4×64, 4×128, 4×256, 4×512, FC2048", dict(model="large")),
    "B1": ("B", "Không tăng cường dữ liệu", dict(augment="none")),
    "B2": ("B", "Tăng cường mạnh (xoay 20°, dịch 15%, zoom 15%, xóa ngẫu nhiên)", dict(augment="strong")),
    "B3": ("B", "SGD momentum 0.9, lr 0.01 thay cho Adam", dict(optimizer="sgd", lr=0.01, weight_decay=5e-4)),
    "B4": ("B", "Label smoothing 0.1", dict(label_smoothing=0.1)),
    "C1": ("C", "Hàm kích hoạt Sigmoid thay ReLU", dict(activation="sigmoid")),
    "C2": ("C", "Hàm kích hoạt ELU thay ReLU", dict(activation="elu")),
    "C3": ("C", "Hàm kích hoạt LeakyReLU(0.1) thay ReLU", dict(activation="leakyrelu")),
    "C4": ("C", "Bỏ BatchNorm", dict(batchnorm=False)),
    "C5": ("C", "Bỏ Dropout (conv và FC)", dict(dropout_conv=0.0, dropout_fc=0.0)),
    "D1": ("D", "ResNet18 tiền huấn luyện ImageNet, fine-tune, ảnh 96×96", dict(model="resnet18", pretrained=True, image_size=96, lr=3e-4)),
    "D2": ("D", "VGG16-BN tiền huấn luyện ImageNet, fine-tune, ảnh 96×96", dict(model="vgg16bn", pretrained=True, image_size=96, lr=1e-4, batch_size=64)),
}
GROUP_TITLES = {
    "A": "Kiến trúc CNN",
    "B": "Kỹ thuật huấn luyện",
    "C": "Hàm kích hoạt và điều chuẩn",
    "D": "Học chuyển giao",
}


def keys_of_group(g):
    return [k for k, v in EXPERIMENTS.items() if v[0] == g]
