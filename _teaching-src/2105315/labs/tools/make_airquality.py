"""Build assets/data/airquality.json from the UCI Air Quality file (reproducible, offline after download).

    curl -L -o /tmp/aq.zip https://archive.ics.uci.edu/static/public/360/air+quality.zip
    unzip -o /tmp/aq.zip -d /tmp/aq
    python3 _teaching-src/2105315/labs/tools/make_airquality.py /tmp/aq/AirQualityUCI.csv

Source: De Vito S. (2008). Air Quality [Dataset]. UCI Machine Learning Repository.
https://doi.org/10.24432/C59K5F (CC BY 4.0). Introductory paper: De Vito et al., Sensors and
Actuators B 129 (2008) 750-757, https://doi.org/10.1016/j.snb.2007.09.060.

The values are kept as the exact text of the source file (decimal comma, -200 missing code,
"-200,0" in C6H6(GT)), so the page can rebuild a file that reads like the original export.
The source is hourly with no gaps; the script stops if that ever changes.
"""
import csv
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timedelta

SHA256 = '13277ae5d8581e80b7be09d47c7d3d06fe9b8e957078f2cf6e859f955e62f996'
KEEP = ['CO(GT)', 'PT08.S1(CO)', 'NMHC(GT)', 'C6H6(GT)', 'NOx(GT)', 'NO2(GT)', 'T', 'RH']
UNITS = {'CO(GT)': 'mg/m³', 'PT08.S1(CO)': 'sensor response', 'NMHC(GT)': 'µg/m³', 'C6H6(GT)': 'µg/m³',
         'NOx(GT)': 'ppb', 'NO2(GT)': 'µg/m³', 'T': '°C', 'RH': '%'}


def main(path):
    raw = pathlib.Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise SystemExit('AirQualityUCI.csv does not match the expected UCI file (sha256).')
    rows = [r for r in csv.reader(raw.decode('latin-1').splitlines(), delimiter=';') if any(c.strip() for c in r)]
    header, body = rows[0], rows[1:]
    idx = {name: header.index(name) for name in ['Date', 'Time', *KEEP]}
    stamps = [datetime.strptime(r[idx['Date']] + ' ' + r[idx['Time']], '%d/%m/%Y %H.%M.%S') for r in body]
    for a, b in zip(stamps, stamps[1:]):
        if b - a != timedelta(hours=1):
            raise SystemExit(f'Gap or repeat in the source at {a}.')
    out = {
        'source': {
            'title': 'Air Quality (UCI Machine Learning Repository)',
            'creator': 'Saverio De Vito',
            'doi': '10.24432/C59K5F',
            'license': 'CC BY 4.0',
            'paper': 'De Vito S., Massera E., Piga M., Martinotto L., Di Francia G. (2008). On field calibration of an electronic nose for benzene estimation in an urban pollution monitoring scenario. Sensors and Actuators B: Chemical 129, 750-757.',
            'paperDoi': '10.1016/j.snb.2007.09.060',
            'site': 'Multisensor device at road level in a significantly polluted area of an Italian city; reference analyzer values are the (GT) columns.',
            'sha256': SHA256,
        },
        'start': stamps[0].strftime('%Y-%m-%dT%H:%M'),
        'hours': len(body),
        'columns': KEEP,
        'units': UNITS,
        'text': {name: [r[idx[name]] for r in body] for name in KEEP},
    }
    target = pathlib.Path(__file__).resolve().parents[1] / 'assets/data/airquality.json'
    target.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
    print(target, len(body), 'hours', target.stat().st_size, 'bytes')


if __name__ == '__main__':
    main(sys.argv[1])
