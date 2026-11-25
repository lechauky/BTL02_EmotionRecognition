"""Biểu đồ cho slide (ảnh PNG để Google Slides hiển thị đúng nhãn)."""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
D = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
R, F = D["latest"], D["final"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
ks = sorted(R, key=lambda k: -R[k]["metrics"]["valid_acc"])
va = [100 * R[k]["metrics"]["valid_acc"] for k in ks]; te = [100 * R[k]["metrics"]["test_acc"] for k in ks]
fig, ax = plt.subplots(figsize=(8.2, 5.2), dpi=200)
x = range(len(ks)); w = 0.4
ax.bar([i - w / 2 for i in x], va, w, color="#247BA0", label="Valid acc (PublicTest)")
ax.bar([i + w / 2 for i in x], te, w, color="#E4572E", label="Test acc (PrivateTest)")
ax.axhline(100 * R["A2"]["metrics"]["valid_acc"], color="#324A5F", lw=1, ls="--")
ax.text(len(ks) - 0.5, 100 * R["A2"]["metrics"]["valid_acc"] + 0.15, "baseline A2 (valid)", ha="right", va="bottom", fontsize=9, color="#324A5F")
ax.set_xticks(list(x)); ax.set_xticklabels(ks, fontsize=11)
ax.set_ylim(60, 71.5); ax.set_ylabel("Accuracy (%)"); ax.grid(axis="y", color="#DDE3E9", lw=0.6); ax.set_axisbelow(True)
ax.legend(loc="upper right", frameon=False, ncol=2, bbox_to_anchor=(1, 1.08))
fig.tight_layout(); fig.savefig(f"{out}/chart_all.png"); plt.close(fig)
cls = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
f1 = [F["per_class_test"][c]["f1-score"] for c in cls]
fig, ax = plt.subplots(figsize=(5.2, 5.0), dpi=200)
ax.barh(cls[::-1], f1[::-1], color=["#E4572E" if v == min(f1) else ("#76B041" if v == max(f1) else "#247BA0") for v in f1[::-1]])
for i, v in enumerate(f1[::-1]):
    ax.text(v + 0.01, i, f"{v:.2f}".replace(".", ","), va="center", fontsize=11, color="#1B2A41")
ax.set_xlim(0, 1.05); ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
ax.set_title("F1 từng lớp – PrivateTest", fontsize=12, color="#1B2A41")
fig.tight_layout(); fig.savefig(f"{out}/chart_f1.png"); plt.close(fig)
print("ok")
