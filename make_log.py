"""Dựng file nhật ký thực nghiệm BTL02_NhatKyThucNghiem.xlsx từ thư mục exps/ (để đưa lên Google Sheets).

    python make_log.py
Nguồn dữ liệu duy nhất là các thư mục exps/<nhóm>/<run_id>/ (meta.json, config.json, metrics.json):
file Excel/Sheets luôn dựng lại được và luôn khớp với thực nghiệm. Mỗi dòng có liên kết tới đúng thư mục
thực nghiệm trên GitHub (log, cấu hình, hình) và trọng số trên Google Drive.
Sheet KiemTra đối chiếu các con số được trích dẫn trong báo cáo/slide (report/citations.json) với nhật ký.
"""
import datetime as dt
import json
import os

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from src import config as C
from src import tracking as T
from src.experiments import EXPERIMENTS, GROUP_TITLES

F = "Arial"
FB, FBOLD = Font(name=F, size=10), Font(name=F, size=10, bold=True)
FHEAD = Font(name=F, size=10, bold=True, color="FFFFFF")
FTITLE = Font(name=F, size=14, bold=True, color="1F3864")
FSUB = Font(name=F, size=11, bold=True, color="2E74B5")
FLINK = Font(name=F, size=10, color="0563C1", underline="single")
HEAD = PatternFill("solid", fgColor="1F4E79")
KEY = PatternFill("solid", fgColor="DDEBF7")
GOOD = PatternFill("solid", fgColor="E2EFDA")
BAD = PatternFill("solid", fgColor="FCE4D6")
SIDE = Side(style="thin", color="BFBFBF")
BOX = Border(left=SIDE, right=SIDE, top=SIDE, bottom=SIDE)
WRAP = Alignment(wrap_text=True, vertical="top")
TOP = Alignment(vertical="top")
PCT = "0.00%"

CITATIONS = os.path.join(C.ROOT, "report", "citations.json")


def header(ws, row, cols, widths=None):
    for j, name in enumerate(cols, 1):
        c = ws.cell(row=row, column=j, value=name)
        c.font, c.fill, c.border = FHEAD, HEAD, BOX
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        if widths:
            ws.column_dimensions[get_column_letter(j)].width = widths[j - 1]
    ws.row_dimensions[row].height = 32


def put(ws, r, c, v, fmt=None, bold=False, wrap=False, link=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font, cell.border = (FBOLD if bold else FB), BOX
    cell.alignment = WRAP if wrap else TOP
    if fmt:
        cell.number_format = fmt
    if link:
        cell.value = f'=HYPERLINK("{link}","{v}")'
        cell.font = FLINK
    return cell


def short_time(s):
    try:
        return dt.datetime.fromisoformat(s)
    except Exception:
        return None


def sheet_guide(wb, df):
    ws = wb.active
    ws.title = "HuongDan"
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 110
    ws["A1"] = "NHẬT KÝ THỰC NGHIỆM – BTL02: NHẬN DẠNG CẢM XÚC KHUÔN MẶT (FER2013) BẰNG CNN – PYTORCH"
    ws["A1"].font = FTITLE
    ws["A2"] = (f"{C.GROUP_NAME} · Lớp {C.CLASS_NAME} · GV {C.LECTURER} · dựng lại lúc {dt.datetime.now():%Y-%m-%d %H:%M} "
                f"từ {len(df)} thư mục thực nghiệm trong exps/")
    ws["A2"].font = Font(name=F, size=10, italic=True)
    links = [("Kho code + exps (GitHub)", C.GITHUB_REPO), ("Trọng số (Google Drive)", C.DRIVE_WEIGHTS_URL),
             ("Slide (Google Slides)", C.SLIDES_URL), ("Nhật ký này (Google Sheets)", C.SHEETS_URL)]
    rows = [("Liên kết", "")] + [(a, b or "(điền sau)") for a, b in links] + [("", ""), ("Các sheet", "")] + [
        ("NhatKy", "Mỗi dòng là MỘT lần chạy: ngày giờ, người chạy, thí nghiệm, phiên bản, mô hình, dữ liệu, tối ưu, kết quả, "
                   "thiết bị, commit, liên kết tới thư mục thực nghiệm (GitHub) và trọng số (Drive)."),
        ("TongHop", "Mỗi thí nghiệm một dòng (phiên bản mới nhất), so với baseline A2; theo 4 nhóm A, B, C, D."),
        ("PhanCong", "Task manager: trục dọc = đầu việc, trục ngang = thành viên (ma trận RACI) + trạng thái, sản phẩm."),
        ("KiemTra", "Đối chiếu từng con số trích dẫn trong báo cáo/slide với nhật ký: cột 'Khớp' phải là ✔."),
        ("", ""), ("Quy tắc đặt tên", "exps/<nhóm>/<mã>_<dữ liệu>_<mô hình>_<tối ưu>_<yymmdd-HHMM>/ – mỗi lần chạy một thư mục, "
                                     "không ghi đè; chạy lại cùng mã tạo phiên bản mới (v2, v3…)."),
        ("Phiên bản Sheets", "File → Lịch sử phiên bản (Version history) để xem mọi lần cập nhật; mỗi lần cập nhật = một lần chạy make_log.py."),
        ("Chia tập", "Training (28.709) để học · PublicTest (3.589) = valid để chọn mô hình / dừng sớm · "
                     "PrivateTest (3.589) = test chỉ để báo cáo."),
        ("Không sửa tay", "Sheet được dựng lại từ exps/; muốn sửa thì sửa meta.json của thực nghiệm rồi chạy lại make_log.py."),
    ]
    for i, (a, b) in enumerate(rows, 4):
        ws.cell(row=i, column=1, value=a).font = FSUB if (b == "" and a) else FBOLD
        c = ws.cell(row=i, column=2, value=b)
        c.font, c.alignment = FB, WRAP
        if b.startswith("http"):
            c.value, c.font = f'=HYPERLINK("{b}","{b}")', FLINK


NK_COLS = [("STT", 5), ("Ngày", 11), ("Bắt đầu", 8), ("Kết thúc", 8), ("Người chạy", 17), ("Nhóm", 6), ("Mã TN", 6),
           ("Phiên bản", 8), ("Nội dung thực nghiệm", 38), ("Mô hình", 22), ("Dữ liệu / tăng cường", 12),
           ("Tối ưu / lr", 14), ("Batch", 6), ("Epoch tốt nhất / chạy", 9), ("Số tham số", 11),
           ("Valid acc", 9), ("Valid loss", 9), ("Test acc", 9), ("Test macro-F1", 9), ("Thời gian (phút)", 9),
           ("Thiết bị", 22), ("Commit", 9), ("Thư mục thực nghiệm", 46), ("Trọng số", 14), ("W&B", 10), ("Ghi chú", 24)]


def journal_values(i, r):
    """Một dòng của sheet NhatKy (dùng chung cho file Excel và cho việc ghi thẳng lên Google Sheets từ Colab)."""
    st, en = short_time(r["start"]), short_time(r["end"])
    data, model, opt = T.slug({k[4:]: r[k] for k in r.index if k.startswith("cfg_")})
    link = lambda url, text: f'=HYPERLINK("{url}","{text}")' if url else text  # noqa: E731
    wb_url = r.get("wandb_url") if isinstance(r.get("wandb_url"), str) else ""
    return [i, st.strftime("%Y-%m-%d") if st else "", st.strftime("%H:%M") if st else "", en.strftime("%H:%M") if en else "",
            r["author"], r["group"], r["key"], r["version"], r["description"], model, data.replace("fer-", ""), opt,
            int(r["cfg_batch_size"]), f"{int(r['best_epoch'])} / {int(r['epochs_run'])}", int(r["n_params"]),
            round(float(r["valid_acc"]), 4), round(float(r["valid_loss"]), 4), round(float(r["test_acc"]), 4),
            round(float(r["test_f1"]), 4), round(float(r["train_time_s"]) / 60, 1),
            r["device"], r["git_commit"] if isinstance(r["git_commit"], str) else "", link(r["github"], r["run_id"]),
            link(C.DRIVE_WEIGHTS_URL, "best.pt"), link(wb_url, "mở") if wb_url.startswith("http") else "",
            r.get("note", "") if isinstance(r.get("note", ""), str) else ""]


def sheet_journal(wb, df):
    ws = wb.create_sheet("NhatKy")
    header(ws, 1, [c for c, _ in NK_COLS], [w for _, w in NK_COLS])
    fmts = {15: "#,##0", 16: PCT, 17: "0.0000", 18: PCT, 19: "0.0000", 20: "0.0"}
    for i, r in df.iterrows():
        for k, v in enumerate(journal_values(i + 1, r), 1):
            c = put(ws, i + 2, k, v, fmt=fmts.get(k), wrap=k in (9, 26))
            if isinstance(v, str) and v.startswith("=HYPERLINK"):
                c.font = FLINK
    ws.freeze_panes = "H2"
    if len(df):
        ws.auto_filter.ref = f"A1:{get_column_letter(len(NK_COLS))}{len(df) + 1}"
        ws.conditional_formatting.add(f"P2:P{len(df) + 1}", FormulaRule(formula=[f"P2=MAX($P$2:$P${len(df) + 1})"], fill=GOOD))
    return {r["run_id"]: i + 2 for i, r in df.iterrows()}


def latest(df):
    return df.sort_values("start").groupby("key").tail(1).set_index("key")


SUM_COLS = [("Nhóm", 6), ("Mã", 6), ("Nội dung", 44), ("Người chạy", 17), ("Phiên bản", 8), ("Số tham số", 11),
            ("Epoch tốt nhất", 8), ("Valid acc", 9), ("Δ valid acc so với A2", 10), ("Test acc", 9), ("Test macro-F1", 9),
            ("Train acc (epoch tốt nhất)", 10), ("Train – valid", 10), ("Thời gian (phút)", 9), ("Lần chạy (run_id)", 46)]
SUM_TOP = 3     # dòng tiêu đề bảng


def summary_rows(df):
    """Mỗi mã thực nghiệm một dòng (phiên bản mới nhất), theo thứ tự A1..D2; dùng cho Excel và Google Sheets."""
    L = latest(df)
    keys = [k for k in EXPERIMENTS if k in L.index]
    base = SUM_TOP + 1 + keys.index("A2") if "A2" in keys else None
    rows = []
    for i, k in enumerate(keys):
        r = SUM_TOP + 1 + i
        x = L.loc[k]
        link = f'=HYPERLINK("{x["github"]}","{x["run_id"]}")' if x["github"] else x["run_id"]
        rows.append([x["group"], k, EXPERIMENTS[k][1], x["author"], x["version"], int(x["n_params"]), int(x["best_epoch"]),
                     round(float(x["valid_acc"]), 4), f"=H{r}-H{base}" if base else "", round(float(x["test_acc"]), 4),
                     round(float(x["test_f1"]), 4), round(float(x["train_acc_at_best"]), 4), f"=L{r}-H{r}",
                     round(float(x["train_time_s"]) / 60, 1), link])
    return rows


def sheet_summary(wb, df, rowmap=None):
    ws = wb.create_sheet("TongHop")
    ws["A1"] = "TỔNG HỢP THEO THÍ NGHIỆM (phiên bản mới nhất của mỗi mã; baseline = A2). Nhóm: A kiến trúc · B huấn luyện · C kích hoạt/điều chuẩn · D chuyển giao"
    ws["A1"].font = FSUB
    header(ws, SUM_TOP, [c for c, _ in SUM_COLS], [w for _, w in SUM_COLS])
    fm = {6: "#,##0", 8: PCT, 9: "+0.00%;-0.00%;0.00%", 10: PCT, 11: "0.0000", 12: PCT, 13: "+0.00%;-0.00%", 14: "0.0"}
    rows = summary_rows(df) if len(df) else []
    for i, row in enumerate(rows):
        for j, v in enumerate(row, 1):
            c = put(ws, SUM_TOP + 1 + i, j, v, fmt=fm.get(j), bold=(row[1] == "A2" and j <= 3), wrap=j == 3)
            if isinstance(v, str) and v.startswith("=HYPERLINK"):
                c.font = FLINK
    last = SUM_TOP + 60
    ws.conditional_formatting.add(f"I4:I{last}", CellIsRule(operator="greaterThan", formula=["0"], fill=GOOD))
    ws.conditional_formatting.add(f"I4:I{last}", CellIsRule(operator="lessThan", formula=["0"], fill=BAD))
    ws.freeze_panes = "D4"


RACI_TASKS = [
    # (đầu việc, sản phẩm, {mã TV: vai trò})  R = thực hiện, A = chịu trách nhiệm cuối, C = góp ý, I = được thông báo
    ("Chuẩn bị dữ liệu, tăng cường dữ liệu (data.py, run_data.py)", "src/data.py, exps/_data", {"TV1": "R/A", "TV2": "C", "TV3": "I", "TV4": "I"}),
    ("Kiến trúc mô hình CNN (models.py)", "src/models.py", {"TV1": "C", "TV2": "R/A", "TV3": "C", "TV4": "I"}),
    ("Vòng lặp huấn luyện, callback (train.py)", "src/train.py", {"TV1": "I", "TV2": "C", "TV3": "R/A", "TV4": "C"}),
    ("Đánh giá, trực quan hóa bộ lọc (evaluate.py, visualize.py)", "src/evaluate.py, src/visualize.py", {"TV1": "I", "TV2": "C", "TV3": "C", "TV4": "R/A"}),
    ("Quản lý thực nghiệm, nhật ký Sheets, GitHub", "src/tracking.py, make_log.py, Sheets", {"TV1": "R/A", "TV2": "I", "TV3": "I", "TV4": "C"}),
    ("Thực nghiệm nhóm A – kiến trúc", "exps/A", {"TV1": "I", "TV2": "R/A", "TV3": "C", "TV4": "I"}),
    ("Thực nghiệm nhóm B – kỹ thuật huấn luyện", "exps/B", {"TV1": "R/A", "TV2": "I", "TV3": "C", "TV4": "I"}),
    ("Thực nghiệm nhóm C – kích hoạt, điều chuẩn", "exps/C", {"TV1": "I", "TV2": "C", "TV3": "R/A", "TV4": "I"}),
    ("Thực nghiệm nhóm D – học chuyển giao", "exps/D", {"TV1": "I", "TV2": "C", "TV3": "I", "TV4": "R/A"}),
    ("Chọn mô hình cuối, đánh giá PrivateTest, bộ lọc", "exps/FINAL", {"TV1": "C", "TV2": "C", "TV3": "C", "TV4": "R/A"}),
    ("Báo cáo – mục 1 Dữ liệu + mục 6 Quản lý thực nghiệm", "report/*.docx", {"TV1": "R", "TV2": "I", "TV3": "I", "TV4": "A"}),
    ("Báo cáo – mục 2 Mô hình + 4.1 Nhóm A", "report/*.docx", {"TV1": "I", "TV2": "R", "TV3": "I", "TV4": "A"}),
    ("Báo cáo – mục 3 Huấn luyện + 4.3 Nhóm C", "report/*.docx", {"TV1": "I", "TV2": "I", "TV3": "R", "TV4": "A"}),
    ("Báo cáo – 4.2 Nhóm B", "report/*.docx", {"TV1": "R", "TV2": "I", "TV3": "I", "TV4": "A"}),
    ("Báo cáo – 4.4 Nhóm D, mục 5 Mô hình cuối, kết luận, ghép bản", "report/*.docx", {"TV1": "C", "TV2": "C", "TV3": "C", "TV4": "R/A"}),
    ("Slide (Google Slides) – mỗi người phần của mình", "Google Slides", {"TV1": "R", "TV2": "R", "TV3": "R", "TV4": "R/A"}),
    ("Kiểm tra thống nhất báo cáo – slide – nhật ký – exps", "sheet KiemTra", {"TV1": "R", "TV2": "C", "TV3": "C", "TV4": "A"}),
]


def sheet_raci(wb, df):
    ws = wb.create_sheet("PhanCong")
    ws["A1"] = "PHÂN CÔNG (TASK MANAGER) – trục dọc: đầu việc · trục ngang: thành viên (RACI)"
    ws["A1"].font = FTITLE
    ws["A2"] = "R = trực tiếp làm · A = chịu trách nhiệm cuối/duyệt · C = góp ý · I = được thông báo. Tỷ lệ đóng góp mỗi thành viên 25%."
    ws["A2"].font = Font(name=F, size=10, italic=True)
    names = [f"{code}\n{name}" for code, name, *_ in C.MEMBERS]
    cols = ["STT", "Đầu việc"] + names + ["Sản phẩm / vị trí", "Trạng thái", "Số lần chạy (nhật ký)"]
    header(ws, 4, cols, [5, 52, 15, 15, 15, 15, 30, 12, 12])
    ws.row_dimensions[4].height = 44
    for i, (task, prod, roles) in enumerate(RACI_TASKS, 1):
        r = 4 + i
        put(ws, r, 1, i)
        put(ws, r, 2, task, wrap=True)
        for j, (code, *_rest) in enumerate(C.MEMBERS):
            c = put(ws, r, 3 + j, roles.get(code, ""))
            c.alignment = Alignment(horizontal="center", vertical="top")
            if "R" in roles.get(code, ""):
                c.fill = KEY
        put(ws, r, 7, prod, wrap=True)
        put(ws, r, 8, "Hoàn thành" if (prod.startswith("exps/") and len(df) and (df["folder"].str.startswith(prod)).any()) else "")
        if prod.startswith("exps/") and prod != "exps/_data":
            put(ws, r, 9, f'=COUNTIF(NhatKy!$F$2:$F$1000,"{prod.split("/")[1]}")')
    r = 6 + len(RACI_TASKS)
    ws.cell(row=r, column=1, value="THÀNH VIÊN").font = FSUB
    header(ws, r + 1, ["Mã", "Họ tên", "MSSV", "Phần code", "Nhóm TN", "Số lần chạy", "Tỷ lệ đóng góp"])
    for k, (code, name, mssv, part, g) in enumerate(C.MEMBERS):
        rr = r + 2 + k
        for j, v in enumerate([code, name, mssv, part, g], 1):
            put(ws, rr, j, v, wrap=j == 4)
        put(ws, rr, 6, f'=COUNTIF(NhatKy!$E$2:$E$1000,B{rr})')
        put(ws, rr, 7, 0.25, fmt="0%")
    rr = r + 2 + len(C.MEMBERS)
    put(ws, rr, 2, "Tổng", bold=True)
    put(ws, rr, 6, f"=SUM(F{r + 2}:F{rr - 1})", bold=True)
    put(ws, rr, 7, f"=SUM(G{r + 2}:G{rr - 1})", fmt="0%", bold=True)
    ws.freeze_panes = "C5"


def sheet_check(wb, df, rowmap):
    ws = wb.create_sheet("KiemTra")
    ws["A1"] = "KIỂM TRA THỐNG NHẤT: báo cáo / slide  ↔  nhật ký  ↔  thư mục thực nghiệm"
    ws["A1"].font = FTITLE
    ws["A2"] = ("Mỗi con số trích dẫn trong báo cáo/slide được ghi kèm run_id. Cột 'Giá trị trong nhật ký' lấy bằng công thức "
                "từ sheet NhatKy; cột 'Khớp' = ✔ nếu bằng nhau (làm tròn như khi trích dẫn).")
    ws["A2"].font = Font(name=F, size=10, italic=True)
    cols = ["STT", "Tài liệu", "Vị trí", "Nội dung", "run_id", "Chỉ số", "Giá trị trích dẫn", "Giá trị trong nhật ký",
            "Khớp", "Thư mục thực nghiệm"]
    header(ws, 4, cols, [5, 10, 16, 40, 44, 12, 12, 12, 7, 14])
    cites = json.load(open(CITATIONS, encoding="utf-8")) if os.path.exists(CITATIONS) else []
    col = {"valid_acc": "P", "test_acc": "R", "test_f1": "S", "valid_loss": "Q", "n_params": "O"}
    for i, c in enumerate(cites, 1):
        r = 4 + i
        nr = rowmap.get(c["run_id"])
        put(ws, r, 1, i)
        put(ws, r, 2, c["doc"])
        put(ws, r, 3, c["where"], wrap=True)
        put(ws, r, 4, c["text"], wrap=True)
        put(ws, r, 5, c["run_id"])
        put(ws, r, 6, c["metric"])
        fmt = PCT if "acc" in c["metric"] else ("#,##0" if c["metric"] == "n_params" else "0.0000")
        put(ws, r, 7, c["value"], fmt=fmt)
        cl = col[c["metric"]]
        put(ws, r, 8, f'=IFERROR(INDEX(NhatKy!${cl}$2:${cl}$1000,MATCH(E{r},NhatKy!$W$2:$W$1000,0)),"KHÔNG THẤY")', fmt=fmt)
        dec = c.get("decimals", 4)
        put(ws, r, 9, f'=IF(ISNUMBER(H{r}),IF(ROUND(G{r},{dec})=ROUND(H{r},{dec}),"✔","✘"),"✘")')
        gh = df.loc[df["run_id"] == c["run_id"], "github"]
        put(ws, r, 10, "mở" if len(gh) and gh.iloc[0] else "", link=(gh.iloc[0] if len(gh) and gh.iloc[0] else None))
    if cites:
        ws.conditional_formatting.add(f"I5:I{4 + len(cites)}", CellIsRule(operator="equal", formula=['"✔"'], fill=GOOD))
        ws.conditional_formatting.add(f"I5:I{4 + len(cites)}", CellIsRule(operator="equal", formula=['"✘"'], fill=BAD))
    ws.freeze_panes = "A5"


def build(path=None):
    df = T.scan()
    df = df[~df["quick"].astype(bool)].reset_index(drop=True) if len(df) and "quick" in df else df
    wb = Workbook()
    sheet_guide(wb, df)
    rowmap = sheet_journal(wb, df)
    sheet_summary(wb, df, rowmap)
    sheet_raci(wb, df)
    sheet_check(wb, df, rowmap)
    for ws in wb.worksheets:
        ws.sheet_view.zoomScale = 90
    wb.save(path or C.EXCEL_LOG)
    print("Đã dựng", os.path.relpath(path or C.EXCEL_LOG, C.ROOT), f"({len(df)} lần chạy)")
    return path or C.EXCEL_LOG


if __name__ == "__main__":
    build()
