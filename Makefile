export PROJECTNAME=$(shell basename "$(PWD)")

.SILENT: ;               # no need for @

setup: ## Setup Virtual Env
	uv sync

deps: ## Install dependencies
	uv sync --all-extras

clean: ## Clean package
	find . -type d -name '__pycache__' | xargs rm -rf
	rm -rf build dist

pre-commit: ## Manually run all precommit hooks
	uv run pre-commit install
	uv run pre-commit run --all-files

pre-commit-tool: ## Manually run a single pre-commit hook
	uv run pre-commit run $(TOOL) --all-files

build: clean pre-commit ## Build package
	echo "✅ Done"

deploy: clean ## Copies any changed file to the server
	ssh ${PROJECTNAME} -C 'bash -l -c "mkdir -vp ./${PROJECTNAME}"'
	rsync -avzr \
		.env \
		pyproject.toml \
		uv.lock \
		requirements \
		scripts \
		secret-keys \
		common_utils.py \
		twitter_api.py \
		yt_api.py \
		webpage_to_pdf.py \
		tele_bookmark_bot.py \
		hn_new_github_repos.py \
		tele_stock_rider_bot.py \
		tele_py_code_runner.py \
		tele_github_context_builder.py \
		webpages.txt \
		tele_web_links.py \
		openai_api.py \
		tele_social_vdo.py \
		muninn-photo-ocr.py \
		muninn-storage.py \
		muninn-web-page-downloader.py \
		muninn-git-repo-downloader.py \
		tele-wiki-tok-bot.py \
		tele_memo.py \
		${PROJECTNAME}:./${PROJECTNAME}

start: deploy ## Sets up a screen session on the server and start the app
	ssh ${PROJECTNAME} -C 'bash -l -c "./${PROJECTNAME}/scripts/setup_jobs.sh"'

stop: deploy ## Stop any running screen session on the server
	ssh ${PROJECTNAME} -C 'bash -l -c "./${PROJECTNAME}/scripts/stop_jobs.sh"'

ssh: ## SSH into the target VM
	ssh ${PROJECTNAME}

syncdatabases: ## Copy databases from remote to local
	rm -rf output_dir/*.db
	rsync -avzr ${PROJECTNAME}:./hn_new_github_repos.* output_dir/
	rsync -avzr ${PROJECTNAME}:./rider_brain.* output_dir/
	rsync -avzr ${PROJECTNAME}:./OutputDir/tele-bookmarks/* output_dir/tele-bookmarks/

bpython: ## Runs bpython
	uv run bpython

.PHONY: help
.DEFAULT_GOAL := help

help: Makefile
	echo
	echo " Choose a command run in "$(PROJECTNAME)":"
	echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	echo
