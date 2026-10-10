# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

"""Number of parallel workers used by scans.

The user setting is 0 for automatic, 1 for single-threaded scans or the maximum number of workers.
"""

import os

# With that many CPUs or less, automatic mode scans single-threaded
MIN_CPUS_FOR_PARALLEL = 2

_setting = 0


def set_setting(value) -> None:
    global _setting
    try:
        _setting = max(0, int(value))
    except (TypeError, ValueError):
        _setting = 0


def available_cpus() -> int:
    # process_cpu_count() respects CPU affinity and container limits (Python 3.13+)
    count = getattr(os, "process_cpu_count", os.cpu_count)()
    return count or 1


def cpu_workers() -> int:
    """Worker processes for CPU bound work such as decoding pictures."""
    if _setting > 0:
        return _setting
    cpus = available_cpus()
    return 1 if cpus <= MIN_CPUS_FOR_PARALLEL else cpus


def io_workers() -> int:
    """Threads for IO bound work such as hashing files, fast drives handle several reads in flight."""
    if _setting > 0:
        return _setting
    cpus = available_cpus()
    return 1 if cpus <= MIN_CPUS_FOR_PARALLEL else min(32, cpus + 4)
