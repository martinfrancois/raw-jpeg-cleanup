# rawjpgfinder

Lists JPEG files that have a RAW file with the same name next to them, and moves those JPEGs to the system trash when you ask for it.

## What it does

Cameras that shoot RAW plus JPEG leave two files per photo, for example `DSC00001.ARW` and `DSC00001.JPG`. Once the RAW files are kept, the JPEGs are usually dead weight. This tool walks a folder tree, finds every JPEG that has a RAW companion, prints the list, and only trashes anything when you pass `--trash`.

The selection rule, in full:

- A file counts as a JPEG when its extension is `.jpg` or `.jpeg`, in any letter case.
- A file counts as a RAW file when its extension is on the RAW allowlist, in any letter case. The default list is `.3fr .arw .cr2 .cr3 .crw .dng .nef .nrw .orf .pef .raf .raw .rw2 .rwl .sr2 .srw .x3f`. `--raw-extensions` replaces it.
- A JPEG is selected when a RAW file with exactly the same stem, compared case-sensitively, exists as a regular file in the same directory. `IMG_1.JPG` next to `IMG_1.CR2` is selected. `IMG_1.JPG` next to `img_1.CR2`, or next to `IMG_1.txt`, or next to `IMG_1.jpeg`, is not.
- Directories, symlinks and anything not on the allowlist never count as a RAW companion.

With `--trash`, each selected JPEG is checked again right before it is trashed: it must still exist, and its RAW companion must still exist. A pair that no longer holds is skipped and reported on stderr.

## Requirements

- Python 3.10 or newer
- A desktop trash the `send2trash` package can reach. On Linux this is the freedesktop.org trash, on macOS the Finder trash, on Windows the Recycle Bin.

## Install

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -e .
```

This puts a `rawjpgfinder` command on the virtualenv's PATH.

## Usage

Dry run. Nothing is changed. One selected JPEG per line on stdout, a count on stderr:

```sh
rawjpgfinder /path/to/photos
```

Trash the selected JPEGs:

```sh
rawjpgfinder /path/to/photos --trash
```

Use a different RAW allowlist, for example only Sony files:

```sh
rawjpgfinder /path/to/photos --raw-extensions arw
```

Trashed files go to the system trash, not to `rm`. To get one back, open the trash in your file manager and restore it. On Linux the file sits in `~/.local/share/Trash/files/`, or in `.Trash-<uid>/files/` at the root of the mount the photos live on when that mount is not the home directory's.

## Example

`examples/photos/` holds empty placeholder files. Run the dry run on it:

```sh
rawjpgfinder examples/photos
```

Expected output:

```
examples/photos/2024-05/DSC00010.JPG	(RAW: DSC00010.ARW)
examples/photos/DSC00001.JPG	(RAW: DSC00001.ARW)
examples/photos/DSC00002.jpeg	(RAW: DSC00002.ARW)
3 JPEG file(s) would be trashed. Re-run with --trash to do it.
```

`DSC00003.JPG` is not listed because it has no RAW companion, `DSC00004.ARW` has no JPEG, and `notes.JPG` is not listed because `notes.txt` is not a RAW file.

## Tests

```sh
python -m pytest
```

The tests create empty placeholder files in a temporary directory and mock the trash call, so they never touch your trash or your photos.

## Limitations

- Only the file names are compared. The tool does not open the files, so a JPEG that is not a preview of its RAW twin, but happens to share the name, is still selected.
- One RAW file with the stem is enough. If several RAW files share a stem, the JPEG is selected and the first RAW name in sort order is reported.
- If the trash cannot be reached, the file is skipped and reported. The tool never deletes outright.

## License

MIT, see [LICENSE](LICENSE).
