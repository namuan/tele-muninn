cd tele-muninn || exit
#pip3 install -r requirements/base.txt --user
bash ./scripts/start_screen.sh tele-bookmark-bot 'python3 tele_bookmark_bot.py'
bash ./scripts/start_screen.sh hn-new-github-repos 'python3 hn_new_github_repos.py -v'
#bash ./scripts/start_screen.sh tele-furus 'python3 twitter_furus.py'
bash ./scripts/start_screen.sh tele-stock-rider-bot 'python3 tele_stock_rider_bot.py'
bash ./scripts/start_screen.sh tele-web-links 'python3 tele_web_links.py'
bash ./scripts/start_screen.sh tele-openai-bot 'python3 tele_openai_bot.py'
bash ./scripts/start_screen.sh muninn-storage 'python3 muninn-storage.py --token-file secret-keys/token.json --database-file-path ~/rider_brain.db'
bash ./scripts/start_screen.sh muninn-web-page-downloader 'python3 muninn-web-page-downloader.py --database-file-path ~/rider_brain.db'
bash ./scripts/start_screen.sh muninn-git-repo-downloader 'python3 muninn-git-repo-downloader.py --database-file-path ~/rider_brain.db'
bash ./scripts/start_screen.sh muninn-photo-ocr 'python3 muninn-photo-ocr.py --database-file-path ~/rider_brain.db'
