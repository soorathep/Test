const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, HeadingLevel
} = require('docx');
const fs = require('fs');

const PRUSSIAN = "0E3B5C", SODIUM = "E8A80B", LINE = "D8D6D1", SOFT = "6B7B8C";
const W = 9360;                    // usable width on A4 with 1" margins, in DXA
const COL = [2900, 6460];

const cell = (children, opts = {}) => new TableCell({
  width: { size: opts.w || COL[0], type: WidthType.DXA },
  shading: opts.shade ? { type: ShadingType.CLEAR, fill: opts.shade, color: "auto" } : undefined,
  margins: { top: 90, bottom: 90, left: 120, right: 120 },
  children
});

const label = (en, th) => cell([
  new Paragraph({ children: [new TextRun({ text: en, bold: true, size: 19, font: "Calibri" })] }),
  new Paragraph({ children: [new TextRun({ text: th, size: 17, color: SOFT, font: "Calibri" })] })
], { shade: "F4F3F0" });

const answer = (hint) => cell([
  new Paragraph({ children: [new TextRun({ text: "", size: 21, font: "Calibri" })] }),
  ...(hint ? [new Paragraph({ children: [new TextRun({ text: hint, size: 16, italics: true, color: SOFT, font: "Calibri" })] })] : [])
], { w: COL[1] });

const row = (en, th, hint) => new TableRow({ children: [label(en, th), answer(hint)] });

const rule = () => new Paragraph({
  spacing: { before: 60, after: 200 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: LINE } },
  children: [new TextRun({ text: "" })]
});

const doc = new Document({
  sections: [{
    properties: { page: { margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
    children: [
      new Paragraph({
        spacing: { after: 40 },
        children: [new TextRun({ text: "SKH RESEARCH GROUP", bold: true, size: 17, color: SODIUM, font: "Consolas", characterSpacing: 40 })]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun({ text: "Lab member profile", bold: true, size: 40, color: PRUSSIAN, font: "Calibri" })]
      }),
      new Paragraph({
        spacing: { after: 30 },
        children: [new TextRun({ text: "For the group website, skhgroup.net. Takes about five minutes.", size: 19, color: SOFT, font: "Calibri" })]
      }),
      new Paragraph({
        spacing: { after: 160 },
        children: [new TextRun({ text: "สำหรับเว็บไซต์กลุ่มวิจัย ใช้เวลาประมาณ 5 นาที", size: 19, color: SOFT, font: "Calibri" })]
      }),
      rule(),

      new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun({ text: "Fill in the right-hand column. Do not rename the labels on the left.", bold: true, size: 19, font: "Calibri" })]
      }),
      new Paragraph({
        spacing: { after: 200 },
        children: [new TextRun({ text: "กรอกในช่องขวาเท่านั้น อย่าแก้ข้อความในช่องซ้าย ระบบอ่านจากช่องซ้ายเพื่อจับคู่ข้อมูล", size: 18, color: SOFT, font: "Calibri" })]
      }),

      new Table({
        columnWidths: COL,
        width: { size: W, type: WidthType.DXA },
        borders: {
          top: { style: BorderStyle.SINGLE, size: 4, color: LINE },
          bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE },
          left: { style: BorderStyle.SINGLE, size: 4, color: LINE },
          right: { style: BorderStyle.SINGLE, size: 4, color: LINE },
          insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: LINE },
          insideVertical: { style: BorderStyle.SINGLE, size: 4, color: LINE }
        },
        rows: [
          row("Full name", "ชื่อ-นามสกุล (ภาษาอังกฤษ)", "Exactly as it appears on your papers"),
          row("Short name", "ชื่อเล่น / ชื่อที่ให้เรียก", "Optional — what the website calls you day to day"),
          row("Role", "ตำแหน่ง", "PhD student / MEng student / Postdoc / Research assistant / Visiting"),
          row("Year joined", "ปีที่เข้าร่วมกลุ่ม", "e.g. 2024"),
          row("Research, in one sentence", "งานวิจัย 1 ประโยค", "Max 20 words, plain English, no acronyms a first-year would not know"),
          row("Previous degree", "วุฒิก่อนหน้า และสถาบัน", "e.g. MSc Chemistry, Chiang Mai University, 2023"),
          row("ORCID or Google Scholar", "ลิงก์ ORCID หรือ Google Scholar", "Optional — paste the full link")
        ]
      }),

      new Paragraph({ spacing: { before: 320, after: 120 }, children: [new TextRun({ text: "Photo", bold: true, size: 26, color: PRUSSIAN, font: "Calibri" })] }),
      new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Send one photo as a separate file. Do not paste it into this document.", size: 19, font: "Calibri" })] }),
      new Paragraph({ spacing: { after: 140 }, children: [new TextRun({ text: "ส่งรูปเป็นไฟล์แยก อย่าวางรูปลงในไฟล์นี้", size: 18, color: SOFT, font: "Calibri" })] }),

      ...[
        ["Head and shoulders, you looking at the camera.", "ครึ่งตัว มองกล้อง"],
        ["Plain background if you can. A wall is fine.", "ฉากหลังเรียบ ๆ ผนังก็ได้"],
        ["Any recent phone photo is fine. It does not need to be professional.", "รูปจากมือถือได้ ไม่ต้องเป็นรูปสตูดิโอ"],
        ["Name the file with your own name, e.g. somchai_p.jpg", "ตั้งชื่อไฟล์เป็นชื่อตัวเอง เช่น somchai_p.jpg"]
      ].map(([en, th]) => new Paragraph({
        spacing: { after: 80 }, indent: { left: 260 },
        children: [
          new TextRun({ text: "—  ", color: SODIUM, bold: true, size: 19, font: "Calibri" }),
          new TextRun({ text: en, size: 19, font: "Calibri" }),
          new TextRun({ text: "   " + th, size: 17, color: SOFT, font: "Calibri" })
        ]
      })),

      rule(),
      new Paragraph({
        spacing: { before: 120 },
        children: [new TextRun({ text: "Send this file and the photo back to soorathep.k@chula.ac.th", size: 19, bold: true, color: PRUSSIAN, font: "Calibri" })]
      }),
      new Paragraph({
        children: [new TextRun({ text: "Everything here goes on a public website. Send nothing you would not want a stranger to read.", size: 17, italics: true, color: SOFT, font: "Calibri" })]
      }),
      new Paragraph({
        children: [new TextRun({ text: "ข้อมูลทั้งหมดจะขึ้นเว็บสาธารณะ อย่าใส่ข้อมูลที่ไม่อยากให้คนอื่นเห็น เช่น เบอร์โทรส่วนตัว ที่อยู่บ้าน", size: 17, italics: true, color: SOFT, font: "Calibri" })]
      })
    ]
  }]
});

Packer.toBuffer(doc).then(b => { fs.writeFileSync('member_form.docx', b); console.log('member_form.docx written'); });
