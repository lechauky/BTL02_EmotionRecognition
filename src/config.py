"""Cấu hình chung: đường dẫn, nhóm, thành viên, siêu tham số mặc định (baseline).

Đường dẫn có thể đổi bằng biến môi trường (tiện khi chạy trên Colab với Google Drive):
    FER_DATA_DIR   thư mục chứa fer2013.csv hoặc fer2013.tar.gz   (mặc định: <project>/data)
    FER_EXPS_DIR   thư mục lưu thực nghiệm                         (mặc định: <project>/exps)
    FER_WEIGHTS_DIR thư mục lưu trọng số .pt (Drive)               (mặc định: <exps>/<...>/checkpoints)
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("FER_DATA_DIR", os.path.join(ROOT, "data"))
EXPS_DIR = os.environ.get("FER_EXPS_DIR", os.path.join(ROOT, "exps"))
WEIGHTS_DIR = os.environ.get("FER_WEIGHTS_DIR") or None
FIG_DIR = os.path.join(EXPS_DIR, "_data")          # hình khảo sát dữ liệu
REGISTRY_CSV = os.path.join(EXPS_DIR, "registry.csv")
EXCEL_LOG = os.path.join(ROOT, "BTL02_NhatKyThucNghiem.xlsx")

# Liên kết công khai (điền sau khi tạo) – dùng để Sheets/Slides/báo cáo trỏ tới từng thực nghiệm
GITHUB_REPO = os.environ.get("FER_GITHUB_REPO", "https://github.com/lechauky/BTL02_EmotionRecognition")
GITHUB_BRANCH = os.environ.get("FER_GITHUB_BRANCH", "main")
DRIVE_WEIGHTS_URL = os.environ.get("FER_DRIVE_WEIGHTS_URL", "https://drive.google.com/drive/folders/16lyivk-DlgbP9q31Oxg2acJtdwTRiyyV")  # thư mục exps trên Drive (có checkpoints/best.pt)
SHEETS_URL = os.environ.get("FER_SHEETS_URL", "https://docs.google.com/spreadsheets/d/17R3AmpbdE-dxEJrX0fMZhDw2iZWPCG3-ITbCVEo-V0E/edit")
SLIDES_URL = os.environ.get("FER_SLIDES_URL", "")

# FER2013: nhãn gốc trong file csv
CLASSES = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
CLASSES_VI = ["Giận dữ", "Ghê tởm", "Sợ hãi", "Vui", "Buồn", "Ngạc nhiên", "Bình thường"]
SPLITS = {"train": "Training", "valid": "PublicTest", "test": "PrivateTest"}

# Giờ Việt Nam: máy Colab chạy theo giờ UTC, nên mọi mốc thời gian đều ghi kèm múi giờ +07:00
import datetime as _dt
VN_TZ = _dt.timezone(_dt.timedelta(hours=7), "ICT")


def now():
    return _dt.datetime.now(VN_TZ)


GROUP_NAME = "Nhóm 06"
CLASS_NAME = "DCT123C4"
LECTURER = "Đỗ Như Tài"
# (mã, họ tên, MSSV, phần code, nhóm thực nghiệm)
MEMBERS = [
    ("TV1", "Lê Châu Kỳ", "3123411173", "data.py, run_data.py, tracking/nhật ký", "B"),
    ("TV2", "Trần Thanh Huyền", "3123411126", "models.py", "A"),
    ("TV3", "Vũ Hoàng Phương", "3123411238", "train.py", "C"),
    ("TV4", "Đỗ Minh Thương", "3123411294", "evaluate.py, visualize.py, run_final.py", "D"),
]
GROUP_OWNER = {g: name for _, name, _, _, g in MEMBERS}

# Baseline (= mô hình MEDIUM trong bài mẫu, viết lại bằng PyTorch + BatchNorm)
BASELINE = dict(
    model="medium",          # small | medium | medium01 | large | resnet18 | vgg16bn
    activation="relu",       # relu | leakyrelu | elu | sigmoid
    batchnorm=True,
    dropout_conv=0.2,
    dropout_fc=0.5,
    pretrained=False,
    image_size=48,
    augment="standard",      # none | standard | strong
    optimizer="adam",        # adam | adamw | sgd
    lr=1e-3,
    weight_decay=0.0,
    momentum=0.9,
    label_smoothing=0.0,
    batch_size=128,
    epochs=60,
    early_stopping=10,       # dừng nếu val_loss không giảm sau 10 epoch
    lr_patience=4,           # ReduceLROnPlateau: giảm lr ×0.5 nếu val_loss đứng yên 4 epoch
    lr_factor=0.5,
    min_lr=1e-6,
    seed=42,
)
