"""Bước 3 – Tổng hợp và chọn mô hình cuối.

    python run_final.py [--author "..."]
1. Quét toàn bộ exps/ (bỏ các lần --quick), lấy phiên bản mới nhất của mỗi mã thực nghiệm.
2. Vẽ biểu đồ so sánh từng nhóm A, B, C, D -> exps/_summary/.
3. Chọn mô hình có ACCURACY TRÊN VALID (PublicTest) cao nhất – không nhìn test khi chọn.
4. Đánh giá mô hình đó trên PrivateTest (có và không có TTA lật ngang), vẽ ma trận nhầm lẫn, ca đúng/sai,
   bộ lọc tầng conv đầu/cuối, bản đồ đặc trưng cho mỗi lớp -> exps/FINAL/<run_id>/, ghi final_result.json.
"""
import argparse
import datetime as dt
import json
import os

import numpy as np
import pandas as pd
import torch

from src import config as C
from src import data as D
from src import evaluate as E
from src import tracking as T
from src import visualize as V
from src.experiments import EXPERIMENTS, GROUP_TITLES
from src.models import build_model
from src.train import evaluate_loader, get_device


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--author", default=C.GROUP_OWNER.get("D", ""))
    args = ap.parse_args()
    df = T.scan()
    df = df[~df["quick"].astype(bool)]
    L = df.sort_values("start").groupby("key").tail(1).copy()
    L["label"] = L["key"]
    out = os.path.join(C.EXPS_DIR, "_summary")
    os.makedirs(out, exist_ok=True)
    for g in "ABCD":
        d = L[L["group"] == g].sort_values("key")
        if len(d):
            V.plot_compare(d, ["valid_acc", "test_acc"], ["valid (PublicTest)", "test (PrivateTest)"],
                           os.path.join(out, f"compare_{g}.png"), f"Nhóm {g} – {GROUP_TITLES[g]}")
    V.plot_compare(L.sort_values("key"), ["valid_acc", "test_acc"], ["valid", "test"], os.path.join(out, "compare_all.png"),
                   "Tất cả thực nghiệm (phiên bản mới nhất)")
    L.sort_values("valid_acc", ascending=False)[["key", "run_id", "author", "version", "valid_acc", "valid_loss", "test_acc",
                                                 "test_f1", "n_params", "best_epoch", "train_time_s"]].to_csv(
        os.path.join(out, "ranking_by_valid.csv"), index=False)

    best = L.sort_values(["valid_acc", "valid_loss"], ascending=[False, True]).iloc[0]
    print(f"Mô hình chọn theo valid acc: {best['key']} ({best['run_id']}) valid {best['valid_acc']:.4f}")
    run_dir = os.path.join(C.EXPS_DIR, best["group"], best["run_id"])
    ck = os.path.join(run_dir, "checkpoints", "best.pt")
    if not os.path.exists(ck) and C.WEIGHTS_DIR:
        ck = os.path.join(C.WEIGHTS_DIR, best["group"], best["run_id"], "best.pt")
    device = get_device()
    state = torch.load(ck, map_location=device)
    cfg = state["cfg"]
    model = build_model(cfg).to(device)
    model.load_state_dict(state["model"])
    data = D.prepare()
    loaders, (mean, std) = D.make_loaders(data, 256, device)

    fdir = os.path.join(C.EXPS_DIR, "FINAL", best["run_id"])
    os.makedirs(fdir, exist_ok=True)
    res = {}
    for tta in (False, True):
        for s in ("valid", "test"):
            loss, acc, y, p = evaluate_loader(model, loaders[s], tta=tta)
            m = E.metrics(y, p)
            res[(s, tta)] = dict(loss=loss, acc=m["acc"], f1=m["f1"], m=m, y=y, p=p)
    y, p = res[("test", False)]["y"], res[("test", False)]["p"]
    xt = data["test"][0]
    V.plot_confusion(res[("test", False)]["m"]["cm"], os.path.join(fdir, "confusion_test.png"),
                     f"Mô hình cuối {best['key']} – PrivateTest (acc {res[('test', False)]['acc']:.4f})")
    V.plot_cases(xt, y, p, os.path.join(fdir, "wrong_cases.png"), correct=False, n=32, title="Ca dự đoán SAI – PrivateTest")
    V.plot_cases(xt, y, p, os.path.join(fdir, "true_cases.png"), correct=True, n=32, title="Ca dự đoán ĐÚNG – PrivateTest")
    V.plot_filters(model, os.path.join(fdir, "filters_first_conv.png"), os.path.join(fdir, "filters_last_conv.png"))
    if cfg["model"] not in ("resnet18", "vgg16bn"):
        for c in range(7):
            i = int(np.where((y == c) & (p.argmax(1) == c))[0][0]) if ((y == c) & (p.argmax(1) == c)).any() else int(np.where(y == c)[0][0])
            V.plot_feature_maps(model, xt[i], mean, std, os.path.join(fdir, f"feature_maps_{C.CLASSES[c]}.png"),
                                f"Bản đồ đặc trưng tầng conv cuối – ảnh lớp {C.CLASSES[c]}")
    open(os.path.join(fdir, "classification_report_test.txt"), "w").write(res[("test", False)]["m"]["report_txt"])
    pc = E.per_class_table(res[("test", False)]["m"]["report"])
    pd.DataFrame(pc).T.to_csv(os.path.join(fdir, "per_class_test.csv"))
    final = {
        "selected_key": best["key"], "run_id": best["run_id"], "group": best["group"], "rule": "max valid_acc (PublicTest)",
        "description": EXPERIMENTS[best["key"]][1], "author_of_run": best["author"], "evaluated_by": args.author,
        "evaluated_at": C.now().isoformat(timespec="seconds"),
        **{f"{s}_{k}{'_tta' if tta else ''}": float(v[k]) for (s, tta), v in res.items() for k in ("acc", "loss", "f1")},
        "per_class_test": pc, "confusion_test": res[("test", False)]["m"]["cm"].tolist(),
    }
    json.dump(final, open(os.path.join(fdir, "final_result.json"), "w"), indent=2, ensure_ascii=False)
    print(f"PrivateTest: acc {final['test_acc']:.4f} (TTA {final['test_acc_tta']:.4f}), macro-F1 {final['test_f1']:.4f}")
    print("Đã lưu vào", fdir)
    try:
        from make_log import build
        build()
    except Exception as e:
        print("(chưa dựng được Excel:", e, ")")


if __name__ == "__main__":
    main()
