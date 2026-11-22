"""Chỉ số đánh giá phân loại: accuracy, macro-F1, precision/recall/F1 từng lớp, ma trận nhầm lẫn."""
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from . import config as C


def metrics(y, p):
    pred = p.argmax(1)
    return {"acc": float((pred == y).mean()), "f1": float(f1_score(y, pred, average="macro")),
            "cm": confusion_matrix(y, pred, labels=range(7)),
            "report": classification_report(y, pred, labels=range(7), target_names=C.CLASSES, digits=4,
                                            output_dict=True, zero_division=0),
            "report_txt": classification_report(y, pred, labels=range(7), target_names=C.CLASSES, digits=4,
                                                zero_division=0)}


def per_class_table(rep):
    return {c: {k: round(rep[c][k], 4) for k in ("precision", "recall", "f1-score", "support")} for c in C.CLASSES}
