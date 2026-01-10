# tele-muninn

Collection of Telegram bots

![](muninn-logo.jpg)

> Acrylic Paint of Muninn, Aerial View, in the style of Ancient Egyptian Art

![](docs/flow.png)

###### Setting up python3 and dependencies with VirtualEnv

```
 make setup
```

### Scripts

<!-- START makefile-doc -->
tele_py_code_runner.py
```
usage: tele_py_code_runner.py [-h] [-b] [-v]

Telegram bot to run Python code

options:
  -h, --help        show this help message and exit
  -b, --run-as-bot  Run as telegram bot
  -v, --verbose     Increase verbosity of logging output. Display context
                    variables between each step run

```
muninn-photo-ocr.py
```
Running Muninn-OCR
usage: muninn-photo-ocr.py [-h] -d DATABASE_FILE_PATH [-b] [-v]

options:
  -h, --help            show this help message and exit
  -d, --database-file-path DATABASE_FILE_PATH
                        Path to database file
  -b, --batch           Run in batch mode (no scheduling, just run once)
  -v, --verbose         Increase verbosity of logging output. Display context
                        variables between each step run

```
muninn-storage.py
```
Running Muninn-Storage
usage: muninn-storage.py [-h] -d DATABASE_FILE_PATH -t TOKEN_FILE [-b] [-v]

Copy local files to GDrive remote storage

options:
  -h, --help            show this help message and exit
  -d, --database-file-path DATABASE_FILE_PATH
                        Path to database file
  -t, --token-file TOKEN_FILE
                        Token file for authenticated GDrive access
  -b, --batch           Run in batch mode (no scheduling, just run once)
  -v, --verbose         Increase verbosity of logging output. Display context
                        variables between each step run

```
tele-wiki-tok-bot.py
```
usage: tele-wiki-tok-bot.py [-h] [--db DB] [-v]

Wikipedia TikTok-style Telegram bot

options:
  -h, --help     show this help message and exit
  --db DB        Path to SQLite database file
  -v, --verbose  Increase verbosity (-v, -vv)

```
tele_bookmark_bot.py
```
usage: tele_bookmark_bot.py [-h] [-v]

Bookmark notes, web pages, tweets, youtube videos, and photos.

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
muninn-git-repo-downloader.py
```
Running Muninn-GitRepo-Downloader
usage: muninn-git-repo-downloader.py [-h] -d DATABASE_FILE_PATH [-b] [-v]

Download the snapshot of GitHub repos as a zip file and save it to local file system

options:
  -h, --help            show this help message and exit
  -d, --database-file-path DATABASE_FILE_PATH
                        Path to database file
  -b, --batch           Run in batch mode (no scheduling, just run once)
  -v, --verbose         Increase verbosity of logging output. Display context
                        variables between each step run

```
tele_web_links.py
```
usage: tele_web_links.py [-h] [-v]

Send links to telegram on a schedule

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
imghdr.py
```
--help: *** not found ***

```
muninn-web-page-downloader.py
```
Running Muninn-WebPage-Downloader
usage: muninn-web-page-downloader.py [-h] -d DATABASE_FILE_PATH [-b] [-v]

Download web page using puppeteer and save it to local file system

options:
  -h, --help            show this help message and exit
  -d, --database-file-path DATABASE_FILE_PATH
                        Path to database file
  -b, --batch           Run in batch mode (no scheduling, just run once)
  -v, --verbose         Increase verbosity of logging output. Display context
                        variables between each step run

```
twitter-fetch.py
```
usage: twitter-fetch.py [-h] -i INPUT

Download video from tweet url

options:
  -h, --help         show this help message and exit
  -i, --input INPUT  Twitter Url

```
tele_pathy.py
```

```
tele_social_vdo.py
```
usage: tele_social_vdo.py [-h] [-i INPUT_URL] [-b] [-v]

Telegram bot to download videos from social media websites

options:
  -h, --help            show this help message and exit
  -i, --input-url INPUT_URL
                        Input url
  -b, --run-as-bot      Run as telegram bot
  -v, --verbose         Increase verbosity of logging output. Display context
                        variables between each step run

```
tele_memo.py
```
usage: tele_memo.py [-h] [-v] [-i] [-s SOURCE]

Spaced Repetition using Telegram Bot

options:
  -h, --help           show this help message and exit
  -v, --verbose        Increase verbosity of logging output
  -i, --import-anki    Import Question Answers from Anki Exported XML file
  -s, --source SOURCE  QA Database

```
hn_new_github_repos.py
```
Running HN GitHub Repos
usage: hn_new_github_repos.py [-h] [-b] [-v]

Find Links to Github/GitLab and Bitbucket from HN new news
Send links over Telegram

Usage:
./hn_new_github_repos.py -h

options:
  -h, --help     show this help message and exit
  -b, --batch    Run in batch mode (no scheduling, just run once)
  -v, --verbose  Increase verbosity of logging output. Display context
                 variables between each step run

```
tele_research_agent.py
```

```
twitter_furus.py
```
usage: twitter_furus.py [-h] [-v]

Fetch tweets from a list of twitter accounts and send the tweets to a telegram group
It also generates a chart for the stock symbol mentioned in the tweet

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
tele_stock_rider_bot.py
```
usage: tele_stock_rider_bot.py [-h] [-v]

Listen to messages with a stock ticker starting with a $ sign and reply with a chart.
It also sends a messages with links to various websites with more information about the stock.

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity of logging output

```
tele_github_context_builder.py
```
usage: tele_github_context_builder.py [-h] [-b] [-u URL]
                                      [-t TYPES [TYPES ...]] [-v]

Telegram bot to generate LLM context from GitHub repositories
This script downloads a GitHub repository, extracts it, and builds a context
from specified folder and file types.

Usage:
Run as a telegram bot
./tele_github_context_builder.py -v -v

Single use
./tele_github_context_builder.py -u https://github.com/motion-canvas/motion-canvas/tree/main/packages/docs/docs -t md mdx -v

options:
  -h, --help            show this help message and exit
  -b, --run-as-bot      Run as telegram bot
  -u, --url URL         GitHub URL (repository or specific folder)
  -t, --types TYPES [TYPES ...]
                        File types to include (e.g., .py .js)
  -v, --verbose         Increase verbosity of logging output. Display context
                        variables between each step run

```
twitter-threads.py
```

```
<!-- END makefile-doc -->

### Development

Run `make deps` to update dependencies

Run `make pre-commit` to all the pre-commit hooks

Commit and push all the changes
