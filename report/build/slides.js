// Dựng slide BTL02 (.pptx, sau đó tải lên Google Drive chuyển thành Google Slides) từ build/data.json.
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3], CIT = process.argv[4];
const R = D.latest, F = D.final;
const L = {
  repo: D.repo, sheets: "https://docs.google.com/spreadsheets/d/17R3AmpbdE-dxEJrX0fMZhDw2iZWPCG3-ITbCVEo-V0E/edit",
  drive: "https://drive.google.com/drive/folders/16lyivk-DlgbP9q31Oxg2acJtdwTRiyyV",
};
const THEME = { name: "BTL02 FER", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1B2A41", lt1: "FFFFFF", dk2: "324A5F", lt2: "EEF2F6", accent1: "E4572E", accent2: "247BA0",
    accent3: "76B041", accent4: "FFC914", accent5: "8E6C8A", accent6: "17BEBB", hlink: "247BA0", folHlink: "8E6C8A" } };
const HEX = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "BTL02 – Nhận dạng cảm xúc khuôn mặt bằng CNN";
pres.author = "Lê Châu Kỳ, Trần Thanh Huyền, Vũ Hoàng Phương, Đỗ Minh Thương";
const C = pres.SchemeColor;

pres.defineSlideMaster({ title: "TITLE_ONLY", background: { color: C.background1 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.25, w: 9, h: 0.65, fontSize: 22, bold: true,
    color: C.text1, fontFace: THEME.headFontFace, valign: "middle", margin: 0 }, text: "" } },
  { text: { text: "BTL02 · FER2013 – CNN (PyTorch)", options: { x: 0.5, y: 5.25, w: 6, h: 0.25, fontSize: 9, color: C.text2, margin: 0 } } }],
  slideNumber: { x: 9.0, y: 5.22, w: 0.5, h: 0.25, fontSize: 9, color: C.text2, align: "right" } });
pres.defineSlideMaster({ title: "DARK", background: { color: C.text1 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.5, w: 8.8, h: 1.4, fontSize: 36, bold: true,
    color: C.background1, fontFace: THEME.headFontFace, valign: "bottom", margin: 0 }, text: "" } }] });

// ---------- trích dẫn ----------
const cites = [];
let SN = 0;
const pct = (x) => (100 * x).toFixed(2).replace(".", ",") + "%";
const int = (x) => Math.round(x).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
function cite(run, metric, opt = {}) {
  const isF = opt.final, v = isF ? F[metric] : run.metrics[metric];
  cites.push({ doc: "Slide", where: `Slide ${SN}`, text: `${isF ? "FINAL" : run.key} – ${metric}${isF ? " (FINAL)" : ""}`,
    run_id: isF ? F.run_id : run.run_id, metric, value: metric === "n_params" ? v : Math.round(v * 1e4) / 1e4,
    decimals: metric === "n_params" ? 0 : 4, ...(isF ? { source: "final" } : {}) });
  return metric === "n_params" ? int(v) : pct(v);
}
const sizeOf = (p) => { const b = fs.readFileSync(p); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; };
function pic(s, p, x, y, w, h, name) {
  if (!p || !fs.existsSync(p)) return;
  const { w: iw, h: ih } = sizeOf(p);
  const k = Math.min(w / iw, h / ih), ww = iw * k, hh = ih * k;
  s.addImage({ path: p, x: x + (w - ww) / 2, y: y + (h - hh) / 2, w: ww, h: hh, altText: name, objectName: name });
}
function slide(title, sec) { SN++; const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: sec }); s.addText(title, { placeholder: "title" }); return s; }
const txt = (s, items, o) => s.addText(items, { isTextBox: true, fontSize: 14, color: C.text1, valign: "top", paraSpaceAfter: 6, margin: 0.05, ...o });
const bul = (arr) => arr.map((x, i) => ({ text: x, options: { bullet: true, breakLine: i < arr.length - 1 } }));
const link = (text, url, o = {}) => ({ text, options: { hyperlink: { url, tooltip: url }, color: C.accent2, underline: { style: "sng" }, ...o } });
function note(s, n) { s.addNotes(n); }
function footerLinks(s, extra) {
  const items = [link("Nhật ký (Sheets)", L.sheets), { text: "  ·  " }, ...(extra || []), link("exps/ trên GitHub", L.repo + "/tree/main/exps")];
  s.addText(items, { isTextBox: true, x: 5.3, y: 5.22, w: 3.6, h: 0.25, fontSize: 9, color: C.text2, align: "right", margin: 0 });
}
const H = (s) => ({ text: s, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk2 }, align: "center", valign: "middle" } });
function groupSlide(g, title, who, msg, sec) {
  const s = slide(title, sec);
  const keys = Object.keys(R).filter((k) => R[k].group === g).sort();
  const best = Math.max(...keys.map((k) => R[k].metrics.valid_acc));
  const rows = [[H("Mã"), H("Nội dung"), H("Valid acc"), H("Test acc"), H("Test F1"), H("Thư mục")]];
  keys.forEach((k) => {
    const r = R[k], hl = r.metrics.valid_acc === best ? { fill: { color: "E3F1D7" }, bold: true } : {};
    rows.push([{ text: k, options: { align: "center", ...hl } }, { text: r.description, options: hl },
      { text: cite(r, "valid_acc"), options: { align: "right", ...hl } }, { text: cite(r, "test_acc"), options: { align: "right", ...hl } },
      { text: cite(r, "test_f1"), options: { align: "right", ...hl } },
      { text: r.version, options: { align: "center", hyperlink: { url: r.url, tooltip: r.run_id }, color: C.accent2, underline: { style: "sng" }, ...hl } }]);
  });
  s.addTable(rows, { x: 0.5, y: 1.05, w: 5.9, colW: [0.45, 2.55, 0.8, 0.75, 0.7, 0.65], fontSize: 10.5, color: C.text1,
    border: { type: "solid", pt: 0.5, color: "C9D3DD" }, rowH: 0.36, valign: "middle", margin: [2, 4, 2, 4] });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.7, y: 1.05, w: 2.8, h: 3.9, fill: { color: C.background2 }, rectRadius: 0.08, line: { color: C.background2 }, objectName: "msg-card" });
  txt(s, [{ text: who, options: { bold: true, color: C.accent1, fontSize: 12, breakLine: true } }, ...msg.map((m, i) => ({ text: m, options: { bullet: true, breakLine: i < msg.length - 1, fontSize: 12 } }))],
    { x: 6.85, y: 1.15, w: 2.5, h: 3.7 });
  txt(s, "Dòng tô xanh: tốt nhất nhóm theo valid acc (PublicTest). Bấm v1/v2 để mở thư mục thực nghiệm.", { x: 0.5, y: 4.75, w: 5.9, h: 0.35, fontSize: 9.5, color: C.text2, italic: true });
  footerLinks(s);
  return s;
}

// 1. Bìa
SN++;
pres.addSection({ title: "Mở đầu" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Mở đầu" });
s.addText("Nhận dạng cảm xúc khuôn mặt bằng CNN", { placeholder: "title" });
s.addText("BTL02 · Học sâu · FER2013 · PyTorch", { isTextBox: true, x: 0.6, y: 3.0, w: 8.8, h: 0.5, fontSize: 18, color: C.accent4, margin: 0 });
s.addText("Lê Châu Kỳ · Trần Thanh Huyền · Vũ Hoàng Phương · Đỗ Minh Thương\nGV Đỗ Như Tài · Lớp DCT123C4 · Trường Đại học Sài Gòn · 11/2026",
  { isTextBox: true, x: 0.6, y: 3.7, w: 8.8, h: 0.9, fontSize: 13, color: C.background1, margin: 0 });

// 2. Liên kết
s = slide("Bốn sản phẩm liên kết, kiểm tra được với nhau", "Mở đầu");
const cards = [["Nhật ký – Google Sheets", "Mỗi lần chạy một dòng; lịch sử phiên bản ghi ai cập nhật, lúc nào; sheet KiemTra đối chiếu số liệu.", L.sheets, C.accent1],
  ["Báo cáo – Word (.docx)", "Mọi bảng số liệu kèm run_id và liên kết tới thư mục thực nghiệm; phụ lục A là danh sách trích dẫn.", L.drive.replace("16lyivk-DlgbP9q31Oxg2acJtdwTRiyyV", "1rz0GDl1D-OAW24Wup3akU4sQ2PE_nhY1"), C.accent2],
  ["Mã nguồn + exps – GitHub", "config.json, meta.json, history.csv, metrics.json, hình của từng lần chạy.", L.repo, C.accent3],
  ["Trọng số – Google Drive", "exps/ đầy đủ kèm checkpoints/best.pt.", L.drive, C.accent5]];
cards.forEach((c, i) => {
  const x = 0.5 + (i % 2) * 4.6, y = 1.1 + Math.floor(i / 2) * 1.75;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.4, h: 1.55, fill: { color: C.background2 }, line: { color: C.background2 }, rectRadius: 0.08, objectName: `card-${i}` });
  s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.25, w: 0.42, h: 0.42, fill: { color: c[3] }, line: { color: c[3] }, objectName: `dot-${i}` });
  s.addText(String(i + 1), { isTextBox: true, x: x + 0.2, y: y + 0.25, w: 0.42, h: 0.42, align: "center", valign: "middle", fontSize: 14, bold: true, color: C.background1, margin: 0 });
  txt(s, [link(c[0], c[2], { bold: true, fontSize: 14, breakLine: true }), { text: c[1], options: { fontSize: 11.5, color: C.text2 } }], { x: x + 0.8, y: y + 0.18, w: 3.45, h: 1.3 });
});
txt(s, [{ text: "Lần ngược một con số: ", options: { bold: true } }, { text: "slide/báo cáo → run_id → dòng trong NhatKy → thư mục exps/<nhóm>/<run_id>/metrics.json" }],
  { x: 0.5, y: 4.65, w: 9, h: 0.4, fontSize: 12 });
note(s, "Giới thiệu bốn sản phẩm và cách kiểm tra: mọi số trên slide đều có run_id, sheet KiemTra tự so sánh với nhật ký và metrics.json.");

// 3. Phân công
s = slide("Phân công: mỗi người một phần code, một nhóm thực nghiệm", "Mở đầu");
const mem = [["Lê Châu Kỳ", "3123411173", "Dữ liệu, tăng cường, quản lý thực nghiệm, Sheets", "B"],
  ["Trần Thanh Huyền", "3123411126", "Kiến trúc CNN (models.py)", "A"], ["Vũ Hoàng Phương", "3123411238", "Vòng lặp huấn luyện (train.py)", "C"],
  ["Đỗ Minh Thương", "3123411294", "Đánh giá, trực quan hóa, mô hình cuối", "D + FINAL"]];
s.addTable([[H("Thành viên"), H("MSSV"), H("Phần code"), H("Nhóm TN"), H("Số lần chạy")],
  ...mem.map((m) => [m[0], m[1], m[2], { text: m[3], options: { align: "center" } }, { text: String(D.runs.filter((r) => r.author === m[0]).length), options: { align: "center" } }])],
  { x: 0.5, y: 1.1, w: 9, colW: [1.9, 1.2, 3.8, 1.05, 1.05], fontSize: 12, color: C.text1, border: { type: "solid", pt: 0.5, color: "C9D3DD" }, rowH: 0.45, valign: "middle" });
txt(s, [{ text: "Mỗi người tự chạy nhóm của mình trên Colab bằng tài khoản Google riêng → nhật ký ghi đúng người chạy, lịch sử phiên bản Sheets ghi đúng người cập nhật. Ma trận RACI đầy đủ: sheet " }, link("PhanCong", L.sheets), { text: ". Đóng góp: mỗi thành viên 25%." }],
  { x: 0.5, y: 3.6, w: 9, h: 0.9, fontSize: 13 });
footerLinks(s);

// 4. Dữ liệu
pres.addSection({ title: "Dữ liệu và mô hình" });
s = slide("FER2013: 35.887 ảnh xám 48×48, 7 lớp, mất cân bằng mạnh", "Dữ liệu và mô hình");
const st = D.stats;
pic(s, D.datafig.histogram_data, 0.4, 1.0, 5.6, 4.1, "histogram");
[[int(st.train.n), "Training – để học"], [int(st.valid.n), "PublicTest – valid, chọn mô hình"], ["3.589", "PrivateTest – test, chỉ báo cáo"]].forEach((k, i) => {
  txt(s, [{ text: k[0], options: { fontSize: 26, bold: true, color: C.accent2, breakLine: true } }, { text: k[1], options: { fontSize: 11, color: C.text2 } }], { x: 6.3, y: 1.0 + i * 0.95, w: 3.2, h: 0.9 });
});
txt(s, `Happy ${pct(st.train.ratio.Happy)}, Disgust chỉ ${pct(st.train.ratio.Disgust)} → báo cáo thêm macro-F1.`, { x: 6.3, y: 3.95, w: 3.2, h: 0.8, fontSize: 12 });
footerLinks(s);

// 5. Tăng cường + huấn luyện
s = slide("Tăng cường dữ liệu trên GPU và quy trình huấn luyện", "Dữ liệu và mô hình");
pic(s, D.datafig.augmentation, 0.4, 1.0, 4.9, 4.0, "augmentation");
txt(s, bul(["Chuẩn: xoay ±10°, dịch/zoom ±10%, lật ngang", "Mạnh (B2): ±20°, ±15%, xóa ngẫu nhiên", "Adam lr 0,001, batch 128, tối đa 60 epoch",
  "Dừng sớm sau 10 epoch valid loss không giảm; giảm lr ×0,5 sau 4 epoch", "Lưu best.pt theo valid loss; AMP trên Tesla T4; seed 42"]), { x: 5.6, y: 1.05, w: 3.9, h: 3.9, fontSize: 13.5 });
footerLinks(s);

// 6. Kiến trúc
s = slide("Bốn CNN của bài mẫu và hai mô hình học chuyển giao", "Dữ liệu và mô hình");
const arch = [["SMALL", "A1", "[64,64] · [128,128,256,256] · FC1024", R.A1], ["MEDIUM (baseline)", "A2", "[64×2] · [128×3] · [256×3] · FC1024", R.A2],
  ["MEDIUM_01", "A3", "[64×3] · [128×4] · [256×4] · FC1024", R.A3], ["LARGE", "A4", "[64×4] · [128×4] · [256×4] · [512×4] · FC2048", R.A4],
  ["ResNet18 ImageNet", "D1", "ảnh 96×96, fine-tune toàn mạng", R.D1], ["VGG16-BN ImageNet", "D2", "ảnh 96×96, FC512", R.D2]];
s.addTable([[H("Mô hình"), H("Mã"), H("Cấu trúc"), H("Số tham số")], ...arch.map((a) => [a[0], { text: a[1], options: { align: "center" } }, a[2], { text: cite(a[3], "n_params"), options: { align: "right" } }])],
  { x: 0.5, y: 1.05, w: 9, colW: [2.0, 0.6, 4.6, 1.8], fontSize: 12, color: C.text1, border: { type: "solid", pt: 0.5, color: "C9D3DD" }, rowH: 0.42, valign: "middle" });
txt(s, "Mỗi khối: [Conv3×3 → BatchNorm → ReLU] × n → MaxPool → Dropout 0,2; đầu ra FC → BN → ReLU → Dropout 0,5 → 7 lớp. SMALL nhiều tham số nhất vì chỉ 2 lần pooling (FC nhận 12×12×256).",
  { x: 0.5, y: 4.15, w: 9, h: 0.8, fontSize: 12, color: C.text2 });
footerLinks(s);

// 7. Tổng quan 15 thí nghiệm
pres.addSection({ title: "Thực nghiệm" });
s = slide("15 thí nghiệm, mỗi thí nghiệm đổi một yếu tố so với baseline", "Thực nghiệm");
const ks = Object.keys(R).sort((a, b) => R[b].metrics.valid_acc - R[a].metrics.valid_acc);
ks.forEach((k) => cite(R[k], "valid_acc"));
pic(s, process.env.CHART_DIR + "/chart_all.png", 0.4, 1.0, 6.5, 4.15, "chart-all");
txt(s, [{ text: "Sắp theo valid acc (PublicTest)", options: { bold: true, breakLine: true } },
  ...bul([`Cao nhất: D2 VGG16-BN ${pct(R.D2.metrics.valid_acc)}`, `Baseline A2: ${pct(R.A2.metrics.valid_acc)}`, `Thấp nhất: B1 bỏ tăng cường ${pct(R.B1.metrics.valid_acc)}`,
    "Phần lớn chênh lệch chỉ 1–2 điểm; tăng cường dữ liệu, Dropout và hàm kích hoạt tạo khác biệt lớn nhất"])], { x: 7.0, y: 1.1, w: 2.6, h: 3.9, fontSize: 12 });
footerLinks(s);
note(s, "Biểu đồ: valid và test acc của phiên bản mới nhất mỗi thí nghiệm, số liệu từ exps/*/metrics.json (khớp sheet TongHop).");

groupSlide("A", "Nhóm A – Kiến trúc: sâu hơn không tốt hơn", "Trần Thanh Huyền", [
  `MEDIUM (A2) tốt nhất trên valid: ${pct(R.A2.metrics.valid_acc)}`,
  `LARGE gấp ${(R.A4.metrics.n_params / R.A2.metrics.n_params).toFixed(1).replace(".", ",")} lần tham số, chậm hơn ${(R.A4.metrics.train_time_s / R.A2.metrics.train_time_s).toFixed(1).replace(".", ",")} lần, kém hơn`,
  "SMALL kém trên valid nhưng cao nhất trên test → khác biệt ~1–2 điểm gần dao động ngẫu nhiên"], "Thực nghiệm");
groupSlide("B", "Nhóm B – Tăng cường dữ liệu quan trọng nhất, label smoothing tốt nhất", "Lê Châu Kỳ", [
  `Bỏ tăng cường: −${(100 * (R.A2.metrics.valid_acc - R.B1.metrics.valid_acc)).toFixed(2).replace(".", ",")} điểm, quá khớp từ epoch ${R.B1.metrics.best_epoch}`,
  `Label smoothing 0,1: vượt baseline, test acc cao nhất ${pct(R.B4.metrics.test_acc)}`,
  "Chạy lại cả nhóm (v2): kết quả trùng khớp v1 → tái lập được"], "Thực nghiệm");
groupSlide("C", "Nhóm C – ReLU + BatchNorm + Dropout là đủ", "Vũ Hoàng Phương", [
  `Sigmoid: ${pct(R.C1.metrics.valid_acc)}, vẫn đang học ở epoch ${R.C1.metrics.best_epoch} (suy giảm gradient)`,
  `Bỏ BatchNorm: cần ${R.C4.metrics.best_epoch} epoch thay vì ${R.A2.metrics.best_epoch}`,
  `Bỏ Dropout: quá khớp sớm (epoch ${R.C5.metrics.best_epoch}), khoảng cách train–valid ${(100 * (R.C5.metrics.train_acc_at_best - R.C5.metrics.valid_acc)).toFixed(1).replace(".", ",")} điểm`], "Thực nghiệm");
groupSlide("D", "Nhóm D – Học chuyển giao: VGG16-BN cao nhất, ResNet18 thất bại", "Đỗ Minh Thương", [
  `VGG16-BN: valid ${pct(R.D2.metrics.valid_acc)}, cao nhất toàn bộ`,
  `Cả hai tốt nhất ngay epoch ${R.D2.metrics.best_epoch} rồi quá khớp`,
  "ResNet18 lr 3e-4 kém CNN nhỏ: khác biệt miền ảnh màu ImageNet ↔ ảnh xám 48×48"], "Thực nghiệm");

// 12. Mô hình cuối
pres.addSection({ title: "Mô hình cuối" });
s = slide(`Mô hình cuối: ${F.selected_key} – VGG16-BN, chọn theo valid acc`, "Mô hình cuối");
[[cite(F, "valid_acc", { final: true }), "Valid acc (PublicTest)"], [cite(F, "test_acc", { final: true }), "Test acc (PrivateTest)"],
  [cite(F, "test_acc_tta", { final: true }), "Test acc + TTA lật ngang"], [cite(F, "test_f1_tta", { final: true }), "Test macro-F1 + TTA"]].forEach((k, i) => {
  const x = 0.5 + i * 2.3;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.1, w: 2.1, h: 1.6, fill: { color: i === 2 ? C.text1 : C.background2 }, line: { color: i === 2 ? C.text1 : C.background2 }, rectRadius: 0.08, objectName: `stat-${i}` });
  txt(s, [{ text: k[0], options: { fontSize: 28, bold: true, color: i === 2 ? C.accent4 : C.accent2, breakLine: true } }, { text: k[1], options: { fontSize: 11, color: i === 2 ? C.background1 : C.text2 } }],
    { x: x + 0.1, y: 1.25, w: 1.9, h: 1.35, align: "center", valign: "middle" });
});
txt(s, bul(["Quy tắc đặt trước: valid acc cao nhất trong 15 thí nghiệm (không nhìn tập test)",
  `B4 có test acc cao hơn (${pct(R.B4.metrics.test_acc)}) nhưng valid thấp hơn → vẫn giữ D2 để con số test khách quan`,
  "Mức tốt nhất của cuộc thi theo đề bài: ~69% PublicTest, ~71% PrivateTest"]), { x: 0.5, y: 3.0, w: 9, h: 1.6, fontSize: 13.5 });
s.addText([link("Mở exps/FINAL", F.url)], { isTextBox: true, x: 0.5, y: 4.65, w: 3, h: 0.3, fontSize: 11, margin: 0 });
footerLinks(s);

// 13. Theo lớp
s = slide("Happy dễ nhất, Fear khó nhất; Sad bị nhầm nhiều nhất", "Mô hình cuối");
const cls = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"];
pic(s, process.env.CHART_DIR + "/chart_f1.png", 0.4, 1.0, 4.6, 4.1, "chart-f1");
pic(s, F.figures.confusion_test, 5.2, 1.0, 4.4, 4.1, "confusion");
footerLinks(s);

// 14. Ca đúng sai
s = slide("Ca đúng và ca sai trên PrivateTest", "Mô hình cuối");
pic(s, F.figures.true_cases, 0.4, 1.0, 4.5, 3.7, "true-cases");
pic(s, F.figures.wrong_cases, 5.1, 1.0, 4.5, 3.7, "wrong-cases");
txt(s, "Ca sai thường do che mặt, nghiêng mạnh, tương phản thấp hoặc nhãn gốc nhập nhằng (Fear/Surprise, Sad/Neutral).", { x: 0.5, y: 4.72, w: 9, h: 0.4, fontSize: 11.5, color: C.text2 });
footerLinks(s);

// 15. Bộ lọc
s = slide("Trực quan hóa bộ lọc lớp tích chập đầu và cuối", "Mô hình cuối");
pic(s, F.figures.filters_first_conv, 0.4, 1.0, 4.5, 3.4, "filters-first");
pic(s, F.figures.filters_last_conv, 5.1, 1.0, 4.5, 3.4, "filters-last");
txt(s, [{ text: "Lớp đầu: ", options: { bold: true } }, { text: "bộ lọc tâm – xung quanh (đốm sáng/tối) và bộ lọc biên ngang, dọc, chéo. " }, { text: "Lớp cuối: ", options: { bold: true } }, { text: "tổ hợp đặc trưng trừu tượng, khó diễn giải bằng mắt." }],
  { x: 0.5, y: 4.5, w: 9, h: 0.6, fontSize: 12.5 });
footerLinks(s);

// 16. Kết luận
pres.addSection({ title: "Kết luận" });
s = slide("Kết luận", "Kết luận");
const concl = [["Chống quá khớp > độ sâu", "Tăng cường dữ liệu và Dropout quan trọng hơn thêm lớp"], ["Label smoothing", "Cải tiến rẻ nhất, tốt cả valid lẫn test"],
  ["Học chuyển giao", "VGG16-BN cao nhất nhưng tốn tài nguyên, quá khớp nhanh"], ["Quản lý thực nghiệm", `${D.runs.length} lần chạy, có phiên bản, tái lập được, đối chiếu tự động`]];
concl.forEach((c, i) => {
  const x = 0.5 + (i % 2) * 4.6, y = 1.1 + Math.floor(i / 2) * 1.55;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.4, h: 1.35, fill: { color: C.background2 }, line: { color: C.background2 }, rectRadius: 0.08, objectName: `concl-${i}` });
  txt(s, [{ text: c[0], options: { bold: true, fontSize: 15, color: C.accent1, breakLine: true } }, { text: c[1], options: { fontSize: 12.5 } }], { x: x + 0.2, y: y + 0.15, w: 4.0, h: 1.1 });
});
txt(s, "Hướng tiếp: VGG16-BN + label smoothing, đóng băng lớp đầu, focal loss cho Disgust/Fear, nhiều seed, ensemble.", { x: 0.5, y: 4.3, w: 9, h: 0.5, fontSize: 12.5, color: C.text2 });
footerLinks(s);

SN++;
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Kết luận" });
s.addText("Cảm ơn thầy và các bạn", { placeholder: "title" });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 3.05, w: 6.2, h: 0.6, fill: { color: C.background1 }, line: { color: C.background1 }, rectRadius: 0.1, objectName: "links-pill" });
s.addText([link("Nhật ký Google Sheets", L.sheets), { text: "   ·   ", options: { color: C.text1 } }, link("GitHub", L.repo),
  { text: "   ·   ", options: { color: C.text1 } }, link("Google Drive", L.drive)], { isTextBox: true, x: 0.8, y: 3.1, w: 6.0, h: 0.5, fontSize: 16, margin: 0, valign: "middle" });

pres.writeFile({ fileName: OUT }).then(async () => {
  await applyTheme(OUT, THEME);
  fs.writeFileSync(CIT, JSON.stringify(cites, null, 1));
  console.log("OK", OUT, "slides:", SN, "citations:", cites.length);
});
