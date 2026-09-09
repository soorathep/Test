# MMS3 - Worked Worksheets A, B and C: Battery Recycling

ตัวอย่างกรอกแล้วภาษาไทย 5 หน้า อ้างอิง Eeamtak et al., Green Chemistry (2026), DOI: 10.1039/d6gc03171d

- หน้า 1: Worksheet A - prior-review comparison และ review gap
- หน้า 2: Worksheet B - one-page proposal; แผนเวลาและวิธีทำงานระบุเป็นสมมติเพื่อการสอน
- หน้า 3: Worksheet C - evidence matrix 5 แถวเงื่อนไขจาก 4 งาน โดยสกัดผ่าน Table 3 ใน review
- หน้า 4: Worksheet C - boundary, pattern, research-gap และ review-novelty statements
- หน้า 5: แนวทางเฉลยและแหล่งอ้างอิง

กรณีศึกษานี้ถอดเหตุผลย้อนหลังจากบทความที่ตีพิมพ์แล้ว ไม่อ้างว่าเป็น review ใหม่หรือการค้นวรรณกรรมครบทั้งสาขา

## Render

เก็บไฟล์ QMD กับ worksheet.css ไว้ด้วยกัน (ฟอนต์ฝังใน CSS แล้ว)

```sh
quarto render MMS3_Battery_Recycling_Worked_Worksheets.qmd --to html
```

PDF สร้างจาก HTML ที่ Quarto แปลงแล้ว พิมพ์บน A4 เปิด background graphics ไม่ใส่ browser headers/footers และใช้ขนาดหน้าตาม CSS
