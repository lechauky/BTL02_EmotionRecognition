# B1_fer-noaug_medium-relu-bn_adam-0.001_261123-1557

- **Thực nghiệm:** B1 – Không tăng cường dữ liệu (nhóm B: Kỹ thuật huấn luyện)
- **Phiên bản:** v4 · **Người chạy:** Lê Châu Kỳ · **Thời gian:** 2026-11-23T15:57:25 → 2026-11-23T16:01:02
- **Máy:** Google Colab, Linux 6.6.159+, Tesla T4, Python 3.13.16, PyTorch 2.14.1+cu130, commit `64e5908`
- **Lệnh:** `run_experiment.py --group B --author Lê Châu Kỳ --note `

## Kết quả

| Chỉ số | Valid (PublicTest) | Test (PrivateTest) |
|---|---|---|
| Accuracy | 0.6317 | 0.6389 |
| Loss | 1.0397 | 1.0052 |
| Macro-F1 | 0.6141 | 0.6261 |

Epoch tốt nhất (val_loss nhỏ nhất): **9** / 19 epoch · 11,329,607 tham số · 3.4 phút

## Cấu hình

```json
{
  "model": "medium",
  "activation": "relu",
  "batchnorm": true,
  "dropout_conv": 0.2,
  "dropout_fc": 0.5,
  "pretrained": false,
  "image_size": 48,
  "augment": "none",
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
