"""Check that the Lab 01 browser engine gives the same numbers as pandas (the lab is the students' reference).

Needs Node.js and pandas. Run from anywhere:

    python3 _teaching-src/2105315/labs/tests/engine_vs_pandas.py

For two demo windows and six student IDs it compares: rows, repeated rows, missing CO(GT), mean of valid
CO(GT), share of missing NMHC(GT), sensor-off hours, timestamp gaps, the mean the AI code in Step 4 prints,
missing share by hour of day and daily means.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent


def main():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['node', str(HERE / 'engine_cases.mjs'), tmp], check=True)
        cases = json.loads((pathlib.Path(tmp) / 'facts.json').read_text())
        failed = 0
        for case in cases:
            fa, path = case['facts'], pathlib.Path(tmp) / f"v{case['k']}.csv"
            df = pd.read_csv(path, sep=';', decimal=',', na_values=[-200])
            raw_rows = len(df)
            df = df.loc[:, ~df.columns.str.startswith('Unnamed')].dropna(how='all').drop_duplicates()
            co = df['CO(GT)']
            ts = pd.to_datetime(df.Date + ' ' + df.Time, format='%d/%m/%Y %H.%M.%S')
            ai = pd.read_csv(path, sep=';', decimal=',').drop_duplicates()   # the code shown in Step 4
            daily = co.groupby(ts.dt.date).agg(['count', 'mean'])
            engine_daily = {d['day']: d for d in case['daily']}
            checks = {
                'rows in file': (raw_rows - 2, fa['rowsInFile']),
                'unique rows': (len(df), fa['uniqueRows']),
                'missing CO': (int(co.isna().sum()), fa['coMissing']),
                'mean valid CO': (round(co.mean(), 9), round(fa['coMeanValid'], 9)),
                'mean printed by AI code': (round(ai['CO(GT)'].mean(), 9), round(fa['coMeanNaive'], 9)),
                'NMHC missing share': (round(df['NMHC(GT)'].isna().mean(), 9), round(fa['nmhcShare'], 9)),
                'sensor-off hours': (int(df['PT08.S1(CO)'].isna().sum()), fa['sensorMissing']),
                'gaps': (int((ts.diff().dropna() != pd.Timedelta('1h')).sum()), fa['gaps']),
                'missing by hour': (bool(np.allclose(co.isna().groupby(ts.dt.hour).mean().reindex(range(24)).values, case['hours'])), True),
                'daily means': (len(engine_daily) == len(daily) and all(
                    engine_daily[str(day)]['valid'] == int(r['count']) and (int(r['count']) == 0 or abs(engine_daily[str(day)]['mean'] - r['mean']) < 1e-9)
                    for day, r in daily.iterrows()), True),
            }
            fails = {k: v for k, v in checks.items() if v[0] != v[1]}
            failed += bool(fails)
            print(('ok   ' if not fails else 'FAIL ') + case['label'] + ('' if not fails else f': {fails}'))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
