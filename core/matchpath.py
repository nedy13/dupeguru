# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

"""Relative path scan: files match when they have the same path below their scanned folder and the same size.

No file content is read, which makes the scan as fast as listing the folders, also on network drives.
"""

import os
from collections import defaultdict
from itertools import combinations

from hscommon.jobprogress import job
from hscommon.trans import tr

from core.engine import Match


def relative_path(f, roots):
    """Path of ``f`` below the deepest of ``roots`` containing it, its name alone outside of them.

    ``roots`` are strings ending with the path separator, sorted from the deepest. Strings, because
    :mod:`pathlib` is too slow for hundreds of thousands of files.
    """
    path = str(f.path)
    for root in roots:
        if path.startswith(root):
            return path[len(root) :]
    return f.name


def _root_prefixes(roots):
    prefixes = {os.path.join(str(root), "") for root in roots}
    return sorted(prefixes, key=len, reverse=True)


def getmatches(files, roots, mtime_tolerance=None, j=job.nulljob):
    """Return a :class:`Match` of 100% for each pair of ``files`` with the same relative path and size.

    With ``mtime_tolerance`` (seconds), the modification times must also differ by at most that much.
    Pairs of reference files are skipped, they are never compared to each other.
    """
    roots = _root_prefixes(roots)
    key2files = defaultdict(list)
    for f in j.iter_with_progress(files, tr("Read size of %d/%d files")):
        key2files[(relative_path(f, roots), f.size)].append(f)
    result = []
    for group in key2files.values():
        for first, second in combinations(group, 2):
            if first.is_ref and second.is_ref:
                continue
            if mtime_tolerance is not None and abs(first.mtime - second.mtime) > mtime_tolerance:
                continue
            result.append(Match(first, second, 100))
    return result
