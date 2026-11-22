# BTL02 – Nhận dạng cảm xúc khuôn mặt (FER2013) bằng CNN – PyTorch

**Nhóm 06 · Lớp DCT123C4 · GV Đỗ Như Tài · Trường Đại học Sài Gòn – Khoa CNTT**

| Thành viên | MSSV | Code phụ trách | Nhóm thực nghiệm | Đóng góp |
|---|---|---|---|---|
| Lê Châu Kỳ (TV1) | 3123411173 | `src/data.py`, `run_data.py`, `src/tracking.py`, `make_log.py` | B – kỹ thuật huấn luyện | 25% |
| Trần Thanh Huyền (TV2) | 3123411126 | `src/models.py` | A – kiến trúc CNN | 25% |
| Vũ Hoàng Phương (TV3) | 3123411238 | `src/train.py` | C – kích hoạt, điều chuẩn | 25% |
| Đỗ Minh Thương (TV4) | 3123411294 | `src/evaluate.py`, `src/visualize.py`, `run_final.py` | D – học chuyển giao, mô hình cuối | 25% |

Phân công chi tiết theo ma trận RACI (trục dọc: đầu việc, trục ngang: thành viên) ở sheet **PhanCong** của nhật ký thực nghiệm.

## Bài toán
Phân loại ảnh khuôn mặt xám 48×48 thành 7 cảm xúc: 0 Angry, 1 Disgust, 2 Fear, 3 Happy, 4 Sad, 5 Surprise, 6 Neutral.
Dữ liệu Kaggle FER2013 (`fer2013.csv`, bản sao: https://www.kaggle.com/datasets/deadskull7/fer2013):
Training 28.709 ảnh (huấn luyện) · PublicTest 3.589 (valid – chọn mô hình, dừng sớm) · PrivateTest 3.589 (test – chỉ báo cáo).

## Cấu trúc
```
BTL02_EmotionRecognition/
├── src/
│   ├── config.py        # đường dẫn, thành viên, baseline
│   ├── experiments.py   # danh sách 15 thực nghiệm A1–D2 (mỗi cái đổi 1 yếu tố so với baseline A2)
│   ├── data.py          # đọc csv -> npz, tăng cường dữ liệu trên GPU, DataLoader
│   ├── models.py        # CNN small/medium/medium01/large, ResNet18/VGG16-BN chuyển giao
│   ├── train.py         # vòng lặp huấn luyện, checkpoint, early stopping, ReduceLROnPlateau, AMP
│   ├── evaluate.py      # accuracy, macro-F1, báo cáo từng lớp, ma trận nhầm lẫn
│   ├── visualize.py     # đường học, ma trận nhầm lẫn, ca đúng/sai, bộ lọc, bản đồ đặc trưng
│   └── tracking.py      # đặt tên, thư mục thực nghiệm, metadata, registry, W&B
├── run_data.py          # bước 1: chuẩn bị + khảo sát dữ liệu
├── run_experiment.py    # bước 2: chạy thực nghiệm (--exp A2 | --group B)
├── run_final.py         # bước 3: so sánh, chọn mô hình theo valid, đánh giá PrivateTest, bộ lọc
├── make_log.py          # dựng nhật ký BTL02_NhatKyThucNghiem.xlsx (-> Google Sheets)
├── notebooks/BTL02_Colab.ipynb   # chạy trên Google Colab GPU
├── exps/                # mỗi lần chạy một thư mục (xem dưới); registry.csv
└── report/              # báo cáo .docx/.pdf, slide, citations.json (đối chiếu số liệu)
```

## Chạy
```bash
pip install -r requirements.txt
# đặt fer2013.csv (hoặc .zip/.tar.gz) vào data/
python run_data.py
python run_experiment.py --list
python run_experiment.py --exp A2 --quick          # chạy thử 2 epoch
python run_experiment.py --group A --author "Trần Thanh Huyền"
python run_final.py
python make_log.py
```
Trên Colab: mở `notebooks/BTL02_Colab.ipynb`, chọn GPU T4, sửa ô cấu hình (tên, nhóm) rồi chạy lần lượt.

## Thực nghiệm (baseline = A2)
Baseline: CNN MEDIUM (2×64, 3×128, 3×256 conv 3×3 + BatchNorm + ReLU, MaxPool, Dropout 0.2; FC1024 + Dropout 0.5),
tăng cường chuẩn (lật ngang, xoay ±10°, dịch 10%, zoom 10% – như bài mẫu), Adam lr 1e-3, batch 128, tối đa 60 epoch,
dừng sớm sau 10 epoch val_loss không giảm, ReduceLROnPlateau ×0.5 (patience 4), lưu checkpoint khi val_loss giảm.

| Nhóm | Mã | Thay đổi so với baseline |
|---|---|---|
| A – kiến trúc | A1 / A2 / A3 / A4 | SMALL / MEDIUM / MEDIUM_01 / LARGE (4 mô hình của bài mẫu) |
| B – huấn luyện | B1 / B2 / B3 / B4 | không tăng cường / tăng cường mạnh / SGD momentum / label smoothing 0.1 |
| C – kích hoạt, điều chuẩn | C1 / C2 / C3 / C4 / C5 | Sigmoid / ELU / LeakyReLU / bỏ BatchNorm / bỏ Dropout |
| D – chuyển giao | D1 / D2 | ResNet18 / VGG16-BN tiền huấn luyện ImageNet, ảnh 96×96 |

## Quản lý thực nghiệm
Quy tắc đặt tên: `exps/<nhóm>/<mã>_<dữ liệu>_<mô hình>_<tối ưu>_<yymmdd-HHMM>/`, ví dụ
`exps/A/A2_fer-std_medium-relu-bn_adam-0.001_261123-1430/`. Mỗi thư mục có `config.json`, `meta.json`
(người chạy, thời gian, GPU, phiên bản v1/v2…, commit git, lệnh), `history.csv` (log từng epoch), `metrics.json`,
`model_summary.txt`, `figures/` (đường học, ma trận nhầm lẫn, bộ lọc, bản đồ đặc trưng, ca đúng/sai), `README.md`
và `checkpoints/best.pt` (trọng số – giữ trên Google Drive, không đưa lên GitHub).

Liên kết hai chiều: **báo cáo (.docx) → Google Sheets nhật ký / Google Slides → thư mục thực nghiệm trên GitHub**.
Mọi con số trong báo cáo/slide ghi kèm `run_id`; sheet **KiemTra** đối chiếu tự động với nhật ký (cột Khớp ✔/✘).
