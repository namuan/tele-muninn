# tele-muninn

[![PyPI](https://img.shields.io/pypi/v/tele-muninn?style=flat-square)](https://pypi.python.org/pypi/tele-muninn/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tele-muninn?style=flat-square)](https://pypi.python.org/pypi/tele-muninn/)
[![PyPI - License](https://img.shields.io/pypi/l/tele-muninn?style=flat-square)](https://pypi.python.org/pypi/tele-muninn/)

---

**Homepage**: [https://github.com/namuan/tele-muninn](https://github.com/namuan/tele-muninn)

---

Just like Alfred but for Telegram

## Installation

```sh
pip install tele-muninn
```

## Usage

Setup following environment variables:
```
export TELE_MUNINN_BOT_TOKEN=
```

Run following command:
```
tele-muninn
```

## Development

* Clone this repository
* Requirements:
  * [Poetry](https://python-poetry.org/)
  * Python 3.7+
* Create a virtual environment and install the dependencies

```sh
poetry install
```

* Activate the virtual environment

```sh
poetry shell
```

### Testing

```sh
pytest
```

### Releasing

Trigger the [Draft release workflow](https://github.com/namuan/tele-muninn/actions/workflows/draft_release.yml)
(press _Run workflow_). This will update the changelog & version and create a GitHub release which is in _Draft_ state.

Find the draft release from the
[GitHub releases](https://github.com/namuan/tele-muninn/releases) and publish it. When
 a release is published, it'll trigger [release](https://github.com/namuan/tele-muninn/blob/master/.github/workflows/release.yml) workflow which creates PyPI
 release and deploys updated documentation.

### Makefile

Run `make` to see the list of available commands.
