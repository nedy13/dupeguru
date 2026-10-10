# dupeGuru

[dupeGuru][dupeguru] is a cross-platform (Linux, OS X, Windows) GUI tool to find duplicate files in
a system. It is written mostly in Python 3 and uses [qt](https://www.qt.io/) for the UI.

This is a fork of [arsenetar/dupeguru](https://github.com/arsenetar/dupeguru) that uses
[PySide6][pyside6] instead of PyQt.

## Download
Prebuilt packages for Windows (installer), macOS (app bundle) and Arch Linux are attached to the
[GitHub releases](https://github.com/nedy13/dupeguru/releases).

## Current status
Still looking for additional help especially with regards to:
* OSX maintenance: reproducing bugs, packaging verification.
* Linux maintenance: reproducing bugs, maintaining PPA repository, Debian package, rpm package.
* Translations: updating missing strings, transifex project at https://www.transifex.com/voltaicideas/dupeguru-1
* Documentation: keeping it up-to-date.

## Contents of this folder

This folder contains the source for dupeGuru. Its documentation is in `help`, but is also
[available online][documentation] in its built form. Here's how this source tree is organized:

* core: Contains the core logic code for dupeGuru. It's Python code.
* qt: UI code for the Qt toolkit. It's written in Python and uses PySide6.
* images: Images used by the different UI codebases.
* pkg: Skeleton files required to create different packages
* help: Help document, written for Sphinx.
* locale: .po files for localization.
* hscommon: A collection of helpers used across HS applications.

## How to build dupeGuru from source

### Windows & macOS specific additional instructions
For windows instructions see the [Windows Instructions](Windows.md).

For macos instructions (qt version) see the [macOS Instructions](macos.md).

### Prerequisites
* [Python 3.10+][python]
* [PySide6][pyside6] 6.5+

### System Setup
When running in a linux based environment the following system packages or equivalents are needed to build:
* PySide6 (Debian/Ubuntu: python3-pyside6.qtwidgets, Arch: pyside6)
* python3-venv (only if using a virtual environment)
* python3-dev
* build-essential

On Windows and macOS PySide6 is installed from PyPI together with the other dependencies.

To create Debian packages the following are also needed:
* python3-setuptools
* debhelper

### Building with Make
dupeGuru comes with a makefile that can be used to build and run:

    $ make && make run

### Building without Make
All dependencies are declared in `pyproject.toml`. The editable install also compiles the C
extension modules in place:

    $ cd <dupeGuru directory>
    $ python3 -m venv --system-site-packages ./env
    $ source ./env/bin/activate
    $ pip install -e ".[build]"
    $ python builder.py
    $ python run.py

### Generating Debian/Ubuntu package

    $ cd <dupeGuru directory>
    $ python3 -m venv --system-site-packages ./env
    $ source ./env/bin/activate
    $ pip install -e ".[build]"
    $ python builder.py --clean
    $ python package.py

### Generating Arch Linux package
A `PKGBUILD` building the `master` branch of this fork lives in `pkg/arch`. Build it from that
directory so makepkg's `src/` and `pkg/` folders stay out of the source tree:

    $ cd pkg/arch
    $ makepkg -si

## Releases
Pushing a tag like `v4.4.0` runs the CI workflow, which builds the Windows installer, the macOS
app and the Arch Linux package and publishes them as a GitHub release. The tag has to match
`__version__` in `core/__init__.py`.

## Running tests

The complete test suite is run with [Tox 1.7+][tox]. If you have it installed system-wide, you
don't even need to set up a virtualenv. Just `cd` into the root project folder and run `tox`.

If you don't have Tox system-wide, install it in your virtualenv with `pip install tox` and then
run `tox`.

You can also run automated tests without Tox. Install the development extras with
`pip install -e ".[dev]"` inside your virtualenv and then run `pytest core hscommon`.

[dupeguru]: https://dupeguru.voltaicideas.net/
[cross-toolkit]: http://www.hardcoded.net/articles/cross-toolkit-software
[documentation]: http://dupeguru.voltaicideas.net/help/en/
[python]: http://www.python.org/
[pyside6]: https://doc.qt.io/qtforpython-6/
[tox]: https://tox.readthedocs.org/en/latest/
