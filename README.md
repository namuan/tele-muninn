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
[_tele-social-vdo.py_](https://namuan.github.io/tele-muninn/tele-social-vdo.html)
```
usage: tele-social-vdo.py [-h] [-i INPUT_URL] [-b] [-v]

Telegram bot to download videos from social media websites

options:
  -h, --help            show this help message and exit
  -i INPUT_URL, --input-url INPUT_URL
                        Input url
  -b, --run-as-bot      Run as telegram bot
  -v, --verbose         Increase verbosity of logging output. Display context
                        variables between each step run

```
[_muninn-storage.py_](https://namuan.github.io/tele-muninn/muninn-storage.html)
```
Running Muninn-Storage
usage: muninn-storage.py [-h] -d DATABASE_FILE_PATH -t TOKEN_FILE [-b] [-v]

Copy local files to GDrive remote storage

options:
  -h, --help            show this help message and exit
  -d DATABASE_FILE_PATH, --database-file-path DATABASE_FILE_PATH
                        Path to database file
  -t TOKEN_FILE, --token-file TOKEN_FILE
                        Token file for authenticated GDrive access
  -b, --batch           Run in batch mode (no scheduling, just run once)
  -v, --verbose         Increase verbosity of logging output. Display context
                        variables between each step run

```
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
[_muninn-web-page-downloader.py_](https://namuan.github.io/tele-muninn/muninn-web-page-downloader.html)
```
Running Muninn-WebPage-Downloader
usage: muninn-web-page-downloader.py [-h] -d DATABASE_FILE_PATH [-b] [-v]

Download web page using puppeteer and save it to local file system

options:
  -h, --help            show this help message and exit
  -d DATABASE_FILE_PATH, --database-file-path DATABASE_FILE_PATH
                        Path to database file
  -b, --batch           Run in batch mode (no scheduling, just run once)
  -v, --verbose         Increase verbosity of logging output. Display context
                        variables between each step run

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

### Development

Run `make deps` to update dependencies

Run `make pre-commit` to all the pre-commit hooks

Commit and push all the changes
