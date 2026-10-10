# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import csv
import os
from collections import namedtuple

import pytest

from core import fs, missing
from core.engine import Match
from core.scanner import Scanner, ScanType

FakeFile = namedtuple("FakeFile", "name is_ref")


def match(first, second):
    return Match(first, second, 100)


def test_none_without_reference():
    files = [FakeFile("a", False), FakeFile("b", False)]
    assert missing.get_missing_in_reference(files, []) is None


def test_files_matching_a_reference_file_are_not_missing():
    ref, present, absent = FakeFile("ref", True), FakeFile("present", False), FakeFile("absent", False)
    result = missing.get_missing_in_reference([ref, present, absent], [match(present, ref)])
    assert result == [absent]


def test_duplicates_in_normal_folders_dont_count():
    ref = FakeFile("ref", True)
    copy1, copy2 = FakeFile("copy1", False), FakeFile("copy2", False)
    assert missing.get_missing_in_reference([ref, copy1, copy2], [match(copy1, copy2)]) == [copy1, copy2]


def test_all_reference_folders_form_one_reference():
    ref1, ref2 = FakeFile("ref1", True), FakeFile("ref2", True)
    in_ref1, in_ref2 = FakeFile("in_ref1", False), FakeFile("in_ref2", False)
    files = [ref1, ref2, in_ref1, in_ref2]
    assert missing.get_missing_in_reference(files, [match(ref1, in_ref1), match(in_ref2, ref2)]) == []


@pytest.fixture
def no_hash_cache(monkeypatch):
    monkeypatch.setattr(fs.filesdb, "get", lambda path, key: None)
    monkeypatch.setattr(fs.filesdb, "put", lambda path, key, value: None)


def test_contents_scan(tmp_path, no_hash_cache):
    # Two reference folders and two normal folders
    layout = {
        "ref1": {"a.jpg": b"A" * 20000, "only_in_ref.jpg": b"R" * 20000},
        "ref2": {"b.jpg": b"B" * 20000},
        "normal1": {"a.jpg": b"A" * 20000, "c.jpg": b"C" * 20000, "d.jpg": b"D" * 20000},
        "normal2": {"b_renamed.jpg": b"B" * 20000, "c_copy.jpg": b"C" * 20000},
    }
    files = []
    for folder, contents in layout.items():
        (tmp_path / folder).mkdir()
        for name, data in contents.items():
            (tmp_path / folder / name).write_bytes(data)
            f = fs.File(tmp_path / folder / name)
            f.is_ref = folder.startswith("ref")
            files.append(f)
    scanner = Scanner()
    scanner.scan_type = ScanType.CONTENTS
    scanner.get_dupe_groups(files)
    found = sorted(f"{f.path.parent.name}/{f.name}" for f in scanner.missing_in_reference)
    # a and b are in a reference folder, c is duplicated but only in normal folders, d exists once
    assert found == ["normal1/c.jpg", "normal1/d.jpg", "normal2/c_copy.jpg"]


def test_export_to_csv(tmp_path):
    path = tmp_path / "pic.jpg"
    path.write_bytes(b"x" * 2048)
    dest = tmp_path / "missing.csv"
    missing.export_to_csv([fs.File(path)], dest)
    with open(dest, encoding="utf-8", newline="") as fp:
        rows = list(csv.reader(fp))
    assert rows[0] == missing.COLUMNS
    assert rows[1][:3] == ["pic.jpg", str(tmp_path), "2048"]


def test_destination_keeps_subfolders(tmp_path):
    root = tmp_path / "normal"
    (root / "2019" / "summer").mkdir(parents=True)
    path = root / "2019" / "summer" / "x.jpg"
    path.write_bytes(b"x")
    dest = missing.destination_for(fs.File(path), [tmp_path / "other", root], tmp_path / "ref")
    assert dest == tmp_path / "ref" / "2019" / "summer" / "x.jpg"


def test_transfer_copies_with_timestamp_and_never_overwrites(tmp_path):
    source = tmp_path / "x.jpg"
    source.write_bytes(b"new")
    os.utime(source, (1_000_000_000, 1_000_000_000))
    dest = tmp_path / "dest" / "sub" / "x.jpg"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"existing")
    final = missing.transfer(source, dest, copy=True)
    assert dest.read_bytes() == b"existing"
    assert final.name == "[000] x.jpg"
    assert final.read_bytes() == b"new"
    assert final.stat().st_mtime == 1_000_000_000
    assert source.exists()


def make_app_with_missing(tmp_path, monkeypatch):
    from core.directories import DirectoryState
    from core.tests.base import DupeGuru
    from hscommon.jobprogress import job

    app = DupeGuru()
    monkeypatch.setattr(app, "_start_job", lambda jobid, func: func(job.nulljob))
    ref, normal = tmp_path / "ref", tmp_path / "normal"
    (ref).mkdir()
    (normal / "2020").mkdir(parents=True)
    app.directories.add_path(ref)
    app.directories.add_path(normal)
    app.directories.set_state(ref, DirectoryState.REFERENCE)
    files = []
    for name in ("a.jpg", "b.jpg"):
        (normal / "2020" / name).write_bytes(name.encode())
        files.append(fs.File(normal / "2020" / name))
    app.missing_in_reference = list(files)
    return app, ref, normal, files


def test_copy_to_reference_removes_from_list(tmp_path, monkeypatch):
    app, ref, normal, files = make_app_with_missing(tmp_path, monkeypatch)
    app.copy_or_move_missing(files[:1], True, ref)
    assert (ref / "2020" / "a.jpg").read_bytes() == b"a.jpg"
    assert (normal / "2020" / "a.jpg").exists()
    assert app.missing_in_reference == files[1:]


def test_copy_elsewhere_keeps_list(tmp_path, monkeypatch):
    app, ref, normal, files = make_app_with_missing(tmp_path, monkeypatch)
    app.copy_or_move_missing(files, True, tmp_path / "backup")
    assert (tmp_path / "backup" / "2020" / "b.jpg").exists()
    assert app.missing_in_reference == files


def test_move_removes_from_list(tmp_path, monkeypatch):
    app, ref, normal, files = make_app_with_missing(tmp_path, monkeypatch)
    app.copy_or_move_missing(files, False, tmp_path / "elsewhere")
    assert (tmp_path / "elsewhere" / "2020" / "a.jpg").exists()
    assert not (normal / "2020" / "a.jpg").exists()
    assert app.missing_in_reference == []
    assert "2 files were moved." in app._missing_transfer_message()


def test_reference_folders(tmp_path, monkeypatch):
    from core.directories import DirectoryState

    app, ref, normal, files = make_app_with_missing(tmp_path, monkeypatch)
    app.directories.set_state(normal / "2020", DirectoryState.REFERENCE)
    assert missing.reference_folders(app.directories) == sorted([ref, normal / "2020"])


def test_files_below_size_threshold_are_not_missing(tmp_path, no_hash_cache):
    # They are not compared, so the scan can't tell whether the reference has them
    (tmp_path / "ref").mkdir()
    (tmp_path / "normal").mkdir()
    files = []
    for folder, name, data in (
        ("ref", "small.txt", b"s" * 100),
        ("normal", "small.txt", b"s" * 100),
        ("normal", "big.txt", b"b" * 20000),
    ):
        (tmp_path / folder / name).write_bytes(data)
        f = fs.File(tmp_path / folder / name)
        f.is_ref = folder == "ref"
        files.append(f)
    scanner = Scanner()
    scanner.scan_type = ScanType.CONTENTS
    scanner.size_threshold = 1000
    scanner.get_dupe_groups(files)
    assert [f.name for f in scanner.missing_in_reference] == ["big.txt"]
