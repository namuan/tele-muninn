# tele-muninn
🦅

###### Setting up python3 and dependencies with VirtualEnv

```
 make setup
```

### Scripts

<!-- START makefile-doc -->
[_tele_web_links.py_](https://namuan.github.io/bin-utils/tele_web_links.html)
```
usage: tele_web_links.py [-h] [-v]

Send links to telegram on a schedule

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
[_readme_docs.py_](https://namuan.github.io/bin-utils/readme_docs.html)
```
usage: readme_docs.py [-h]

Generates documentation for the readme.md file

options:
  -h, --help  show this help message and exit

```
[_hn_new_github_repos.py_](https://namuan.github.io/bin-utils/hn_new_github_repos.html)
```
usage: hn_new_github_repos.py [-h] [-v]

Find Links to Github/GitLab and Bitbucket from HN new news
Send links over Telegram

Usage:
./hn_new_github_repos.py -h

options:
  -h, --help     show this help message and exit
  -v, --verbose  Display context variables at each step

```
[_twitter_furus.py_](https://namuan.github.io/bin-utils/twitter_furus.html)
```

```
[_tele_stock_rider_bot.py_](https://namuan.github.io/bin-utils/tele_stock_rider_bot.html)
```

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
