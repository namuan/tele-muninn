cd tele-muninn || exit
pip3 install -r requirements/base.txt --user
bash ./scripts/start_screen.sh rider-brain-bot 'python3 rider_brain_bot.py'
bash ./scripts/start_screen.sh hn-new-github-repos 'python3 hn_new_github_repos.py'
bash ./scripts/start_screen.sh tele-furus 'python3 twitter_furus.py'
bash ./scripts/start_screen.sh tele_stock_rider_bot 'python3 tele_stock_rider_bot.py'
