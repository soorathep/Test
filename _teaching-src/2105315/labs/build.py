"""Publish the 2105315 labs from _teaching-src/2105315/labs/ to teaching/2105315/labs/.

    python3 _teaching-src/2105315/labs/build.py

The shared kit (teaching/shared/labs-kit/) is published first, because these pages load it.
Only pages and assets are copied; tools/ and tests/ stay in the source folder.
"""
from pathlib import Path
import importlib.util
import shutil


def publish_shared_kit():
    path = Path(__file__).resolve().parents[2] / 'shared/labs-kit/build.py'
    spec = importlib.util.spec_from_file_location('shared_labs_kit_build', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.publish()


def main():
    publish_shared_kit()
    source = Path(__file__).resolve().parent
    repository = source.parents[2]
    destination = repository / 'teaching/2105315/labs'
    files = [*source.glob('*.html'), *source.joinpath('assets').rglob('*')]
    for path in sorted(files):
        if not path.is_file():
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        print(target.relative_to(repository))


if __name__ == '__main__':
    main()
