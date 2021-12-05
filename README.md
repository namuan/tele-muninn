# tele-muninn

[![PyPI](https://img.shields.io/pypi/v/tele-muninn?style=flat-square)](https://pypi.python.org/pypi/tele-muninn/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tele-muninn?style=flat-square)](https://pypi.python.org/pypi/tele-muninn/)
[![PyPI - License](https://img.shields.io/pypi/l/tele-muninn?style=flat-square)](https://pypi.python.org/pypi/tele-muninn/)
[![Coookiecutter - Wolt](https://img.shields.io/badge/cookiecutter-Wolt-00c2e8?style=flat-square&logo=cookiecutter&logoColor=D4AA00&link=https://github.com/woltapp/wolt-python-package-cookiecutter)](https://github.com/woltapp/wolt-python-package-cookiecutter)


---

**Documentation**: [https://namuan.github.io/tele-muninn](https://namuan.github.io/tele-muninn)

**Source Code**: [https://github.com/namuan/tele-muninn](https://github.com/namuan/tele-muninn)

**PyPI**: [https://pypi.org/project/tele-muninn/](https://pypi.org/project/tele-muninn/)

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
