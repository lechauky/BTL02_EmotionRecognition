# A4_fer-std_large-relu-bn_adam-0.001_261125-1031

- **Thực nghiệm:** A4 – LARGE CNN: 4×64, 4×128, 4×256, 4×512, FC2048 (nhóm A: Kiến trúc CNN)
- **Phiên bản:** v1 · **Người chạy:** Trần Thanh Huyền · **Thời gian:** 2026-11-25T10:31:21+07:00 → 2026-11-25T10:54:00+07:00
- **Máy:** Google Colab, Linux 6.6.159+, Tesla T4, Python 3.13.16, PyTorch 2.14.1+cu130, commit `29ce7d3`
- **Lệnh:** `run_experiment.py --group A --author Trần Thanh Huyền --note `

## Kết quả

| Chỉ số | Valid (PublicTest) | Test (PrivateTest) |
|---|---|---|
| Accuracy | 0.6656 | 0.6757 |
| Loss | 0.9460 | 0.9089 |
| Macro-F1 | 0.6337 | 0.6474 |

Epoch tốt nhất (val_loss nhỏ nhất): **52** / 60 epoch · 20,412,487 tham số · 22.5 phút

## Cấu hình

```json
{
  "model": "large",
  "activation": "relu",
  "batchnorm": true,
  "dropout_conv": 0.2,
  "dropout_fc": 0.5,
  "pretrained": false,
  "image_size": 48,
  "augment": "standard",
  "optimizer": "adam",
  "lr": 0.001,
  "weight_decay": 0.0,
  "momentum": 0.9,
  "label_smoothing": 0.0,
  "batch_size": 128,
  "epochs": 60,
  "early_stopping": 10,
  "lr_patience": 4,
  "lr_factor": 0.5,
  "min_lr": 1e-06,
  "seed": 42
}
```

## Hình

![confusion_test.png](figures/confusion_test.png)
![confusion_valid.png](figures/confusion_valid.png)
![feature_maps_last_conv.png](figures/feature_maps_last_conv.png)
![filters_first_conv.png](figures/filters_first_conv.png)
![filters_last_conv.png](figures/filters_last_conv.png)
![training_curves.png](figures/training_curves.png)
![true_cases.png](figures/true_cases.png)
![wrong_cases.png](figures/wrong_cases.png)

Trọng số: `checkpoints/best.pt` – bản lưu trên Google Drive: https://drive.google.com/drive/folders/16lyivk-DlgbP9q31Oxg2acJtdwTRiyyV
