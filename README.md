# RAW + JPG, JPG Finder

Finds JPG files where a RAW file with the same name is in the same folder.

1. Install dependencies with `python3 -m pip install -r requirements.txt`.
2. Run `python3 raw_jpeg_cleanup.py /path/to/photos` to list matching JPEG paths, one per line on stdout. The count goes to stderr.
3. Review the list, then run `python3 raw_jpeg_cleanup.py /path/to/photos --trash` to move those JPEGs to the system trash.

Requires Python 3.10 or newer. A pair has the same case-sensitive filename stem, a `.jpg` or `.jpeg` extension, and a regular RAW file beside it. RAW extensions come from the allowlist shown by `--help`; `--raw-extensions` replaces it. Symlinks do not count as RAW companions. The tool compares names, not image contents. It checks each pair again before trashing. Restore trashed files through your file manager.

For a dry run on synthetic files, use `python3 raw_jpeg_cleanup.py examples/photos`. It prints these paths:

```text
examples/photos/2024-05/DSC00010.JPG
examples/photos/DSC00001.JPG
examples/photos/DSC00002.jpeg
```

Run tests with `python3 -m pytest`. Tests never use your photos or trash.

MIT, see [LICENSE](LICENSE).
