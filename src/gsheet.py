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
    from make_log import NK_COLS, SUM_TOP, journal_values, summary_rows
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
    links = [[f'=HYPERLINK("{u}","{u}")' if u else "(điền sau)"] for u in
             (C.GITHUB_REPO, C.DRIVE_WEIGHTS_URL, C.SLIDES_URL, C.SHEETS_URL)]
    hd.update(values=links, range_name="B5:B8", value_input_option="USER_ENTERED")
    print(f"Đã cập nhật Google Sheets: NhatKy {len(rows)} lần chạy, TongHop {len(srows)} thí nghiệm.")
    return len(rows)
