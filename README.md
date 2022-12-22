# tele-muninn
🦅

###### Setting up python3 and dependencies with VirtualEnv

```
 make setup
```

### Scripts

<!-- START makefile-doc -->
[_readme_docs.py_](https://namuan.github.io/bin-utils/readme_docs.html)
```
usage: readme_docs.py [-h]

Generates documentation for the readme.md file

options:
  -h, --help  show this help message and exit

```
[_rider_brain_bot.py_](https://namuan.github.io/bin-utils/rider_brain_bot.html)
```
usage: rider_brain_bot.py [-h]

🧠 Telegram bot to bookmark stuff

options:
  -h, --help  show this help message and exit

```
<!-- END makefile-doc -->

### DEV: Setting up Pre-commit hooks

Add following dependencies in requirements/dev.txt
```
pre-commit
black
flake8
...
```

Run `make deps` to update dependencies

Create following files and add appropriate configurations
```
touch .flake8
touch .pre-commit-config.yaml
touch .pyproject.toml
```

Run `pre-commit install` to setup git hooks.

Commit and push all the changes
