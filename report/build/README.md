# Dựng báo cáo và slide từ exps/

Báo cáo (`report/BTL02_BaoCao_Nhom06.docx`) và slide (`report/BTL02_Slide_Nhom06.pptx`) được sinh tự động từ thư mục `exps/`,
nên mọi con số trùng với `metrics.json` / `final_result.json` của từng lần chạy.

1. `collect.py exps data.json` – gom metrics, meta, config, history và hình của mọi lần chạy chính thức (bỏ `--quick`).
2. `charts.py`, `slides.js` – dựng slide (pptxgenjs), tải lên Google Drive để chuyển thành Google Slides.
3. `report.js` – dựng báo cáo (docx-js) hai lượt để có mục lục kèm số trang (`toc.py`).
4. Mỗi con số in ra được ghi vào `report/citations.json` (tài liệu, vị trí, run_id, chỉ số, giá trị).
   Sheet **KiemTra** của nhật ký đọc file này và so sánh với sheet NhatKy và với metrics.json → cột Khớp ✔/✘.

`build_all.sh <exps> <thư mục ra>` chạy toàn bộ các bước (cần Node.js với `docx`, `pptxgenjs` và LibreOffice).
