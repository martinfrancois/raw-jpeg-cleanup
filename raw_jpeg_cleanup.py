"""Find JPEG files that sit next to a RAW file with the same name, and trash them on request."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import send2trash

JPEG_EXTENSIONS = frozenset({".jpg", ".jpeg"})

# Extensions the tool treats as RAW. A JPEG is only selected when a file with one of
# these extensions and the same stem exists in the same directory. Anything not in this
# list, such as .txt or .png, never counts as a RAW companion.
DEFAULT_RAW_EXTENSIONS = (
    ".3fr", ".arw", ".cr2", ".cr3", ".crw", ".dng", ".nef", ".nrw", ".orf",
    ".pef", ".raf", ".raw", ".rw2", ".rwl", ".sr2", ".srw", ".x3f",
)

EXIT_SKIPPED = 1
# argparse exits with 2 on bad arguments, so the tool's own usage errors match it.
EXIT_USAGE = 2


@dataclass(frozen=True)
class Pair:
    jpeg: Path
    raw: Path


def normalize_extensions(values: Iterable[str]) -> frozenset[str]:
    """Lowercase each extension and make sure it starts with a dot."""
    normalized = set()
    for value in values:
        cleaned = value.strip().lower()
        if not cleaned:
            continue
        if not cleaned.startswith("."):
            cleaned = "." + cleaned
        normalized.add(cleaned)
    if not normalized:
        raise ValueError("the RAW extension list must not be empty")
    overlap = normalized & JPEG_EXTENSIONS
    if overlap:
        raise ValueError(f"a JPEG extension cannot be a RAW extension: {sorted(overlap)}")
    return frozenset(normalized)


def is_jpeg(path: Path) -> bool:
    """Return whether `path` is an existing file with a JPEG extension in any letter case."""
    return path.suffix.lower() in JPEG_EXTENSIONS and path.is_file()


def raw_files_by_stem(directory: Path, raw_extensions: frozenset[str]) -> dict[str, Path]:
    """Map each stem to the regular RAW file in one directory that carries it.

    The stem is taken as is, so the comparison is case-sensitive. The extension
    is lowercased before it is checked against the allowlist. When several RAW
    files share a stem, the one whose name sorts first wins.
    """
    index: dict[str, Path] = {}
    try:
        entries = list(os.scandir(directory))
    except OSError:
        return index
    for entry in entries:
        candidate = Path(entry.path)
        if candidate.suffix.lower() in raw_extensions and entry.is_file(follow_symlinks=False):
            current = index.get(candidate.stem)
            index[candidate.stem] = candidate if current is None else min(current, candidate)
    return index


def raw_companion(jpeg: Path, raw_extensions: frozenset[str]) -> Path | None:
    """Return the RAW file next to `jpeg` with the same stem, or None.

    Reads the directory fresh on every call, so it doubles as the check right
    before trashing.
    """
    if not is_jpeg(jpeg):
        return None
    return raw_files_by_stem(jpeg.parent, raw_extensions).get(jpeg.stem)


def find_pairs(folder: Path, raw_extensions: frozenset[str]) -> list[Pair]:
    """Walk `folder` and return every JPEG that has a RAW companion, sorted by path."""
    pairs = []
    for root, _dirs, files in os.walk(folder):
        directory = Path(root)
        index = None
        for name in files:
            jpeg = directory / name
            if not is_jpeg(jpeg):
                continue
            if index is None:
                index = raw_files_by_stem(directory, raw_extensions)
            raw = index.get(jpeg.stem)
            if raw is not None:
                pairs.append(Pair(jpeg=jpeg, raw=raw))
    return sorted(pairs, key=lambda pair: str(pair.jpeg))


def trash_pairs(pairs: Sequence[Pair], raw_extensions: frozenset[str]) -> tuple[int, int]:
    """Send each JPEG to the trash after checking its RAW companion still exists.

    Every pair is validated again right before the trash call, so a RAW file that
    disappeared between the scan and this step keeps its JPEG. Returns the number
    of trashed and skipped files.
    """
    trashed = 0
    skipped = 0
    for pair in pairs:
        current_raw = raw_companion(pair.jpeg, raw_extensions)
        if current_raw is None:
            print(f"skip (no RAW companion any more): {pair.jpeg}", file=sys.stderr)
            skipped += 1
            continue
        try:
            send2trash.send2trash(str(pair.jpeg))
        except OSError as error:
            print(f"skip ({error}): {pair.jpeg}", file=sys.stderr)
            skipped += 1
            continue
        print(f"trashed: {pair.jpeg}")
        trashed += 1
    sys.stdout.flush()
    return trashed, skipped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="raw-jpeg-cleanup",
        description=(
            "List JPEG files that have a RAW file with the same name in the same directory. "
            "Without --trash nothing is changed."
        ),
    )
    parser.add_argument("folder", type=Path, help="directory to scan recursively")
    parser.add_argument(
        "--trash",
        action="store_true",
        help="move the listed JPEG files to the system trash instead of only listing them",
    )
    parser.add_argument(
        "--raw-extensions",
        default=",".join(DEFAULT_RAW_EXTENSIONS),
        help="comma-separated extensions that count as RAW (default: %(default)s)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    folder = args.folder
    if not folder.is_dir():
        print(f"not a directory: {folder}", file=sys.stderr)
        return EXIT_USAGE
    try:
        raw_extensions = normalize_extensions(args.raw_extensions.split(","))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return EXIT_USAGE

    pairs = find_pairs(folder, raw_extensions)
    if not args.trash:
        for pair in pairs:
            print(f"{pair.jpeg}\t(RAW: {pair.raw.name})")
        sys.stdout.flush()
        print(f"{len(pairs)} JPEG file(s) would be trashed. Re-run with --trash to do it.", file=sys.stderr)
        return 0

    trashed, skipped = trash_pairs(pairs, raw_extensions)
    print(f"trashed {trashed} JPEG file(s), skipped {skipped}.", file=sys.stderr)
    return EXIT_SKIPPED if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
