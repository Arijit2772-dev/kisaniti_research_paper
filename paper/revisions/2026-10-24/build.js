// Builds the Springer-style (LNCS/LNNS) Word file for the KisanNiti paper.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType, WidthType,
  BorderStyle, TabStopType, Tab, HeadingLevel, VerticalAlign,
} = require("docx");
const { meta, body, refs, declarations } = require("./content_v2r.js");

const OUT = process.argv[2] || "kisaniti_rp_v2.docx";
const FONT = "Times New Roman";
const TEXT_W = 6917;                 // 12.2 cm text width (LNCS)

// ---------------------------------------------------------------- citation numbering by first use
const order = [];
function scan(s) {
  for (const m of (s || "").matchAll(/\[@([^\]]+)\]/g))
    for (const k of m[1].split(",").map((x) => x.trim().replace(/^@/, "")))
      if (!order.includes(k)) {
        if (!refs[k]) throw new Error("Unknown reference key: " + k);
        order.push(k);
      }
}
for (const b of body) {
  scan(b.text); scan(b.caption); scan(b.note);
  if (b.rows) b.rows.forEach((r) => r.forEach(scan));
}
const unused = Object.keys(refs).filter((k) => !order.includes(k));
if (unused.length) throw new Error("Uncited references: " + unused.join(", "));
const num = (k) => order.indexOf(k) + 1;

function citeText(keys) {
  const ns = keys.map(num).sort((a, b) => a - b);
  const parts = [];
  for (let i = 0; i < ns.length; ) {
    let j = i;
    while (j + 1 < ns.length && ns[j + 1] === ns[j] + 1) j++;
    if (j - i >= 2) parts.push(`${ns[i]}–${ns[j]}`);
    else for (let q = i; q <= j; q++) parts.push(String(ns[q]));
    i = j + 1;
  }
  return "[" + parts.join(", ") + "]";
}

// ---------------------------------------------------------------- inline markup
function runs(s, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|_\{[^}]*\}|\^\{[^}]*\}|\[@[^\]]+\])/g;
  let last = 0;
  for (const m of s.matchAll(re)) {
    if (m.index > last) out.push(new TextRun({ text: s.slice(last, m.index), font: FONT, ...base }));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(new TextRun({ text: tok.slice(2, -2), bold: true, font: FONT, ...base }));
    else if (tok.startsWith("*")) out.push(new TextRun({ text: tok.slice(1, -1), italics: true, font: FONT, ...base }));
    else if (tok.startsWith("_{")) out.push(new TextRun({ text: tok.slice(2, -1), subScript: true, font: FONT, ...base }));
    else if (tok.startsWith("^{")) out.push(new TextRun({ text: tok.slice(2, -1), superScript: true, font: FONT, ...base }));
    else out.push(new TextRun({ text: "[" + num(tok.slice(2, -1).trim()) + "]", font: FONT, ...base }));
    last = m.index + tok.length;
  }
  if (last < s.length) out.push(new TextRun({ text: s.slice(last), font: FONT, ...base }));
  return out;
}

const SZ = { body: 20, small: 18, tiny: 16, title: 28, h1: 24 };   // half-points

// ---------------------------------------------------------------- blocks
const children = [];
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: meta.title, bold: true, size: SZ.title, font: FONT })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
  children: [new TextRun({ text: meta.authors.slice(0, -1).join(", ") + ", and " + meta.authors.slice(-1)[0], size: SZ.body, font: FONT })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
  children: [new TextRun({ text: meta.affiliation, size: SZ.small, font: FONT })] }));
meta.emails.forEach((e, i) => children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: i === meta.emails.length - 1 ? 360 : 0 },
  children: [new TextRun({ text: e, size: SZ.small, font: "Courier New" })] })));
children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { left: 567, right: 567 }, spacing: { after: 120 },
  children: [new TextRun({ text: "Abstract. ", bold: true, size: SZ.small, font: FONT }), ...runs(meta.abstract, { size: SZ.small })] }));
children.push(new Paragraph({ alignment: AlignmentType.LEFT, indent: { left: 567, right: 567 }, spacing: { after: 360 },
  children: [new TextRun({ text: "Keywords: ", bold: true, size: SZ.small, font: FONT }), ...runs(meta.keywords, { size: SZ.small })] }));

const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const rule = (sz) => ({ style: BorderStyle.SINGLE, size: sz, color: "000000" });

function makeTable(b) {
  const total = b.widths.reduce((a, c) => a + c, 0);
  const fontSize = b.widths.length > 6 ? SZ.tiny : SZ.tiny;
  const cell = (text, i, isHeader, isLast) => new TableCell({
    width: { size: b.widths[i], type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 30, bottom: 30, left: 60, right: 60 },
    borders: {
      top: isHeader ? rule(8) : noBorder,
      bottom: isHeader ? rule(4) : isLast ? rule(8) : noBorder,
      left: noBorder, right: noBorder,
    },
    children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
      children: isHeader ? [new TextRun({ text, bold: true, size: fontSize, font: FONT })] : runs(text, { size: fontSize }) })],
  });
  const rows = [new TableRow({ tableHeader: true, children: b.header.map((h, i) => cell(h, i, true, false)) })];
  b.rows.forEach((r, ri) => rows.push(new TableRow({ children: r.map((c, i) => cell(c, i, false, ri === b.rows.length - 1)) })));
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: b.widths, alignment: AlignmentType.CENTER,
    borders: { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder, insideHorizontal: noBorder, insideVertical: noBorder },
    rows });
}

for (const b of body) {
  if (b.t === "h1") {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 240 }, keepNext: true,
      children: [new TextRun({ text: b.text, bold: true, size: SZ.h1, font: FONT, color: "000000" })] }));
  } else if (b.t === "h2") {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, keepNext: true,
      children: [new TextRun({ text: b.text, bold: true, size: SZ.body, font: FONT, color: "000000" })] }));
  } else if (b.t === "p") {
    children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { firstLine: b.first ? 0 : 283 },
      children: runs(b.text, { size: SZ.body }) }));
  } else if (b.t === "eq") {
    children.push(new Paragraph({ spacing: { before: 100, after: 100 },
      tabStops: [{ type: TabStopType.CENTER, position: Math.round(TEXT_W / 2) }, { type: TabStopType.RIGHT, position: TEXT_W }],
      children: [new TextRun({ children: [new Tab()], font: FONT }), ...runs(b.text, { size: SZ.body }),
        new TextRun({ children: [new Tab(), `(${b.n})`], size: SZ.body, font: FONT })] }));
  } else if (b.t === "fig") {
    const ext = b.path.toLowerCase().endsWith(".png") ? "png" : "jpg";
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 }, keepNext: true,
      children: [new ImageRun({ type: ext, data: fs.readFileSync(b.path), transformation: { width: b.w, height: b.h } })] }));
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
      children: runs(b.caption, { size: SZ.small }) }));
  } else if (b.t === "table") {
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 100 }, keepNext: true,
      children: runs(b.caption, { size: SZ.small }) }));
    children.push(makeTable(b));
    children.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { before: 60, after: 200 },
      children: b.note ? runs(b.note, { size: SZ.tiny }) : [] }));
  }
}

if (declarations) {
  children.push(new Paragraph({ spacing: { before: 240, after: 120 }, keepNext: true,
    children: [new TextRun({ text: "Declarations", bold: true, size: SZ.h1, font: FONT })] }));
  children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, children: runs(declarations, { size: SZ.body }) }));
}
// ---------------------------------------------------------------- references
children.push(new Paragraph({ spacing: { before: 360, after: 200 }, keepNext: true,
  children: [new TextRun({ text: "References", bold: true, size: SZ.h1, font: FONT, color: "000000" })] }));
order.forEach((k, i) => {
  children.push(new Paragraph({ alignment: AlignmentType.LEFT, indent: { left: 340, hanging: 340 }, spacing: { after: 40 },
    children: [new TextRun({ text: `${i + 1}. `, size: SZ.small, font: FONT }), ...runs(refs[k], { size: SZ.small })] }));
});

const doc = new Document({
  creator: "Arijit Singh, Tushar Garg, Hitesh Mehandiratta, Namya Gautam, Harkiran Kaur",
  title: meta.title,
  styles: { default: { document: { run: { font: FONT, size: SZ.body } } } },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 2948, bottom: 2948, left: 2494, right: 2495 } } },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("wrote", OUT, "refs:", order.length);
  console.log(order.map((k, i) => `${i + 1}:${k}`).join("  "));
});
