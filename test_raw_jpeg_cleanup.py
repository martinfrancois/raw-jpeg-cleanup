from pathlib import Path
from unittest.mock import patch

import pytest

import raw_jpeg_cleanup
from raw_jpeg_cleanup import DEFAULT_RAW_EXTENSIONS, Pair, find_pairs, main, normalize_extensions, trash_pairs

RAW = normalize_extensions(DEFAULT_RAW_EXTENSIONS)
EXAMPLES = Path(__file__).parent / "examples" / "photos"


def touch(directory: Path, *names: str) -> None:
    for name in names:
        (directory / name).touch()


def jpegs(pairs: list[Pair]) -> list[str]:
    return [pair.jpeg.name for pair in pairs]


def test_jpeg_with_raw_companion_is_selected(tmp_path: Path) -> None:
    touch(tmp_path, "DSC00001.ARW", "DSC00001.JPG")
    pairs = find_pairs(tmp_path, RAW)
    assert pairs == [Pair(jpeg=tmp_path / "DSC00001.JPG", raw=tmp_path / "DSC00001.ARW")]


def test_jpeg_with_non_raw_twin_is_not_selected(tmp_path: Path) -> None:
    # Same stem, but the twin is not a RAW file.
    touch(tmp_path, "notes.txt", "notes.JPG", "scan.png", "scan.jpg", "a.jpg", "a.jpeg")
    assert find_pairs(tmp_path, RAW) == []


def test_non_raw_twin_next_to_a_raw_still_selects_the_jpeg(tmp_path: Path) -> None:
    touch(tmp_path, "DSC00001.txt", "DSC00001.JPG", "DSC00001.ARW")
    assert jpegs(find_pairs(tmp_path, RAW)) == ["DSC00001.JPG"]


def test_lonely_jpeg_is_not_selected(tmp_path: Path) -> None:
    touch(tmp_path, "DSC00003.JPG", "DSC00004.ARW")
    assert find_pairs(tmp_path, RAW) == []


def test_extension_case_is_ignored_and_stem_case_is_not(tmp_path: Path) -> None:
    touch(tmp_path, "a.arw", "a.jpeg", "B.Cr2", "B.Jpg", "c.ARW", "C.JPG")
    assert jpegs(find_pairs(tmp_path, RAW)) == ["B.Jpg", "a.jpeg"]


def test_raw_must_be_in_the_same_directory(tmp_path: Path) -> None:
    (tmp_path / "raw").mkdir()
    touch(tmp_path / "raw", "DSC00001.ARW")
    touch(tmp_path, "DSC00001.JPG")
    assert find_pairs(tmp_path, RAW) == []


def test_subdirectories_are_scanned(tmp_path: Path) -> None:
    nested = tmp_path / "2024" / "05"
    nested.mkdir(parents=True)
    touch(nested, "x.nef", "x.jpg")
    assert jpegs(find_pairs(tmp_path, RAW)) == ["x.jpg"]


def test_only_allowlisted_extensions_count(tmp_path: Path) -> None:
    touch(tmp_path, "a.arw", "a.jpg", "b.xyz", "b.jpg")
    assert jpegs(find_pairs(tmp_path, RAW)) == ["a.jpg"]
    assert jpegs(find_pairs(tmp_path, normalize_extensions(["xyz"]))) == ["b.jpg"]


def test_directories_and_broken_symlinks_are_not_companions(tmp_path: Path) -> None:
    (tmp_path / "a.arw").mkdir()
    touch(tmp_path, "a.jpg", "b.jpg")
    (tmp_path / "b.arw").symlink_to(tmp_path / "missing.arw")
    assert find_pairs(tmp_path, RAW) == []


def test_normalize_extensions_rejects_empty_and_jpeg() -> None:
    assert normalize_extensions(["ARW", " .cr2 ", ""]) == frozenset({".arw", ".cr2"})
    with pytest.raises(ValueError):
        normalize_extensions([""])
    with pytest.raises(ValueError):
        normalize_extensions([".arw", "jpg"])


def test_dry_run_is_the_default_and_changes_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    touch(tmp_path, "a.arw", "a.jpg")
    with patch.object(raw_jpeg_cleanup.send2trash, "send2trash") as trash:
        assert main([str(tmp_path)]) == 0
    trash.assert_not_called()
    out, err = capsys.readouterr()
    assert str(tmp_path / "a.jpg") in out
    assert "1 JPEG file(s) would be trashed" in err
    assert (tmp_path / "a.jpg").exists()


def test_trash_flag_trashes_only_paired_jpegs(tmp_path: Path) -> None:
    touch(tmp_path, "a.arw", "a.jpg", "notes.txt", "notes.jpg", "lonely.jpg")
    with patch.object(raw_jpeg_cleanup.send2trash, "send2trash") as trash:
        assert main([str(tmp_path), "--trash"]) == 0
    trash.assert_called_once_with(str(tmp_path / "a.jpg"))


def test_pair_is_revalidated_right_before_trashing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    touch(tmp_path, "a.arw", "a.jpg", "b.arw", "b.jpg")
    pairs = find_pairs(tmp_path, RAW)
    assert jpegs(pairs) == ["a.jpg", "b.jpg"]
    (tmp_path / "a.arw").unlink()
    with patch.object(raw_jpeg_cleanup.send2trash, "send2trash") as trash:
        assert trash_pairs(pairs, RAW) == (1, 1)
    trash.assert_called_once_with(str(tmp_path / "b.jpg"))
    assert "skip (no RAW companion any more)" in capsys.readouterr().err


def test_trash_failure_is_reported_and_skipped(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    touch(tmp_path, "a.arw", "a.jpg")
    pairs = find_pairs(tmp_path, RAW)
    with patch.object(raw_jpeg_cleanup.send2trash, "send2trash", side_effect=OSError("no trash here")):
        assert trash_pairs(pairs, RAW) == (0, 1)
    assert "no trash here" in capsys.readouterr().err
    assert (tmp_path / "a.jpg").exists()


def test_missing_folder_fails(tmp_path: Path) -> None:
    assert main([str(tmp_path / "nope")]) == 2


def test_example_folder(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(EXAMPLES)]) == 0
    out, _err = capsys.readouterr()
    selected = [line.split("\t")[0] for line in out.splitlines()]
    assert selected == [
        str(EXAMPLES / "2024-05" / "DSC00010.JPG"),
        str(EXAMPLES / "DSC00001.JPG"),
        str(EXAMPLES / "DSC00002.jpeg"),
    ]
