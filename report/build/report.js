// Dựng báo cáo BTL02 (.docx) từ build/data.json. Mọi con số lấy từ thư mục thực nghiệm và được ghi vào citations.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType,
  BorderStyle, ShadingType, ImageRun, ExternalHyperlink, TableOfContents, PageBreak, Footer, PageNumber,
  LevelFormat, VerticalAlign, TabStopType, PositionalTab, PositionalTabAlignment, PositionalTabRelativeTo, PositionalTabLeader,
} = require("docx");
const sizeOf = (p) => { const b = fs.readFileSync(p); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; };

const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3];
const CIT = process.argv[4];
const L = {
  repo: D.repo, sheets: "https://docs.google.com/spreadsheets/d/17R3AmpbdE-dxEJrX0fMZhDw2iZWPCG3-ITbCVEo-V0E/edit",
  drive: "https://drive.google.com/drive/folders/16lyivk-DlgbP9q31Oxg2acJtdwTRiyyV",
  slides: process.env.SLIDES_URL || "",
};
const R = D.latest, F = D.final;
const FONT = "Times New Roman";
const W = 9638; // độ rộng vùng chữ (A4, lề 2 cm)

// ---------- mục lục tĩnh (số trang lấy từ lần dựng trước, để Google Docs cũng hiển thị) ----------
const TOC = process.env.TOC_JSON && fs.existsSync(process.env.TOC_JSON) ? JSON.parse(fs.readFileSync(process.env.TOC_JSON, "utf8")) : {};
const HEADS = [];
function tocParas() {
  const order = TOC.__order || [];
  if (!order.length) return [];
  const nb = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const bd = { top: nb, bottom: nb, left: nb, right: nb };
  const sub = (h) => /^\d+\.\d/.test(h);
  return [new Table({ width: { size: 9638, type: WidthType.DXA }, columnWidths: [8838, 800], borders: { ...bd, insideHorizontal: nb, insideVertical: nb },
    rows: order.map((h) => new TableRow({ children: [
      new TableCell({ borders: bd, width: { size: 8838, type: WidthType.DXA }, margins: { top: 30, bottom: 30, left: sub(h) ? 400 : 0 },
        children: [new Paragraph({ children: [new TextRun({ text: h, font: "Times New Roman", size: 24, bold: !sub(h) })] })] }),
      new TableCell({ borders: bd, width: { size: 800, type: WidthType.DXA }, margins: { top: 30, bottom: 30 },
        children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: String(TOC[h] || ""), font: "Times New Roman", size: 24, bold: !sub(h) })] })] }),
    ] })) })];
}
// ---------- trích dẫn ----------
const cites = [];
let WHERE = "";
const pct = (x) => (100 * x).toFixed(2).replace(".", ",") + "%";
const dec = (x, n = 4) => x.toFixed(n).replace(".", ",");
const int = (x) => Math.round(x).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
function cite(run, metric, opt = {}) {
  const isFinal = opt.final;
  const v = isFinal ? F[metric] : run.metrics[metric];
  const rid = isFinal ? F.run_id : run.run_id;
  const val = metric === "n_params" ? v : Math.round(v * 1e4) / 1e4;
  const key = isFinal ? "FINAL" : run.key;
  if (!opt.nocite) cites.push({ doc: "Báo cáo", where: opt.where || WHERE, text: `${key} – ${metric}${isFinal ? " (FINAL)" : ""}`,
    run_id: rid, metric, value: val, decimals: metric === "n_params" ? 0 : 4, ...(isFinal ? { source: "final" } : {}) });
  if (metric === "n_params") return int(v);
  if (metric.includes("loss")) return dec(v);
  return pct(v);
}

// ---------- tiện ích ----------
const t = (s, o = {}) => new TextRun({ text: s, font: FONT, size: o.size || 26, ...o });
const P = (parts, o = {}) => new Paragraph({
  children: (Array.isArray(parts) ? parts : [parts]).map((x) => (typeof x === "string" ? t(x) : x)),
  spacing: { after: 120, line: 312 }, alignment: o.align || AlignmentType.JUSTIFIED, ...o,
});
const link = (text, url, o = {}) => new ExternalHyperlink({ link: url, children: [t(text, { style: "Hyperlink", color: "0563C1", underline: {}, ...o })] });
const H1 = (s) => (HEADS.push(s), new Paragraph({ heading: HeadingLevel.HEADING_1, children: [t(s)], pageBreakBefore: true }));
const H2 = (s) => { WHERE = s.split(" ")[0]; HEADS.push(s); return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [t(s)] }); };
const H3 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [t(s)] });
const B = (parts, lvl = 0) => new Paragraph({
  children: (Array.isArray(parts) ? parts : [parts]).map((x) => (typeof x === "string" ? t(x) : x)),
  numbering: { reference: "bul", level: lvl }, spacing: { after: 60, line: 300 }, alignment: AlignmentType.JUSTIFIED,
});
let figNo = 0, tabNo = 0;
function img(p, widthCm, caption, url) {
  if (!p || !fs.existsSync(p)) return [P([t(`[thiếu hình: ${caption}]`, { italics: true, color: "C00000" })])];
  const { w, h } = sizeOf(p);
  const wpx = Math.min(widthCm, 16.5) * 37.8;
  figNo++;
  const cap = [t(`Hình ${figNo}. ${caption}`, { italics: true, size: 22 })];
  if (url) cap.push(t(" – ", { size: 22 }), link("thư mục thực nghiệm", url, { size: 22, italics: true }));
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(p), transformation: { width: wpx, height: (wpx * h) / w },
        altText: { title: caption, description: caption, name: path.basename(p) } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: cap }),
  ];
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "A6A6A6" };
const borders = { top: border, bottom: border, left: border, right: border };
function cell(c, w, o = {}) {
  const kids = (Array.isArray(c) ? c : [c]).map((x) => (typeof x === "string" ? t(x, { size: o.size || 20, bold: o.bold, color: o.color }) : x));
  return new TableCell({
    borders, width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 50, bottom: 50, left: 80, right: 80 },
    children: [new Paragraph({ alignment: o.align || AlignmentType.LEFT, children: kids })],
  });
}
function table(head, rows, widths, caption, o = {}) {
  tabNo++;
  const hr = new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, widths[i], { bold: true, color: "FFFFFF", fill: "1F4E79", align: AlignmentType.CENTER })) });
  const body = rows.map((r, ri) => new TableRow({ children: r.map((c, i) => cell(c, widths[i], {
    align: (o.align && o.align[i]) || AlignmentType.LEFT, fill: o.hl && o.hl(ri) ? "E2EFDA" : (ri % 2 ? "F2F2F2" : undefined) })) }));
  return [
    new Paragraph({ keepNext: true, spacing: { before: 160, after: 80 }, alignment: AlignmentType.CENTER, children: [t(`Bảng ${tabNo}. ${caption}`, { bold: true, size: 22 })] }),
    new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths, rows: [hr, ...body] }),
    new Paragraph({ spacing: { after: 120 }, children: [] }),
  ];
}
const C = AlignmentType.CENTER, RT = AlignmentType.RIGHT;
const lnk = (u, s = "mở", size = 20) => new ExternalHyperlink({ link: u, children: [t(s, { style: "Hyperlink", color: "0563C1", underline: {}, size })] });
const gap = (r) => r.metrics.train_acc_at_best - r.metrics.valid_acc;
const base = R.A2;
const delta = (r) => { const d = 100 * (r.metrics.valid_acc - base.metrics.valid_acc); return (d >= 0 ? "+" : "−") + Math.abs(d).toFixed(2).replace(".", ","); };

function groupTable(g, caption) {
  const keys = Object.keys(R).filter((k) => R[k].group === g).sort();
  const rows = keys.map((k) => {
    const r = R[k];
    WHERE = `Bảng ${tabNo + 1} – ${k}`;
    return [k, r.description, cite(r, "n_params"), `${r.metrics.best_epoch}/${r.metrics.epochs_run}`,
      pct(r.metrics.train_acc_at_best), cite(r, "valid_acc"), delta(r), cite(r, "test_acc"), cite(r, "test_f1"), lnk(r.url, r.version)];
  });
  const best = Math.max(...keys.map((k) => R[k].metrics.valid_acc));
  return table(["Mã", "Nội dung thay đổi so với baseline", "Số tham số", "Epoch tốt nhất/chạy", "Train acc*", "Valid acc", "Δ so với A2 (điểm %)", "Test acc", "Test macro-F1", "Thư mục"],
    rows, [520, 2560, 1080, 760, 800, 820, 800, 800, 820, 678], caption,
    { align: [C, AlignmentType.LEFT, RT, C, RT, RT, RT, RT, RT, C], hl: (i) => R[keys[i]].metrics.valid_acc === best });
}
function curve(k, w = 15) { const r = R[k]; return img(r.figures.training_curves, w, `Đường học (loss, accuracy) của ${k} – ${r.description}`, r.url); }

// ---------- nội dung ----------
const members = [
  ["TV1", "Lê Châu Kỳ", "3123411173", "data.py, run_data.py, tracking.py, make_log.py, gsheet.py", "B"],
  ["TV2", "Trần Thanh Huyền", "3123411126", "models.py", "A"],
  ["TV3", "Vũ Hoàng Phương", "3123411238", "train.py", "C"],
  ["TV4", "Đỗ Minh Thương", "3123411294", "evaluate.py, visualize.py, run_final.py", "D"],
];
const nRuns = (name) => D.runs.filter((r) => r.author === name).length;
const st = D.stats;
const cls = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"];
const vi = { Angry: "Giận", Disgust: "Ghê tởm", Fear: "Sợ", Happy: "Vui", Sad: "Buồn", Surprise: "Ngạc nhiên", Neutral: "Bình thường" };
const body = [];
const add = (...xs) => xs.forEach((x) => (Array.isArray(x) ? body.push(...x) : body.push(x)));

// Bìa
const cover = [
  P(t("TRƯỜNG ĐẠI HỌC SÀI GÒN", { bold: true, size: 28 }), { align: C, spacing: { after: 60 } }),
  P(t("KHOA CÔNG NGHỆ THÔNG TIN", { bold: true, size: 28 }), { align: C, spacing: { after: 1200 } }),
  P(t("HỌC SÂU (DEEP LEARNING)", { bold: true, size: 30 }), { align: C, spacing: { after: 400 } }),
  P(t("BÀI TẬP LỚN 02", { bold: true, size: 36, color: "1F4E79" }), { align: C, spacing: { after: 200 } }),
  P(t("NHẬN DẠNG CẢM XÚC KHUÔN MẶT BẰNG MẠNG TÍCH CHẬP (CNN)", { bold: true, size: 34, color: "1F4E79" }), { align: C, spacing: { after: 120 } }),
  P(t("Facial Expression Recognition on FER2013 with CNN (PyTorch)", { italics: true, size: 26 }), { align: C, spacing: { after: 900 } }),
  P([t("Lớp: ", { bold: true }), t("SGU26K2_HocSau_S5_DCT123C4_0709")], { align: C, spacing: { after: 60 } }),
  P([t("Giảng viên: ", { bold: true }), t("Đỗ Như Tài")], { align: C, spacing: { after: 60 } }),
  P([t("Nhóm thực hiện: ", { bold: true }), t("Nhóm 06")], { align: C, spacing: { after: 240 } }),
  ...table(["STT", "Họ và tên", "MSSV", "Nhóm thực nghiệm"], members.map((m, i) => [String(i + 1), m[1], m[2], m[4]]),
    [800, 3800, 2200, 2000], "Thành viên nhóm 06", { align: [C, AlignmentType.LEFT, C, C] }),
  P(t("TP. Hồ Chí Minh, tháng 11 năm 2026", { italics: true }), { align: C, spacing: { before: 600 } }),
  new Paragraph({ children: [new PageBreak()] }),
  P(t("MỤC LỤC", { bold: true, size: 30 }), { align: C }),
  ...tocParas(),
];

// 0. Liên kết
add(H1("0. LIÊN KẾT VÀ CÁCH KIỂM TRA TÍNH THỐNG NHẤT"));
add(P("Báo cáo này là một trong bốn sản phẩm liên kết với nhau. Mọi con số trong báo cáo và slide đều lấy trực tiếp từ thư mục thực nghiệm (exps/) và được ghi kèm mã lần chạy (run_id), nên có thể lần ngược từ báo cáo → nhật ký → thư mục thực nghiệm."));
WHERE = "Bảng 2";
add(table(["Sản phẩm", "Nội dung", "Liên kết"], [
  ["Nhật ký thực nghiệm (Google Sheets)", "NhatKy: mỗi lần chạy một dòng · TongHop: mỗi thí nghiệm một dòng · PhanCong: ma trận RACI · KiemTra: đối chiếu số liệu. Xem File → Lịch sử phiên bản để biết ai cập nhật, lúc nào.", lnk(L.sheets, "Google Sheets")],
  ["Slide (Google Slides)", "Tóm tắt kết quả; mỗi bảng số liệu có liên kết tới nhật ký và thư mục thực nghiệm.", L.slides ? lnk(L.slides, "Google Slides") : "(điền sau)"],
  ["Mã nguồn + exps (GitHub)", "Code PyTorch, notebook Colab, toàn bộ exps/ (cấu hình, lịch sử huấn luyện, chỉ số, hình) trừ trọng số.", lnk(L.repo, "GitHub")],
  ["Trọng số mô hình (Google Drive)", "exps/ đầy đủ kèm checkpoints/best.pt của từng lần chạy.", lnk(L.drive, "Google Drive")],
], [2400, 5638, 1600], "Các sản phẩm của bài tập và liên kết", { align: [AlignmentType.LEFT, AlignmentType.LEFT, C] }));
add(P([t("Cách kiểm tra: ", { bold: true }), t("(1) mỗi ô số liệu trong các bảng ở mục 5–6 có liên kết tới thư mục của lần chạy trên GitHub; trong thư mục đó, metrics.json chứa đúng con số được trích, history.csv chứa từng epoch, config.json chứa cấu hình, meta.json ghi người chạy, thời gian, GPU và commit. (2) Danh sách tất cả con số được trích dẫn nằm ở report/citations.json; sheet KiemTra so sánh từng con số với sheet NhatKy (bằng công thức) và với metrics.json trong thư mục thực nghiệm, cột Khớp phải là ✔. (3) Phụ lục A liệt kê các trích dẫn này.")]));
add(P([t("Quy tắc đặt tên thư mục: ", { bold: true }), t("exps/<nhóm>/<mã>_<dữ liệu>_<mô hình>_<tối ưu>_<yymmdd-HHMM>/, ví dụ "), t(R.A2.run_id, { italics: true }), t(" là thí nghiệm A2, dữ liệu FER2013 tăng cường chuẩn, mô hình medium-ReLU-BatchNorm, Adam lr 0,001, chạy lúc 10:15 ngày 25/11/2026. Mỗi lần chạy tạo một thư mục mới, không ghi đè; chạy lại cùng mã thì phiên bản tăng (v1, v2…).")]));

// 1. Giới thiệu & phân công
add(H1("1. GIỚI THIỆU VÀ PHÂN CÔNG"));
add(H2("1.1. Bài toán"));
add(P("Bài toán nhận dạng cảm xúc khuôn mặt (Facial Expression Recognition) trên bộ dữ liệu FER2013 của cuộc thi Kaggle “Challenges in Representation Learning”: đầu vào là ảnh xám 48×48, đầu ra là một trong 7 lớp cảm xúc (0 = Angry, 1 = Disgust, 2 = Fear, 3 = Happy, 4 = Sad, 5 = Surprise, 6 = Neutral). Theo đề bài, độ chính xác tốt nhất thế giới là khoảng 69% trên tập PublicTest và 71% trên tập PrivateTest."));
add(P("Nhóm cài đặt bằng PyTorch, viết lại bốn mô hình CNN của bài mẫu (SMALL, MEDIUM, MEDIUM_01, LARGE) và thử nghiệm có hệ thống ba hướng cải thiện mà đề bài gợi ý: thiết kế mô hình, kỹ thuật huấn luyện (tăng cường dữ liệu, thuật toán tối ưu) và hàm kích hoạt; thêm một nhóm học chuyển giao (VGG16, ResNet18) như phần Fine-tune With VGG16 của bài mẫu. Tổng cộng 15 thí nghiệm, " + D.runs.length + " lần chạy chính thức trên GPU Tesla T4 (Google Colab)."));
add(H2("1.2. Phân công thành viên"));
add(P("Mỗi thành viên phụ trách một phần mã nguồn và một nhóm thực nghiệm, tự chạy nhóm thực nghiệm của mình trên Colab bằng tài khoản Google của mình (nên nhật ký ghi đúng người chạy và lịch sử phiên bản của Google Sheets ghi đúng người cập nhật). Ma trận RACI đầy đủ ở sheet PhanCong."));
add(table(["TV", "Họ tên", "MSSV", "Phần mã nguồn", "Nhóm TN", "Số lần chạy", "Đóng góp"],
  members.map((m) => [m[0], m[1], m[2], m[3], m[4], String(nRuns(m[1])), "25%"]),
  [560, 2000, 1300, 3058, 900, 920, 900], "Phân công và đóng góp (số lần chạy đếm từ nhật ký)", { align: [C, AlignmentType.LEFT, C, AlignmentType.LEFT, C, C, C] }));
add(table(["Đầu việc", "Kỳ", "Huyền", "Phương", "Thương"], [
  ["Dữ liệu, tăng cường dữ liệu", "R/A", "C", "I", "I"], ["Kiến trúc CNN (models.py)", "C", "R/A", "C", "I"],
  ["Vòng lặp huấn luyện, callback (train.py)", "I", "C", "R/A", "C"], ["Đánh giá, trực quan hóa bộ lọc", "I", "C", "C", "R/A"],
  ["Quản lý thực nghiệm, nhật ký Sheets, GitHub", "R/A", "I", "I", "C"], ["Thực nghiệm nhóm A – kiến trúc", "I", "R/A", "C", "I"],
  ["Thực nghiệm nhóm B – huấn luyện", "R/A", "I", "C", "I"], ["Thực nghiệm nhóm C – kích hoạt, điều chuẩn", "I", "C", "R/A", "I"],
  ["Thực nghiệm nhóm D – học chuyển giao", "I", "C", "I", "R/A"], ["Chọn mô hình cuối, đánh giá PrivateTest", "C", "C", "C", "R/A"],
  ["Báo cáo, slide (mỗi người phần của mình)", "R", "R", "R", "R/A"], ["Kiểm tra thống nhất báo cáo – slide – nhật ký", "R", "C", "C", "A"],
], [4838, 1200, 1200, 1200, 1200], "Ma trận RACI (R thực hiện · A chịu trách nhiệm cuối · C góp ý · I được thông báo)", { align: [AlignmentType.LEFT, C, C, C, C] }));

// 2. Dữ liệu
add(H1("2. XỬ LÝ DỮ LIỆU"));
add(H2("2.1. Đọc dữ liệu và chia tập"));
add(P(`File fer2013.csv gồm 35.887 ảnh, mỗi dòng có nhãn emotion, chuỗi 2.304 giá trị điểm ảnh và cột Usage. Hàm prepare() trong src/data.py tách chuỗi thành mảng 48×48, chuẩn hóa về [0, 1] rồi lưu đệm thành fer2013.npz để các lần chạy sau đọc nhanh. Ba tập được giữ đúng như cuộc thi: Training (${int(st.train.n)} ảnh) để học; PublicTest (${int(st.valid.n)} ảnh) làm tập kiểm định (valid) để dừng sớm và chọn mô hình; PrivateTest (${int(st.test ? st.test.n : 3589)} ảnh) làm tập kiểm tra (test), chỉ dùng để báo cáo. Ảnh được chuẩn hóa theo trung bình ${dec(st.mean, 4)} và độ lệch chuẩn ${dec(st.std, 4)} tính trên tập Training.`));
add(H2("2.2. Mã hóa nhãn"));
add(P("Bài mẫu Keras chuyển nhãn sang one-hot để dùng categorical_crossentropy. Trong PyTorch, nn.CrossEntropyLoss nhận trực tiếp chỉ số lớp (0–6) và tương đương toán học với one-hot + softmax + cross-entropy, nên nhóm giữ nhãn dạng số nguyên; với label smoothing (thí nghiệm B4) PyTorch tự tạo phân phối mục tiêu mềm."));
add(H2("2.3. Khảo sát dữ liệu"));
add(P(`Dữ liệu mất cân bằng mạnh: Happy chiếm ${pct(st.train.ratio.Happy)} tập Training trong khi Disgust chỉ có ${int(st.train.per_class.Disgust)} ảnh (${pct(st.train.ratio.Disgust)}). Vì vậy ngoài accuracy, báo cáo dùng thêm macro-F1 (trung bình F1 của 7 lớp, không bị lớp đông áp đảo).`));
add(img(D.datafig.histogram_data, 15, "Phân bố số ảnh theo lớp trên ba tập", L.repo + "/tree/main/exps/_data"));
add(img(D.datafig.training_images, 14, "Ảnh mẫu tập Training", L.repo + "/tree/main/exps/_data"));
add(H2("2.4. Tăng cường dữ liệu"));
add(P("Tương ứng ImageDataGenerator của bài mẫu, nhóm tự viết tăng cường dữ liệu chạy trên GPU theo từng batch (affine_grid + grid_sample) để không làm chậm vòng lặp: mức chuẩn (baseline) xoay ±10°, dịch ±10%, phóng to/thu nhỏ ±10%, lật ngang; mức mạnh (B2) xoay ±20°, dịch ±15%, zoom ±15%, lật ngang và xóa ngẫu nhiên một vùng (random erasing, xác suất 0,5). Chỉ tập Training được tăng cường."));
add(img(D.datafig.augmentation, 14, "Một ảnh qua các phép tăng cường dữ liệu", L.repo + "/tree/main/exps/_data"));

// 3. Mô hình & huấn luyện
add(H1("3. MÔ HÌNH VÀ HUẤN LUYỆN"));
add(H2("3.1. Kiến trúc CNN"));
add(P("Bốn mô hình viết lại từ bài mẫu, cùng cấu trúc khối: [Conv3×3 → BatchNorm → kích hoạt] × n → MaxPool 2×2 → Dropout 0,2; sau các khối là Flatten → FC → BatchNorm1d → kích hoạt → Dropout 0,5 → FC 7 lớp. So với bài mẫu, nhóm thêm BatchNorm (cả ở lớp FC) vì khi thử không có BatchNorm ở lớp FC mô hình đứng ở khoảng 25% accuracy (luôn đoán Happy) với lr 0,001."));
WHERE = "Bảng 5";
add(table(["Mô hình", "Mã", "Các khối tích chập (số kênh)", "FC", "Số tham số"], [
  ["SMALL", "A1", "[64, 64] · [128, 128, 256, 256]", "1024", cite(R.A1, "n_params")],
  ["MEDIUM (baseline)", "A2", "[64, 64] · [128 ×3] · [256 ×3]", "1024", cite(R.A2, "n_params")],
  ["MEDIUM_01", "A3", "[64 ×3] · [128 ×4] · [256 ×4]", "1024", cite(R.A3, "n_params")],
  ["LARGE", "A4", "[64 ×4] · [128 ×4] · [256 ×4] · [512 ×4]", "2048", cite(R.A4, "n_params")],
  ["VGG16-BN (ImageNet)", "D2", "13 lớp conv của VGG16-BN, ảnh 96×96", "512", cite(R.D2, "n_params")],
  ["ResNet18 (ImageNet)", "D1", "ResNet18, ảnh 96×96", "–", cite(R.D1, "n_params")],
], [2100, 700, 3938, 900, 2000], "Các kiến trúc được thử nghiệm", { align: [AlignmentType.LEFT, C, AlignmentType.LEFT, C, RT] }));
add(P("SMALL có nhiều tham số nhất trong bốn CNN dù nông nhất: chỉ có hai lần MaxPool nên bản đồ đặc trưng cuối còn 12×12×256 = 36.864 giá trị, nối toàn bộ với lớp FC 1024 nơ-ron (≈ 37,7 triệu trọng số). Các mô hình sâu hơn giảm kích thước không gian xuống 6×6 hoặc 3×3 trước lớp FC nên lớp FC nhỏ hơn nhiều."));
add(H2("3.2. Học chuyển giao"));
add(P("Lớp TransferNet phóng ảnh 48×48 lên 96×96, lặp 1 kênh xám thành 3 kênh rồi chuẩn hóa theo ImageNet; ResNet18 thay lớp fc cuối bằng FC 7 lớp, VGG16-BN thay bộ phân loại bằng AdaptiveAvgPool → FC 512 → ReLU → Dropout 0,5 → FC 7. Toàn bộ mạng được fine-tune với lr nhỏ (3e-4 cho ResNet18, 1e-4 cho VGG16-BN)."));
add(H2("3.3. Cấu hình huấn luyện chuẩn (baseline A2)"));
add(table(["Tham số", "Giá trị", "Ghi chú"], [
  ["Mô hình", "MEDIUM, ReLU, BatchNorm, Dropout 0,2 / 0,5", "src/models.py"],
  ["Tối ưu", "Adam, lr 0,001, batch 128", "B3 đổi sang SGD momentum 0,9, lr 0,01"],
  ["Hàm mất mát", "CrossEntropyLoss", "B4 thêm label smoothing 0,1"],
  ["Tăng cường", "Mức chuẩn (mục 2.4)", "B1 bỏ, B2 tăng mạnh"],
  ["Số epoch tối đa", "60", "Dừng sớm nếu valid loss không giảm 10 epoch"],
  ["Giảm lr", "ReduceLROnPlateau ×0,5 sau 4 epoch", "lr tối thiểu 1e-6"],
  ["Lưu mô hình", "checkpoints/best.pt theo valid loss nhỏ nhất", "Chỉ số báo cáo lấy ở epoch tốt nhất"],
  ["Tốc độ", "Mixed precision (AMP), dữ liệu giữ sẵn trên GPU", "Tesla T4"],
  ["Tái lập", "seed 42, cấu hình lưu ở config.json", "Chạy lại B1–B4 cho kết quả trùng khớp (mục 5.3)"],
], [2300, 3900, 3438], "Cấu hình chuẩn; mỗi thí nghiệm chỉ đổi MỘT yếu tố so với bảng này"));
add(H2("3.4. Vòng lặp huấn luyện và callback"));
add(P("Hàm train_model() trong src/train.py thực hiện mỗi epoch: (1) tăng cường batch trên GPU, (2) lan truyền thuận trong autocast, (3) tính loss, (4) lan truyền ngược qua GradScaler, (5) cập nhật trọng số; sau đó đánh giá trên valid và ghi một dòng vào history.csv. Ba callback tương ứng bài mẫu: ModelCheckpoint (lưu best.pt khi valid loss giảm), EarlyStopping (patience 10) và ReduceLROnPlateau (patience 4, factor 0,5). Cuối lần chạy, mô hình tốt nhất được nạp lại để đánh giá trên valid và test, lưu metrics.json, ma trận nhầm lẫn, ca đúng/sai, bộ lọc và README.md của thư mục."));

// 4. Mã nguồn
add(H1("4. TÓM TẮT MÃ NGUỒN"));
add(table(["File", "Chức năng", "Người viết"], [
  ["src/config.py", "Đường dẫn, danh sách lớp, thành viên, cấu hình chuẩn (BASELINE), giờ Việt Nam", "Kỳ"],
  ["src/experiments.py", "Danh sách 15 thí nghiệm A1–D2, mỗi thí nghiệm là phần thay đổi so với baseline", "Cả nhóm"],
  ["src/data.py, run_data.py", "Đọc CSV/zip, chia tập, chuẩn hóa, tăng cường trên GPU, DeviceLoader, hình khảo sát dữ liệu", "Kỳ"],
  ["src/models.py", "FERCNN (small/medium/medium01/large, chọn kích hoạt, BN, dropout), TransferNet", "Huyền"],
  ["src/train.py", "train_model(): AMP, checkpoint, early stopping, ReduceLROnPlateau; evaluate_loader() (có TTA)", "Phương"],
  ["src/evaluate.py, src/visualize.py", "Chỉ số, ma trận nhầm lẫn, ca đúng/sai, bộ lọc conv đầu/cuối, feature map, đường học, so sánh", "Thương"],
  ["src/tracking.py", "Tạo thư mục thực nghiệm, ghi config/meta/metrics/README, quét exps/ → registry.csv", "Kỳ"],
  ["make_log.py, src/gsheet.py", "Dựng nhật ký Excel và ghi thẳng lên Google Sheets (NhatKy, TongHop, PhanCong, KiemTra)", "Kỳ"],
  ["run_experiment.py", "Chạy một thí nghiệm (--exp) hoặc cả nhóm (--group), ghi tác giả, ghi chú", "Cả nhóm"],
  ["run_final.py", "So sánh tất cả, chọn mô hình theo valid acc, đánh giá PrivateTest (có/không TTA), trực quan hóa", "Thương"],
  ["notebooks/BTL02_Colab.ipynb", "Notebook chạy trên Colab: mount Drive, clone repo, chạy nhóm, đồng bộ Sheets", "Kỳ"],
], [2700, 5638, 1300], "Cấu trúc mã nguồn (GitHub)"));
add(P(["Ví dụ chạy: ", t("python run_experiment.py --group A --author \"Trần Thanh Huyền\"", { font: "Consolas", size: 22 }), t(" rồi "), t("python run_final.py", { font: "Consolas", size: 22 }), t(". Mã nguồn đầy đủ: "), link("GitHub", L.repo), t(".")]));

// 5. Thực nghiệm
add(H1("5. KẾT QUẢ THỰC NGHIỆM"));
add(H2("5.1. Quản lý thực nghiệm"));
add(P(`Mỗi lần chạy tạo một thư mục riêng gồm config.json (cấu hình đầy đủ), meta.json (người chạy, thời gian theo giờ Việt Nam, GPU, phiên bản PyTorch, commit Git, lệnh chạy), history.csv (từng epoch), metrics.json (chỉ số ở epoch tốt nhất), figures/ và README.md. Sau khi chạy, người chạy đồng bộ nhật ký lên Google Sheets bằng tài khoản của mình. Tổng cộng ${D.runs.length} lần chạy chính thức (không tính các lần chạy thử --quick). Bảng dưới đây tóm tắt từng nhóm; * Train acc là độ chính xác trên Training ở epoch tốt nhất (có tăng cường), dòng tô xanh là tốt nhất nhóm theo valid acc. Mọi so sánh dùng valid acc (PublicTest) vì đó là tập chọn mô hình; test acc (PrivateTest) chỉ để báo cáo.`));
add(img(D.summary.compare_all, 16, "Valid acc và test acc của 15 thí nghiệm (phiên bản mới nhất)", L.repo + "/tree/main/exps/_summary"));

// A
add(H2("5.2. Nhóm A – Kiến trúc CNN (Trần Thanh Huyền)"));
add(groupTable("A", "Nhóm A – so sánh bốn kiến trúc của bài mẫu"));
WHERE = "5.2 – phân tích";
add(P(`MEDIUM (A2, baseline) cho valid acc cao nhất nhóm (${cite(R.A2, "valid_acc")}). Mô hình sâu hơn không tốt hơn: MEDIUM_01 (A3) đạt ${cite(R.A3, "valid_acc")} và LARGE (A4) đạt ${cite(R.A4, "valid_acc")} dù gần gấp đôi số tham số và thời gian huấn luyện của A4 gấp khoảng ${(R.A4.metrics.train_time_s / R.A2.metrics.train_time_s).toFixed(1).replace(".", ",")} lần. Với ảnh 48×48 và chưa tới 29 nghìn ảnh huấn luyện, thêm lớp làm mô hình khó tối ưu hơn mà không có thêm thông tin để học.`));
add(P(`SMALL (A1) là trường hợp đáng chú ý: valid acc thấp hơn A2 (${cite(R.A1, "valid_acc")}) nhưng test acc lại cao nhất nhóm (${cite(R.A1, "test_acc")}). Chênh lệch giữa các kiến trúc chỉ 1–2 điểm phần trăm và thứ hạng trên valid và test không trùng nhau, cho thấy khác biệt ở mức này gần với dao động ngẫu nhiên giữa hai tập 3.589 ảnh; nhóm vẫn chọn theo valid để không “nhìn trộm” tập test.`));
add(curve("A2"));

// B
add(H2("5.3. Nhóm B – Kỹ thuật huấn luyện (Lê Châu Kỳ)"));
add(groupTable("B", "Nhóm B – tăng cường dữ liệu, thuật toán tối ưu, label smoothing"));
WHERE = "5.3 – phân tích";
add(P(`Tăng cường dữ liệu là yếu tố ảnh hưởng lớn nhất trong toàn bộ thực nghiệm. Bỏ tăng cường (B1), valid acc giảm còn ${cite(R.B1, "valid_acc")} (${delta(R.B1)} điểm so với A2); mô hình đạt tốt nhất ngay ở epoch ${R.B1.metrics.best_epoch} rồi valid loss tăng nên dừng ở epoch ${R.B1.metrics.epochs_run}, khoảng cách train – valid lên tới ${(100 * gap(R.B1)).toFixed(1).replace(".", ",")} điểm: quá khớp rõ rệt. Tăng cường mạnh (B2) làm khoảng cách này giảm còn ${(100 * gap(R.B2)).toFixed(1).replace(".", ",")} điểm nhưng mô hình học chậm hơn và valid acc (${cite(R.B2, "valid_acc")}) thấp hơn mức chuẩn một chút trong giới hạn 60 epoch.`));
add(P(`SGD momentum (B3) đạt ${cite(R.B3, "valid_acc")}, gần với Adam nhưng không vượt. Label smoothing 0,1 (B4) là thay đổi duy nhất vượt baseline trên valid (${cite(R.B4, "valid_acc")}, ${delta(R.B4)} điểm) và cho test acc cao nhất trong cả 15 thí nghiệm (${cite(R.B4, "test_acc")}, macro-F1 ${cite(R.B4, "test_f1")}). Label smoothing phạt mô hình khi quá tự tin, hợp với FER2013 vốn có nhiều ảnh gán nhãn nhập nhằng (ví dụ Fear/Surprise, Sad/Neutral).`));
const v1 = D.runs.filter((r) => r.group === "B" && r.version === "v1"), v2 = D.runs.filter((r) => r.group === "B" && r.version === "v2");
if (v1.length && v2.length) {
  WHERE = "Bảng " + (tabNo + 1);
  add(P("Kiểm tra khả năng tái lập: nhóm B được chạy hai lần (23/11 và 25/11, commit khác nhau nhưng cùng cấu hình và seed 42). Hai phiên bản cho chỉ số trùng khớp tới 4 chữ số, chỉ khác thời gian chạy, chứng tỏ kết quả có thể tái lập; nhật ký giữ cả hai phiên bản."));
  add(table(["Mã", "v1 – valid acc", "v2 – valid acc", "v1 – test acc", "v2 – test acc", "v1 / v2"],
    v2.map((b) => { const a = v1.find((x) => x.key === b.key); return [b.key, cite(a, "valid_acc"), cite(b, "valid_acc"), cite(a, "test_acc"), cite(b, "test_acc"), [lnk(a.url, "v1"), t(" / ", { size: 20 }), lnk(b.url, "v2")]]; }),
    [900, 1750, 1750, 1750, 1750, 1738], "Nhóm B chạy hai lần: kết quả trùng khớp", { align: [C, RT, RT, RT, RT, C] }));
}
add(curve("B1"));
add(curve("B4"));

// C
add(H2("5.4. Nhóm C – Hàm kích hoạt và điều chuẩn (Vũ Hoàng Phương)"));
add(groupTable("C", "Nhóm C – hàm kích hoạt, BatchNorm, Dropout"));
WHERE = "5.4 – phân tích";
add(P(`Sigmoid (C1) kém nhất nhóm (${cite(R.C1, "valid_acc")}): đạo hàm sigmoid tối đa 0,25 nên gradient suy giảm qua 8 lớp tích chập; mô hình vẫn đang cải thiện ở epoch ${R.C1.metrics.best_epoch}/${R.C1.metrics.epochs_run} và khoảng cách train – valid chỉ ${(100 * gap(R.C1)).toFixed(1).replace(".", ",")} điểm, tức là học chưa đủ (underfitting) chứ không phải quá khớp. LeakyReLU (C3, ${cite(R.C3, "valid_acc")}) và ELU (C2, ${cite(R.C2, "valid_acc")}) gần ReLU nhưng không vượt; với BatchNorm đứng trước, hiện tượng “ReLU chết” ít xảy ra nên phần âm của LeakyReLU/ELU không mang lại thêm lợi ích.`));
add(P(`Bỏ BatchNorm (C4) giảm còn ${cite(R.C4, "valid_acc")} và cần tới ${R.C4.metrics.best_epoch} epoch mới đạt tốt nhất (baseline cần ${R.A2.metrics.best_epoch}): BatchNorm chủ yếu giúp hội tụ nhanh và ổn định. Bỏ Dropout (C5) đạt ${cite(R.C5, "valid_acc")} nhưng tốt nhất sớm ở epoch ${R.C5.metrics.best_epoch} với khoảng cách train – valid ${(100 * gap(R.C5)).toFixed(1).replace(".", ",")} điểm (baseline ${(100 * gap(R.A2)).toFixed(1).replace(".", ",")}): Dropout là cơ chế chống quá khớp quan trọng thứ hai sau tăng cường dữ liệu.`));
add(curve("C1"));

// D
add(H2("5.5. Nhóm D – Học chuyển giao (Đỗ Minh Thương)"));
add(groupTable("D", "Nhóm D – fine-tune mô hình tiền huấn luyện ImageNet"));
WHERE = "5.5 – phân tích";
add(P(`VGG16-BN (D2) cho valid acc cao nhất trong toàn bộ 15 thí nghiệm (${cite(R.D2, "valid_acc")}), nhưng chỉ hơn baseline ${delta(R.D2)} điểm trong khi mỗi epoch chậm hơn nhiều (ảnh 96×96, ${R.D2.metrics.epochs_run} epoch mất ${(R.D2.metrics.train_time_s / 60).toFixed(1).replace(".", ",")} phút). Cả D1 và D2 đều đạt tốt nhất ngay ở epoch ${R.D2.metrics.best_epoch} rồi valid loss tăng: mạng tiền huấn luyện học rất nhanh nhưng cũng quá khớp nhanh trên tập nhỏ.`));
add(P(`ResNet18 (D1) chỉ đạt ${cite(R.D1, "valid_acc")}, thấp hơn CNN tự thiết kế. Lý do có thể là lr 3e-4 còn lớn với toàn bộ mạng đã tiền huấn luyện, và khác biệt miền giữa ảnh màu ImageNet với ảnh xám 48×48 phóng to; giống phần “Fail Cases – Fine-tune With VGG16” của bài mẫu, học chuyển giao không tự động tốt hơn trên FER2013.`));
add(curve("D2"));

// 6. Mô hình cuối
add(H1("6. MÔ HÌNH CUỐI VÀ ĐÁNH GIÁ"));
add(H2("6.1. Chọn mô hình"));
WHERE = "6.1";
add(P([`Quy tắc chọn đặt trước khi xem tập test: mô hình có valid acc (PublicTest) cao nhất trong phiên bản mới nhất của 15 thí nghiệm. run_final.py (Đỗ Minh Thương chạy lúc ${F.evaluated_at.slice(11, 16)} ngày ${F.evaluated_at.slice(8, 10)}/${F.evaluated_at.slice(5, 7)}/${F.evaluated_at.slice(0, 4)}) chọn ${F.selected_key} – ${F.description}, nạp lại best.pt và đánh giá trên PrivateTest có và không có TTA (trung bình dự đoán của ảnh gốc và ảnh lật ngang). Kết quả lưu ở `, link("exps/FINAL", F.url), t(".")]));
add(table(["Tập", "Chỉ số", "Không TTA", "Có TTA (lật ngang)"], [
  ["PublicTest (valid)", "Accuracy", cite(F, "valid_acc", { final: true }), cite(F, "valid_acc_tta", { final: true })],
  ["PublicTest (valid)", "Macro-F1", cite(F, "valid_f1", { final: true }), cite(F, "valid_f1_tta", { final: true })],
  ["PrivateTest (test)", "Accuracy", cite(F, "test_acc", { final: true }), cite(F, "test_acc_tta", { final: true })],
  ["PrivateTest (test)", "Macro-F1", cite(F, "test_f1", { final: true }), cite(F, "test_f1_tta", { final: true })],
  ["PrivateTest (test)", "Loss", cite(F, "test_loss", { final: true }), cite(F, "test_loss_tta", { final: true })],
], [2800, 1900, 2400, 2538], `Kết quả mô hình cuối ${F.selected_key}`, { align: [AlignmentType.LEFT, AlignmentType.LEFT, RT, RT] }));
add(P(`Trên PrivateTest, mô hình cuối đạt ${cite(F, "test_acc_tta", { final: true })} với TTA, gần mức 71% tốt nhất của cuộc thi mà đề bài nêu. Đáng lưu ý, B4 (label smoothing) có test acc cao hơn (${cite(R.B4, "test_acc")}) nhưng valid acc thấp hơn D2 ${(100 * (R.D2.metrics.valid_acc - R.B4.metrics.valid_acc)).toFixed(2).replace(".", ",")} điểm; nhóm giữ nguyên lựa chọn D2 theo đúng quy tắc, vì chọn lại theo tập test sẽ làm con số test không còn khách quan.`));
add(H2("6.2. Kết quả theo từng lớp"));
WHERE = "Bảng " + (tabNo + 1);
add(table(["Lớp", "Precision", "Recall", "F1", "Số ảnh test"], cls.map((c) => {
  const x = F.per_class_test[c];
  return [`${c} (${vi[c]})`, dec(x.precision), dec(x.recall), dec(x["f1-score"]), int(x.support)];
}), [3000, 1600, 1600, 1600, 1838], `Precision, recall, F1 từng lớp của ${F.selected_key} trên PrivateTest (không TTA)`, { align: [AlignmentType.LEFT, RT, RT, RT, RT] }));
const cm = F.confusion_test;
const offd = [];
cm.forEach((row, i) => row.forEach((v, j) => { if (i !== j) offd.push([v, cls[i], cls[j]]); }));
offd.sort((a, b) => b[0] - a[0]);
add(P(`Happy dễ nhất (F1 ${dec(F.per_class_test.Happy["f1-score"])}) nhờ nhiều ảnh và đặc trưng miệng cười rõ; Surprise đứng thứ hai. Fear khó nhất (F1 ${dec(F.per_class_test.Fear["f1-score"])}). Ma trận nhầm lẫn cho thấy các cặp nhầm nhiều nhất là ${offd.slice(0, 4).map((o) => `${o[1]} → ${o[2]} (${o[0]} ảnh)`).join(", ")}: phần lớn đổ về hoặc đi ra từ lớp Sad. Buồn, sợ, giận và bình thường đều có miệng khép, khác nhau chủ yếu ở nét mày và mắt, rất khó phân biệt trên ảnh xám 48×48; Surprise ↔ Fear cũng hay nhầm vì cùng mắt mở to. Disgust tuy ít ảnh nhất nhưng recall khá (${dec(F.per_class_test.Disgust.recall)}) nhờ đặc trưng nhăn mũi khá riêng, còn precision thấp hơn vì một số ảnh Angry bị đoán thành Disgust.`));
add(img(F.figures.confusion_test, 13, `Ma trận nhầm lẫn của ${F.selected_key} trên PrivateTest`, F.url));
add(H2("6.3. Ca dự đoán đúng và sai"));
add(img(F.figures.true_cases, 15, "Một số ca dự đoán đúng (PrivateTest)", F.url));
add(img(F.figures.wrong_cases, 15, "Một số ca dự đoán sai (PrivateTest): nhãn thật / nhãn dự đoán", F.url));
add(P("Nhiều ca sai là ảnh bị che (tay, kính), nghiêng mạnh, độ tương phản thấp hoặc có nhãn gốc đáng ngờ; một phần sai số của FER2013 đến từ chính chất lượng nhãn."));
add(H2("6.4. Trực quan hóa bộ lọc tích chập"));
add(P("Theo yêu cầu của đề bài, nhóm trực quan hóa trọng số lớp tích chập đầu tiên và lớp tích chập cuối cùng của mô hình cuối. Ở lớp đầu (64 bộ lọc 3×3) có thể thấy rõ hai kiểu: bộ lọc tâm – xung quanh (điểm sáng giữa nền tối hoặc ngược lại, phát hiện đốm như khóe mắt, lỗ mũi) và bộ lọc biên ngang, dọc, chéo (phát hiện đường viền mắt, miệng, lông mày); bộ lọc lớp cuối không còn dễ diễn giải bằng mắt vì chúng tổ hợp các đặc trưng trừu tượng của lớp trước."));
add(img(F.figures.filters_first_conv, 12, `Bộ lọc lớp tích chập đầu tiên của ${F.selected_key}`, F.url));
add(img(F.figures.filters_last_conv, 12, `Bộ lọc lớp tích chập cuối cùng của ${F.selected_key}`, F.url));
const fm = Object.keys(F.figures).filter((k) => k.startsWith("feature_maps"));
fm.slice(0, 2).forEach((k) => add(img(F.figures[k], 15, `Feature map lớp tích chập cuối – ${k.replace("feature_maps_", "")}`, F.url)));
if (R.A2.figures.filters_last_conv) add(img(R.A2.figures.filters_last_conv, 12, "Bộ lọc lớp tích chập cuối của baseline A2 (để so sánh)", R.A2.url));

// 7. Thảo luận & kết luận
add(H1("7. THẢO LUẬN VÀ KẾT LUẬN"));
WHERE = "7";
add(H2("7.1. Những gì nhóm rút ra"));
add(B([t("Chống quá khớp quan trọng hơn tăng độ sâu. ", { bold: true }), t(`Bỏ tăng cường dữ liệu làm mất ${Math.abs(100 * (R.B1.metrics.valid_acc - base.metrics.valid_acc)).toFixed(2).replace(".", ",")} điểm valid acc, bỏ Dropout mất ${Math.abs(100 * (R.C5.metrics.valid_acc - base.metrics.valid_acc)).toFixed(2).replace(".", ",")} điểm, trong khi mô hình sâu nhất (LARGE) còn kém baseline.`)]));
add(B([t("Hàm kích hoạt: ", { bold: true }), t("ReLU cùng BatchNorm là đủ; Sigmoid làm mạng sâu học chậm rõ rệt (suy giảm gradient).")]));
add(B([t("Label smoothing ", { bold: true }), t("là cải tiến rẻ và hiệu quả nhất: không đổi kiến trúc, không tăng thời gian, cải thiện cả valid lẫn test.")]));
add(B([t("Học chuyển giao ", { bold: true }), t("cho valid acc cao nhất (VGG16-BN) nhưng tốn tài nguyên và quá khớp nhanh; ResNet18 với lr chưa phù hợp còn kém CNN nhỏ.")]));
add(B([t("Valid và test không luôn cùng thứ hạng: ", { bold: true }), t("chênh lệch giữa nhiều thí nghiệm chỉ khoảng 1 điểm, nên cần nhiều seed (hoặc k-fold) để khẳng định chắc chắn; đây là giới hạn của bài vì mỗi thí nghiệm chỉ chạy với seed 42.")]));
add(H2("7.2. Kết luận"));
add(P(`Nhóm đã cài đặt bằng PyTorch bốn CNN của bài mẫu cùng hai mô hình học chuyển giao, thực hiện ${D.runs.length} lần chạy cho 15 thí nghiệm có kiểm soát (mỗi lần đổi một yếu tố) và quản lý toàn bộ bằng thư mục thực nghiệm, nhật ký Google Sheets có lịch sử phiên bản, GitHub và Drive. Mô hình cuối ${F.selected_key} đạt ${cite(F, "test_acc", { final: true })} accuracy trên PrivateTest (${cite(F, "test_acc_tta", { final: true })} với TTA). Hướng phát triển: kết hợp label smoothing với VGG16-BN, đóng băng các lớp đầu khi fine-tune, dùng trọng số lớp hoặc focal loss cho Disgust/Fear, chạy nhiều seed và ghép nhiều mô hình (ensemble).`));

// Phụ lục
add(H1("PHỤ LỤC A. CÁC CON SỐ ĐƯỢC TRÍCH DẪN"));
const citeIdx = cites.length;
add(P([t("Bảng dưới đây là nội dung của report/citations.json (phần báo cáo). Sheet KiemTra trong "), link("nhật ký Google Sheets", L.sheets), t(" lấy lại từng dòng, tra giá trị trong sheet NhatKy theo run_id và đọc metrics.json của thư mục thực nghiệm, rồi đánh dấu ✔ nếu khớp.")]));
const uniq = [];
const seen = new Set();
cites.slice(0, citeIdx).forEach((c) => { const k = c.run_id + c.metric; if (!seen.has(k)) { seen.add(k); uniq.push(c); } });
add(table(["#", "run_id", "Chỉ số", "Giá trị", "Vị trí trong báo cáo"], uniq.map((c, i) => [String(i + 1),
  lnk(c.source === "final" ? `${L.repo}/tree/main/exps/FINAL/${c.run_id}` : `${L.repo}/tree/main/exps/${c.run_id[0]}/${c.run_id}`, c.run_id, 16),
  c.metric, c.metric === "n_params" ? int(c.value) : (c.metric.includes("loss") ? dec(c.value) : pct(c.value)), c.where]),
  [500, 4700, 1300, 1200, 1938], "Các con số được trích dẫn (mỗi cặp run_id – chỉ số một dòng)", { align: [C, AlignmentType.LEFT, AlignmentType.LEFT, RT, AlignmentType.LEFT] }));
add(H1("PHỤ LỤC B. TOÀN BỘ CÁC LẦN CHẠY"));
add(table(["#", "Ngày giờ (VN)", "Người chạy", "Mã", "Bản", "Valid acc", "Test acc", "Thư mục"], D.runs.map((r, i) => {
  const s = r.start.replace("T", " ");
  return [String(i + 1), s.slice(0, 16), r.author, r.key, r.version, pct(r.metrics.valid_acc), pct(r.metrics.test_acc), lnk(r.url, "mở")];
}), [500, 1900, 2100, 700, 700, 1300, 1300, 1138], "Mọi lần chạy chính thức (khớp với sheet NhatKy)", { align: [C, C, AlignmentType.LEFT, C, C, RT, RT, C] }));

// ---------- tài liệu ----------
const doc = new Document({
  creator: "Nhóm 06", title: "BTL02 – Nhận dạng cảm xúc khuôn mặt bằng CNN",
  styles: {
    default: { document: { run: { font: FONT, size: 26 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 32, bold: true, color: "1F4E79" }, paragraph: { spacing: { before: 240, after: 200 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: "2E74B5" }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 26, bold: true, italics: true }, paragraph: { spacing: { before: 160, after: 80 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 567, hanging: 283 } } } }] }] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [t("BTL02 – Nhóm 06 – Trang ", { size: 20 }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })] })] }) },
    children: [...cover, ...body],
  }],
});
Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync(OUT, b);
  fs.writeFileSync(CIT, JSON.stringify(cites, null, 1));
  fs.writeFileSync(OUT + ".heads.json", JSON.stringify(HEADS));
  console.log("OK", OUT, "citations:", cites.length, "figures:", figNo, "tables:", tabNo);
});
