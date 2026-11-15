"""Publish the scoped 2027 preview into the existing course website."""
from pathlib import Path
import importlib.util
import shutil


def publish_shared_kit():
    """Refresh teaching/shared/labs-kit/ first; these pages load labs-base.css and mode.js from it."""
    path = Path(__file__).resolve().parents[2] / 'shared/labs-kit/build.py'
    spec = importlib.util.spec_from_file_location('shared_labs_kit_build', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.publish()


def main():
    publish_shared_kit()
    source = Path(__file__).resolve().parent
    repository = source.parents[2]
    destination = repository / "teaching/2105603/preview-2027"
    files = [*source.glob("*.html"), *source.joinpath("assets").rglob("*")]
    for path in sorted(files):
        if not path.is_file():
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        print(target.relative_to(repository))


if __name__ == "__main__":
    main()
