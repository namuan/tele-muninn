# tele-muninn

Collection of Telegram bots

![](muninn-logo.jpg)

> Acrylic Paint of Muninn, Aerial View, in the style of Ancient Egyptian Art

###### Setting up python3 and dependencies with VirtualEnv

```
 make setup
```

### Scripts

<!-- START makefile-doc -->
[_tele_bookmark_bot.py_](https://namuan.github.io/tele-muninn/tele_bookmark_bot.html)
```
usage: tele_bookmark_bot.py [-h] [-v]

Bookmark notes, web pages, tweets, youtube videos, and photos.

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
[_tele_web_links.py_](https://namuan.github.io/tele-muninn/tele_web_links.html)
```
usage: tele_web_links.py [-h] [-v]

Send links to telegram on a schedule

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
[_tele_pathy.py_](https://namuan.github.io/tele-muninn/tele_pathy.html)
```
usage: tele_pathy.py [-h] [-v]

Receive voice messages from Telegram and convert them to text using OpenAI Whisper
Then send the text to OpenAI GPT-3 to generate a response
Then convert the response back to audio using TTS
Then send the audio back to Telegram

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
[_webpage_to_pdf.py_](https://namuan.github.io/tele-muninn/webpage_to_pdf.html)
```
usage: webpage_to_pdf.py [-h] -i INPUT_URL -o OUTPUT_FILE_PATH
                         [-w WAIT_IN_SECS_BEFORE_CAPTURE] [-s] [-v]

Generate PDF from a webpage

options:
  -h, --help            show this help message and exit
  -i INPUT_URL, --input-url INPUT_URL
                        Web Url
  -o OUTPUT_FILE_PATH, --output-file-path OUTPUT_FILE_PATH
                        Full output file path for PDF
  -w WAIT_IN_SECS_BEFORE_CAPTURE, --wait-in-secs-before-capture WAIT_IN_SECS_BEFORE_CAPTURE
                        Wait (in secs) before capturing screenshot
  -s, --headless        Run headless (no browser window)
  -v, --verbose         Increase verbosity of logging output

```
[_hn_new_github_repos.py_](https://namuan.github.io/tele-muninn/hn_new_github_repos.html)
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
[_bot_template.py_](https://namuan.github.io/tele-muninn/bot_template.html)
```
usage: bot_template.py [-h] [-v]

Listen to messages with tt and ii prefix
If a message begins with tt then it'll send a prompt to OpenAI Completion API
If a message begins with ii then it'll send a prompt to OpenAI Image API

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
[_twitter_furus.py_](https://namuan.github.io/tele-muninn/twitter_furus.html)
```
usage: twitter_furus.py [-h] [-v]

Fetch tweets from a list of twitter accounts and send the tweets to a telegram group
It also generates a chart for the stock symbol mentioned in the tweet

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
[_tele_stock_rider_bot.py_](https://namuan.github.io/tele-muninn/tele_stock_rider_bot.html)
```
usage: tele_stock_rider_bot.py [-h] [-v]

Listen to messages with a stock ticker starting with a $ sign and reply with a chart.
It also sends a messages with links to various websites with more information about the stock.

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
[_tele_openai_bot.py_](https://namuan.github.io/tele-muninn/tele_openai_bot.html)
```
usage: tele_openai_bot.py [-h] [-v]

Listen to messages with tt and ii prefix
If a message begins with tt then it'll send a prompt to OpenAI Completion API
If a message begins with ii then it'll send a prompt to OpenAI Image API

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

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
