# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

"""Exact picture scan: pictures match when their pixels are identical, whatever their metadata."""

import logging
import multiprocessing
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from hscommon.jobprogress import job
from hscommon.trans import tr

from core import fs, workers
from core.engine import Match

# Below this amount of pictures, starting worker processes costs more than it saves
PARALLEL_MIN_PICTURES = 50
CACHE_KEY = "pixel_digest"


def _pixel_digest_in_worker(args):
    picture_class, path = args
    try:
        return picture_class(Path(path)).get_pixel_digest(), None
    except (OSError, ValueError) as e:
        return None, str(e)
    except MemoryError:
        return None, f"Ran out of memory while reading {path}"


def _computed_digests(pictures, parallel):
    """Yield ``(picture, digest, error)`` for ``pictures``, decoded in worker processes if ``parallel``."""
    if parallel:
        args = [(type(picture), str(picture.path)) for picture in pictures]
        # Leaving the with block terminates the workers, which also stops them on cancel
        with multiprocessing.Pool(workers.cpu_workers()) as pool:
            for picture, (digest, error) in zip(pictures, pool.imap(_pixel_digest_in_worker, args, chunksize=4)):
                yield picture, digest, error
        return
    for picture in pictures:
        digest, error = _pixel_digest_in_worker((type(picture), str(picture.path)))
        yield picture, digest, error


def _cached_digest(picture):
    try:
        return fs.filesdb.get(picture.path, CACHE_KEY)
    except OSError:
        return None


def get_pixel_digests(pictures, j=job.nulljob, parallel=None):
    """Return ``{picture: pixel digest}``, computing the digests missing from the hash cache.

    Pictures that can't be read are left out.
    """
    digests = {}
    todo = []
    for picture in pictures:
        cached = _cached_digest(picture)
        if cached:
            digests[picture] = cached
        else:
            todo.append(picture)
    if parallel is None:
        parallel = workers.cpu_workers() > 1 and len(todo) >= PARALLEL_MIN_PICTURES
    computed = _computed_digests(todo, parallel)
    try:
        for picture, digest, error in j.iter_with_progress(computed, tr("Analyzed %d/%d pictures"), count=len(todo)):
            if error is not None:
                logging.warning(error)
                continue
            digests[picture] = digest
            fs.filesdb.put(picture.path, CACHE_KEY, digest)
    finally:
        computed.close()
    return digests


def getmatches(pictures, j=job.nulljob, parallel=None):
    """Return a :class:`Match` of 100% for each pair of ``pictures`` with identical pixels.

    Pairs of reference pictures are skipped, they are never compared to each other.
    """
    j = j.start_subjob([9, 1])
    digests = get_pixel_digests(pictures, j, parallel)
    digest2pictures = defaultdict(list)
    for picture, digest in digests.items():
        digest2pictures[digest].append(picture)
    result = []
    groups = [group for group in digest2pictures.values() if len(group) > 1]
    for group in j.iter_with_progress(groups, tr("Verified %d/%d matches")):
        for first, second in combinations(group, 2):
            if first.is_ref and second.is_ref:
                continue
            result.append(Match(first, second, 100))
    return result
