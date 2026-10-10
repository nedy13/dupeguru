# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import pytest

from core import engine, fs, workers


@pytest.fixture(autouse=True)
def reset_setting():
    yield
    workers.set_setting(0)


@pytest.mark.parametrize(
    "setting, cpus, cpu_workers, io_workers",
    [
        (0, 1, 1, 1),  # automatic, small computers stay single-threaded
        (0, 2, 1, 1),
        (0, 4, 4, 8),
        (0, 24, 24, 28),
        (0, 64, 64, 32),
        (1, 24, 1, 1),  # single-threaded
        (6, 24, 6, 6),  # fixed number of workers
        ("bogus", 24, 24, 28),  # invalid values fall back to automatic
    ],
)
def test_worker_counts(monkeypatch, setting, cpus, cpu_workers, io_workers):
    monkeypatch.setattr(workers, "available_cpus", lambda: cpus)
    workers.set_setting(setting)
    assert workers.cpu_workers() == cpu_workers
    assert workers.io_workers() == io_workers


def make_files(tmp_path):
    contents = {
        "a1": b"a" * 50000,
        "a2": b"a" * 50000,
        "a3": b"a" * 49999 + b"x",  # same size and partial digest, different content
        "b1": b"b" * 70000,
        "b2": b"b" * 70000,
        "c": b"c" * 70000,  # same size as b, different content
        "small1": b"tiny",
        "small2": b"tiny",
        "empty1": b"",
        "empty2": b"",
        "unique": b"unique" * 1000,
    }
    files = []
    for name, data in contents.items():
        path = tmp_path / name
        path.write_bytes(data)
        f = fs.File(path)
        f.is_ref = False  # set by the scanner in a real scan
        files.append(f)
    return files


def match_names(matches):
    return sorted(tuple(sorted((m.first.name, m.second.name))) for m in matches)


@pytest.fixture
def no_hash_cache(monkeypatch):
    # Digests must be computed, not taken from the database of a previous run
    monkeypatch.setattr(fs.filesdb, "get", lambda path, key: None)
    monkeypatch.setattr(fs.filesdb, "put", lambda path, key, value: None)


@pytest.mark.parametrize("bigsize", [0, 60000])
def test_contents_matches_same_for_any_worker_count(tmp_path, no_hash_cache, bigsize):
    results = {}
    for setting in (1, 8):
        workers.set_setting(setting)
        folder = tmp_path / str(setting)
        folder.mkdir()
        results[setting] = match_names(engine.getmatches_by_contents(make_files(folder), bigsize=bigsize))
    assert results[1] == results[8]
    assert results[8] == [("a1", "a2"), ("b1", "b2"), ("empty1", "empty2"), ("small1", "small2")]
