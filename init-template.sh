#!/usr/bin/env bash

PROJECT=$(basename "$(PWD)")
PACKAGE=$(basename "$(PWD)" | tr '-' '_')

TEMPLATE_PROJECT="$1"
TEMPLATE_PACKAGE="$2"

rm -rf .git .idea .venv .mypy_cache .pytest_cache .cruft.json .coverage poetry.lock CHANGELOG.md
find . -type d -name '__pycache__' -exec rm -rf {} +
rm -rf build dist
mv src/"$TEMPLATE_PACKAGE" src/"$PACKAGE" || true
find . -type f ! -iname "Makefile" -exec sed -i "" "s/$TEMPLATE_PROJECT/$PROJECT/g" {} +
find . -type f ! -iname "Makefile" -exec sed -i "" "s/$TEMPLATE_PACKAGE/$PACKAGE/g" {} +
