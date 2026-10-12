# dupeGuruX

dupeGuruX is a cross-platform (Linux, macOS, Windows) GUI tool to find duplicate files in a system,
and the files that are missing in a reference folder such as a backup. It is written mostly in
Python 3 and uses [Qt 6][qt] through [PySide6][pyside6] for the UI.

dupeGuruX is a fork of [dupeGuru][dupeguru], created by Virgil Dupras and maintained by Andrew
Senetar. As the development of dupeGuru seemed to have come to a halt, dupeGuruX modernizes it and
adds new features:

* A Qt 6 user interface with PySide6 instead of PyQt5, and support for current Python versions.
* **Files Missing in Reference**: lists the files of the normal folders without duplicate in the
  reference folders, with a preview, and copies or moves them into the reference.
* New scan types: **Relative Path and Size** (checks a copy of a folder in seconds, also over the
  network) and **Exact Picture (ignore metadata)**.
* Parallel hashing and picture analysis.
* Packages for Arch Linux, Debian/Ubuntu, Windows and macOS built by the CI.

The settings and data of dupeGuru are taken over when dupeGuruX starts for the first time. Saved
results (`.dupeguru`) and folder lists (`.dupegurudirs`) keep their file format.

## Download
Prebuilt packages for Windows (installer and portable zip), macOS (app bundle), Debian/Ubuntu (`.deb`) and
Arch Linux are attached to the [GitHub releases](https://github.com/nedy13/dupeguru/releases). The portable zip
needs no installation and keeps its settings and data in its own folder, as long as the `settings.ini` next
to the executable is there.

## Contents of this folder

This folder contains the source for dupeGuruX. Its documentation is in `help`. Here's how this
source tree is organized:

* core: Contains the core logic code for dupeGuruX. It's Python code.
* qt: UI code for the Qt toolkit. It's written in Python and uses PySide6.
* images: Images used by the different UI codebases.
* pkg: Skeleton files required to create different packages
* help: Help document, written for Sphinx.
* locale: .po files for localization.
* hscommon: A collection of helpers used across HS applications.

## How to build dupeGuruX from source

### Windows & macOS specific additional instructions
For windows instructions see the [Windows Instructions](Windows.md).

For macos instructions (qt version) see the [macOS Instructions](macos.md).

### Prerequisites
* [Python 3.12+][python]
* [PySide6][pyside6] 6.5+

### System Setup
When running in a linux based environment the following system packages or equivalents are needed to build:
* PySide6 (Debian/Ubuntu: python3-pyside6.qtwidgets, Arch: pyside6)
* python3-venv (only if using a virtual environment)
* python3-dev
* build-essential

On Windows and macOS PySide6 is installed from PyPI together with the other dependencies.


### Building with Make
dupeGuruX comes with a makefile that can be used to build and run:

    $ make && make run

### Building without Make
All dependencies are declared in `pyproject.toml`. The editable install also compiles the C
extension modules in place:

    $ cd <dupeGuruX directory>
    $ python3 -m venv --system-site-packages ./env
    $ source ./env/bin/activate
    $ pip install -e ".[build]"
    $ python builder.py
    $ python run.py

### Generating Debian/Ubuntu package
The package is built from the distribution packages, no virtual environment is needed. It is
tested on Debian 13 (trixie), which ships PySide6:

    $ sudo apt install build-essential debhelper dpkg-dev python3-dev python3-setuptools \
        python3-sphinx python3-polib python3-distro python3-send2trash python3-mutagen \
        python3-semantic-version python3-xxhash python3-pyside6.qtwidgets qt6-base-dev-tools
    $ cd <dupeGuruX directory>
    $ python3 builder.py --clean
    $ python3 package.py

The package ends up in `build/dupegurux_<version>_amd64.deb`.

### Generating Arch Linux package
A `PKGBUILD` building the `master` branch of this fork lives in `pkg/arch`. Build it from that
directory so makepkg's `src/` and `pkg/` folders stay out of the source tree:

    $ cd pkg/arch
    $ makepkg -si

## Releases
Pushing a tag like `v4.4.0` runs the CI workflow, which builds the Windows installer, the macOS
app and the Debian and Arch Linux packages and publishes them as a GitHub release. The tag has to match
`__version__` in `core/__init__.py`.

## Running tests

The complete test suite is run with [Tox 1.7+][tox]. If you have it installed system-wide, you
don't even need to set up a virtualenv. Just `cd` into the root project folder and run `tox`.

If you don't have Tox system-wide, install it in your virtualenv with `pip install tox` and then
run `tox`.

You can also run automated tests without Tox. Install the development extras with
`pip install -e ".[dev]"` inside your virtualenv and then run `pytest core hscommon`.

[dupeguru]: https://github.com/arsenetar/dupeguru
[qt]: https://www.qt.io/
[cross-toolkit]: http://www.hardcoded.net/articles/cross-toolkit-software
[python]: http://www.python.org/
[pyside6]: https://doc.qt.io/qtforpython-6/
[tox]: https://tox.readthedocs.org/en/latest/
