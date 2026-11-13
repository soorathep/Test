"""Publish the scoped 2027 preview into the existing course website."""
from pathlib import Path
import shutil


def main():
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
