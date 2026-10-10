# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import csv
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
