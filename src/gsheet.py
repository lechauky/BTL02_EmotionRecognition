"""Ghi nhật ký thẳng lên Google Sheets (dùng trên Colab, sau khi xác thực tài khoản Google của người chạy).

Mỗi lần đồng bộ ghi lại toàn bộ sheet NhatKy (mọi lần chạy chính thức trong exps/ trên Drive, theo thứ tự thời gian)
và sheet TongHop, bằng tài khoản của người chạy -> mục 'Lịch sử phiên bản' của Google Sheets ghi rõ ai cập nhật,
lúc nào và thay đổi những dòng nào.
"""
from . import config as C
from . import tracking as T


def _open(sheet_url):
    from google.colab import auth                     # chỉ có trên Colab
    import google.auth
    import gspread
    auth.authenticate_user()
    creds, _ = google.auth.default()
    sh = gspread.authorize(creds).open_by_url(sheet_url or C.SHEETS_URL)
    if sh.locale != "en_US":                          # công thức dùng dấu phẩy, số dùng dấu chấm (như file Excel)
        sh.update_locale("en_US")
    return sh


def sync(sheet_url=None):
    from make_log import (CHECK_COLS, CHECK_NOTE, CHECK_TOP, NK_COLS, RACI_TASKS, SUM_TOP, check_values, journal_values,
                          load_citations, summary_rows, task_status)
    sh = _open(sheet_url)
    df = T.scan()
    df = df[~df["quick"].astype(bool)].reset_index(drop=True) if len(df) else df
    rows = [journal_values(i + 1, r) for i, r in df.iterrows()]

    ws = sh.worksheet("NhatKy")
    ncol = len(NK_COLS)
    last = chr(ord("A") + ncol - 1)
    ws.batch_clear([f"A2:{last}{max(ws.row_count, 2)}"])
    if rows:
        if ws.row_count < len(rows) + 1:
            ws.add_rows(len(rows) + 1 - ws.row_count)
        ws.update(values=rows, range_name="A2", value_input_option="USER_ENTERED")

    ts = sh.worksheet("TongHop")
    srows = summary_rows(df) if len(df) else []
    ts.batch_clear([f"A{SUM_TOP + 1}:O{SUM_TOP + 60}"])
    if srows:
        ts.update(values=srows, range_name=f"A{SUM_TOP + 1}", value_input_option="USER_ENTERED")

    hd = sh.worksheet("HuongDan")
    links = [[name, f'=HYPERLINK("{u}","{u}")' if u else "(điền sau)"] for name, u in
             (("Kho code + exps (GitHub)", C.GITHUB_REPO), ("Trọng số (Google Drive)", C.DRIVE_WEIGHTS_URL),
              ("Slide (PowerPoint)", C.SLIDES_URL), ("Nhật ký này (Google Sheets)", C.SHEETS_URL),
              ("Báo cáo (Word)", C.REPORT_URL))]
    hd.update(values=links, range_name="A5:B9", value_input_option="USER_ENTERED")
    pc = sh.worksheet("PhanCong")
    pc.update(values=[[task_status(prod, df)] for _, prod, _ in RACI_TASKS], range_name="H5")

    kt = sh.worksheet("KiemTra")
    crow = check_values(load_citations())
    kt.batch_clear([f"A2:K{max(kt.row_count, 2)}"])
    if kt.col_count < len(CHECK_COLS):
        kt.add_cols(len(CHECK_COLS) - kt.col_count)
    if kt.row_count < CHECK_TOP + len(crow) + 3:
        kt.add_rows(CHECK_TOP + len(crow) + 3 - kt.row_count)
    kt.update(values=[[CHECK_NOTE]], range_name="A2")
    kt.update(values=[[c for c, _ in CHECK_COLS]], range_name=f"A{CHECK_TOP}")
    if crow:
        n = CHECK_TOP + len(crow)
        kt.update(values=crow, range_name=f"A{CHECK_TOP + 1}", value_input_option="USER_ENTERED")
        kt.update(values=[["Số dòng khớp / tổng", "", "", "", "", "", f'=COUNTIF(J5:J{n},"✔")&"/"&{len(crow)}']],
                  range_name=f"D{n + 2}", value_input_option="USER_ENTERED")
    ok = sum(1 for r in crow if isinstance(r[8], float) and round(r[8], 4) == round(float(r[6]), 4))
    print(f"Đã cập nhật Google Sheets: NhatKy {len(rows)} lần chạy, TongHop {len(srows)} thí nghiệm, "
          f"KiemTra {len(crow)} trích dẫn ({ok} khớp với thư mục thực nghiệm).")
    return len(rows)
