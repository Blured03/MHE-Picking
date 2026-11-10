"""Render the MHE Picking status report as a PNG (same layout as the app's export)."""
import json, sys, base64, pathlib
from playwright.sync_api import sync_playwright

FONT_DIR = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None
TH_MONTHS = ['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.']

def font_face():
    if not FONT_DIR:
        return ''
    css = ''
    for sub in ('thai', 'latin'):
        for w in (400, 700):
            f = FONT_DIR / f'noto-sans-thai-{sub}-{w}-normal.woff2'
            if f.exists():
                b64 = base64.b64encode(f.read_bytes()).decode()
                css += f"@font-face{{font-family:'NST';font-weight:{w};src:url(data:font/woff2;base64,{b64}) format('woff2');}}\n"
    return css

def esc(s):
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def build(data):
    y, m, d = map(int, data['date'].split('-'))
    date_th = f"{d} {TH_MONTHS[m-1]} {y + 543}"
    rows, tot = '', [0, 0, 0]
    for r in data['rows']:
        ready = r['total'] - r['repair']
        tot[0] += r['total']; tot[1] += ready; tot[2] += r['repair']
        rows += (f"<tr><td class='cat'>{esc(r['name'])}</td><td class='n'>{r['total']}</td>"
                 f"<td class='n'>{ready}</td><td class='n'>{r['repair']}</td>"
                 f"<td class='rm'>{esc(r.get('remark') or '-')}</td></tr>")
    rows += (f"<tr class='sum'><td class='cat'>รวมทั้งหมด</td><td class='n'>{tot[0]}</td>"
             f"<td class='n'>{tot[1]}</td><td class='n'>{tot[2]}</td><td></td></tr>")
    units = ''
    for u in data.get('units', []):
        chips = ''.join(f"<span class='chip {'bad' if str(n) in map(str, u.get('repair', [])) else ''}'>{esc(n)}</span>"
                        for n in u['numbers'])
        units += f"<h2>สถานะรายเบอร์ — {esc(u['name'])}</h2><div class='chips'>{chips}</div>"
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>
{font_face()}
*{{box-sizing:border-box}} body{{margin:0;background:#fff;font-family:'NST','Loma',sans-serif;}}
.card{{width:824px;padding:40px 34px 34px;border:1px solid #e3e7ee;border-radius:22px;background:#fff}}
h1{{margin:0;text-align:center;color:#17407a;font-size:29px;font-weight:700}}
.sub{{text-align:center;color:#7a828f;font-size:21px;margin:6px 0 26px}}
table{{width:100%;border-collapse:separate;border-spacing:3px;font-size:21px;color:#222}}
th{{background:#eaf1fb;color:#17407a;font-weight:700;padding:18px 8px;text-align:center;line-height:1.25}}
th:first-child{{text-align:left;padding-left:8px}}
td{{background:#fff;padding:16px 8px;outline:1px solid #e3e7ee;vertical-align:middle;line-height:1.35}}
td.n{{text-align:center;width:78px}} td.cat{{width:240px}}
td.rm{{color:#d9372b;font-size:20px}}
tr.sum td{{background:#f2f4f7;font-weight:700}}
h2{{margin:30px 0 14px;padding-left:14px;border-left:5px solid #1f5fae;color:#17407a;font-size:22px;font-weight:700}}
.chips{{display:flex;flex-wrap:wrap;gap:10px}}
.chip{{min-width:40px;padding:6px 10px;border-radius:10px;background:#e3f5e8;color:#1e8a3c;font-weight:700;font-size:19px;text-align:center}}
.chip.bad{{background:#fde4e2;color:#c62828}}
.foot{{text-align:center;color:#7a828f;font-size:18px;margin-top:36px}}
</style></head><body><div class='card' id='card'>
<h1>รายงานสถานะเครื่อง MHE แผนก Picking</h1>
<div class='sub'>ข้อมูล ณ วันที่ {date_th}</div>
<table><tr><th>Category</th><th>ทั้งหมด</th><th>พร้อม<br>ใช้</th><th>ซ่อม</th><th>เบอร์ที่ชำรุด / หมายเหตุ</th></tr>{rows}</table>
{units}
<div class='foot'>สร้างโดยระบบบันทึกสถานะเครื่อง MHE Picking</div>
</div></body></html>"""

if __name__ == '__main__':
    data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
    html = build(data)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 860, 'height': 800}, device_scale_factor=2)
        pg.set_content(html)
        pg.wait_for_timeout(300)
        pg.locator('#card').screenshot(path=sys.argv[2])
        b.close()
