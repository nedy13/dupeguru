# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import multiprocessing

import pytest

from hscommon.jobprogress.job import Job, JobCancelled
from core.pe import matchblock
from core.pe.photo import Photo


class FakePhoto(Photo):
    """Picture with blocks derived from its file content. Module level, so worker processes can unpickle it."""

    def _plat_get_dimensions(self):
        return (len(self.path.read_bytes()), 10)

    def _plat_get_blocks(self, block_count_per_side, orientation):
        content = self.path.read_bytes()
        if content == b"broken":
            raise OSError(f"cannot decode {self.path}")
        value = sum(content) % 256
        return [(value, orientation, i) for i in range(block_count_per_side * block_count_per_side)]


def make_pictures(tmp_path, count, broken=()):
    pictures = []
    for i in range(count):
        path = tmp_path / f"pic{i}.jpg"
        path.write_bytes(b"broken" if i in broken else f"picture {i}".encode())
        pictures.append(FakePhoto(path))
    return pictures


def prepare(tmp_path, pictures, name, match_rotated=False, **kwargs):
    cache_path = str(tmp_path / f"{name}.db")
    prepared = matchblock.prepare_pictures(pictures, cache_path, True, match_rotated, **kwargs)
    cache = matchblock.get_cache(cache_path, readonly=True)
    blocks = {p.unicode_path: cache[p.unicode_path] for p in prepared}
    cache.close()
    return [p.unicode_path for p in prepared], [p.dimensions for p in prepared], blocks


@pytest.mark.parametrize("match_rotated", [False, True])
def test_parallel_matches_sequential(tmp_path, match_rotated):
    sequential = prepare(tmp_path, make_pictures(tmp_path, 60), "seq", match_rotated, parallel=False)
    parallel = prepare(tmp_path, make_pictures(tmp_path, 60), "par", match_rotated, parallel=True)
    assert len(sequential[0]) == 60
    assert parallel == sequential


@pytest.mark.parametrize("parallel", [False, True])
def test_unreadable_pictures_are_skipped(tmp_path, parallel):
    names, _, blocks = prepare(tmp_path, make_pictures(tmp_path, 60, broken={3, 40}), "db", parallel=parallel)
    assert len(names) == 58
    assert not any(name.endswith(("pic3.jpg", "pic40.jpg")) for name in names)
    assert len(blocks) == 58


def test_cached_pictures_are_not_recomputed(tmp_path):
    pictures = make_pictures(tmp_path, 60)
    prepare(tmp_path, pictures, "db", parallel=True)
    # Corrupt the files: blocks from the cache must be used instead of decoding them again
    for picture in pictures:
        picture.path.write_bytes(b"broken")
    names, _, _ = prepare(tmp_path, [FakePhoto(p.path) for p in pictures], "db", parallel=True)
    assert len(names) == 60


def test_cancel_stops_workers(tmp_path):
    calls = []

    def callback(progress, desc=""):
        calls.append(progress)
        return len(calls) < 5  # Cancel after a few pictures

    with pytest.raises(JobCancelled):
        prepare(tmp_path, make_pictures(tmp_path, 200), "db", j=Job(1, callback), parallel=True)
    assert multiprocessing.active_children() == []
