# MMS3 — Beyond the Summary

ฉบับปรับปรุงสำหรับการบรรยายวันที่ 9 กันยายน 2026

หน้าปกใช้ชื่อ Soorathep Kheawhom, PhD, FRSC พร้อมสังกัดตามบทความที่ให้มา จัดชื่อเรื่องสองบรรทัดและกราฟิก Evidence → Synthesis → Research gaps / Review novelty ในโทน teal–amber

## ไฟล์พร้อมใช้

- `Beyond_the_Summary_Updated.pdf` — สไลด์ 50 หน้า
- `Beyond_the_Summary_Updated.html` — สไลด์สำหรับนำเสนอในเบราว์เซอร์ ฝังฟอนต์และรูปไว้แล้ว
- `Beyond_the_Summary_Updated.qmd` — ต้นฉบับ Quarto พร้อมบันทึกผู้บรรยายภาษาไทย
- `Beyond_the_Summary_TH_Script_Updated.pdf` — บทบรรยายภาษาไทย 29 หน้า ครบ 50 สไลด์ เป็นประโยคพร้อมพูด มีจังหวะกำกับ เวลา และคำตอบสำรอง
- `Beyond_the_Summary_TH_Script_Updated.qmd` — ต้นฉบับ Quarto ของบทบรรยายภาษาไทย
- `Beyond_the_Summary_TH_Script_Updated.html` — บทบรรยายสำหรับเปิดอ่านในเบราว์เซอร์
- `Beyond_the_Summary_Handout_Updated.pdf` — เอกสารประกอบ 14 หน้า พร้อมส่วนเสริมและตัวอย่างจากบทความจริง

เวลาที่เตรียมไว้: บรรยายและกิจกรรมระหว่างเรื่อง 92 นาที + เขียน proposal 8 นาที + ถามตอบ 20 นาที รวม 120 นาที

## ประเด็นที่เพิ่ม

PRISMA และการบันทึกเส้นทางการค้น/คัดเลือก → evidence matrix และการประเมินหลักฐาน → research gaps → contribution และ novelty ของ review paper โดยแยก research gap, review gap และ novelty ให้ชัดเจน

สไลด์ 39 ใช้บทความ Journal of Power Sources เป็นตัวอย่าง evidence audit และการใช้เกณฑ์ evidence tiers เฉพาะบทความ ส่วนสไลด์ 40 ใช้บทความ Green Chemistry เป็นตัวอย่าง conceptual framework และการสังเคราะห์ข้ามงาน ทั้งสองกรณีใช้เพื่ออธิบาย gap และ novelty; ตัวอย่าง PRISMA อยู่แยกต่างหาก

สไลด์ 50 ใช้สีแยกแหล่งอ่านต่อทั้ง 8 กลุ่ม พร้อม legend และหมายเลขที่ตรงกัน เพื่อบอกว่าแต่ละกลุ่มช่วยตอบคำถามหรือนำไปทำอะไรต่อ

บทบรรยายไทยฉบับพร้อมพูดถูกใส่ไว้ใน speaker notes ของสไลด์ Quarto/HTML ด้วย คำกำกับในวงเล็บเหลี่ยมใช้บอกจังหวะชี้ภาพ เว้นจังหวะ หรือทำกิจกรรม ส่วนคำตอบสำรอง 7 ข้อท้ายเอกสารเลือกใช้ตามคำถาม

ตัวเลข PRISMA และ evidence matrix A–D เป็นข้อมูลสมมติสำหรับการสอน ส่วนกรณีศึกษาบทความจริงมีแหล่งอ้างอิงกำกับ ไม่ควรขยายข้อสรุปจากชุดที่ตรวจไปเป็นข้อสรุปของทั้งสาขา

## แก้ไขต้นฉบับ

เก็บไฟล์ `.qmd`, โฟลเดอร์ `theme` และโฟลเดอร์ `assets` ไว้ด้วยกัน ต้นฉบับนี้ตรวจด้วย Quarto 1.10.18

สร้าง HTML ใหม่จากโฟลเดอร์นี้:

```sh
quarto render Beyond_the_Summary_Updated.qmd --to revealjs
```

PDF ที่ให้มาสร้างจาก HTML ที่ Quarto แปลงแล้ว โดยใช้โหมด `?print-pdf` ของ Reveal.js และพิมพ์ผ่าน Chrome พร้อมสีพื้นหลัง ไม่แสดงหัวกระดาษและท้ายกระดาษของเบราว์เซอร์

สร้าง HTML ของบทบรรยายใหม่:

```sh
quarto render Beyond_the_Summary_TH_Script_Updated.qmd --to html
```

PDF บทบรรยายใช้หน้ากระดาษ A4 พร้อมเลขหน้าและสีพื้นหลัง เมื่อแก้เนื้อหา ให้ปรับบทพูดในต้นฉบับบทบรรยายและ speaker notes ของสไลด์ให้ตรงกัน ส่วน handout เป็นเอกสารประกอบที่จัดหน้าแยกไว้

## Worked worksheets - added 9 September 2026

`worksheets/MMS3_Battery_Recycling_Worked_Worksheets.pdf` provides five completed Thai example pages on battery recycling: A on page 1, B on page 2, C on pages 3-4, and facilitation notes/references on page 5. Quarto, HTML and the embedded-font stylesheet are included alongside the PDF. This is a retrospective teaching example based on the published Green Chemistry paper, with illustrative proposal planning clearly labeled.
