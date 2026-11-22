"""Ghi nhật ký thẳng lên Google Sheets (dùng trên Colab, sau khi xác thực tài khoản Google của người chạy).

Mỗi lần đồng bộ, các lần chạy mới (chưa có run_id trong sheet NhatKy) được thêm vào cuối sheet bằng tài khoản
của người chạy -> mục 'Lịch sử phiên bản' của Google Sheets ghi rõ ai thêm dòng nào, lúc nào.
"""
import pandas as pd

from . import config as C
from . import tracking as T


def sync(sheet_url=None):
    from google.colab import auth                     # chỉ có trên Colab
    import google.auth
    import gspread
    auth.authenticate_user()
    creds, _ = google.auth.default()
    gc = gspread.authorize(creds)
    sh = gc.open_by_url(sheet_url or C.SHEETS_URL)
    ws = sh.worksheet("NhatKy")
    existing = ws.get_all_values()
    have = set()
    for row in existing[1:]:                         # cột W (23) chứa run_id (có thể là công thức HYPERLINK)
        if len(row) >= 23 and row[22]:
            have.add(row[22])
    df = T.scan()
    df = df[~df["quick"].astype(bool)].reset_index(drop=True)
    from make_log import journal_values
    n0 = len(existing) - 1
    new = [journal_values(n0 + k + 1, r) for k, (_, r) in enumerate(df[~df["run_id"].isin(have)].iterrows())]
    if new:
        ws.append_rows(new, value_input_option="USER_ENTERED")
    from make_log import SUM_TOP, summary_rows
    ts = sh.worksheet("TongHop")
    rows = summary_rows(df)
    ts.batch_clear([f"A{SUM_TOP + 1}:O{SUM_TOP + 60}"])
    if rows:
        ts.update(values=rows, range_name=f"A{SUM_TOP + 1}", value_input_option="USER_ENTERED")
    print(f"Đã thêm {len(new)} dòng mới vào Google Sheets (sheet NhatKy có {n0 + len(new)} dòng).")
    return len(new)
