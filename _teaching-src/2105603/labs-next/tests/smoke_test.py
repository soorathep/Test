"""Browser smoke test for the 2105603 2027 lab preview.

Run from the repository root after `python3 _teaching-src/2105603/labs-next/build.py`:

    pip install playwright && python3 -m playwright install chromium
    python3 _teaching-src/2105603/labs-next/tests/smoke_test.py

The checks live in the shared kit: _teaching-src/shared/labs-kit/tests/smoke_test.py.
"""
import importlib.util
import pathlib

_path = pathlib.Path(__file__).resolve().parents[3] / 'shared/labs-kit/tests/smoke_test.py'
_spec = importlib.util.spec_from_file_location('shared_labs_smoke_test', _path)
_shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared)

BASE = '/teaching/2105603/preview-2027/'
LABS = ['vle', 'case-study', 'consistency', 'stability', 'lle-fit', 'vlle', 'adiabatic', 'vle-input',
        'virial', 'solids', 'adsorption', 'reaction', 'electrochemistry']

if __name__ == '__main__':
    _shared.main(BASE, LABS)
