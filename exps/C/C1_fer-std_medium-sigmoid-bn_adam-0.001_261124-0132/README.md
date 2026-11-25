# C1_fer-std_medium-sigmoid-bn_adam-0.001_261124-0132

- **Thực nghiệm:** C1 – Hàm kích hoạt Sigmoid thay ReLU (nhóm C: Hàm kích hoạt và điều chuẩn)
- **Phiên bản:** v1 · **Người chạy:** Vũ Hoàng Phương · **Thời gian:** 2026-11-24T01:32:26+07:00 → 2026-11-24T01:32:48+07:00
- **Máy:** Google Colab, Linux 6.6.159+, Tesla T4, Python 3.13.16, PyTorch 2.14.1+cu130, commit `29ce7d3`
- **Lệnh:** `run_experiment.py --exp C1 --quick --author Vũ Hoàng Phương`

## Kết quả

| Chỉ số | Valid (PublicTest) | Test (PrivateTest) |
|---|---|---|
| Accuracy | 0.2540 | 0.2400 |
| Loss | 1.8903 | 1.8405 |
| Macro-F1 | 0.0922 | 0.0834 |

Epoch tốt nhất (val_loss nhỏ nhất): **2** / 2 epoch · 11,329,607 tham số · 0.0 phút

## Cấu hình

```json
{
  "model": "medium",
  "activation": "sigmoid",
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
  "epochs": 2,
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
