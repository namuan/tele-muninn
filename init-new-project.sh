#!/usr/bin/env bash

PROJECT=$(basename "$(PWD)")
PACKAGE=$(basename "$(PWD)" | tr '-' '_')

NEW_PROJECT="$1"

cd ..
cp -R "$PROJECT" "$NEW_PROJECT"
cd "$NEW_PROJECT" || echo "Error: Could not find $NEW_PROJECT"
echo "$PWD"
./init-template.sh "$PROJECT" "$PACKAGE"
poetry install
echo "☑️ Nearly done. Run the following command to get started:"
echo "cd $PWD && poetry shell && idea ."
echo "🧠 Also Remember to update the following:"
echo "  - pyproject.toml: Set version under [tool.poetry] and [tool.commitizen] to version = \"0.1.0\""
echo "  - pyproject.toml: Set description in pyproject.toml"
echo "  - README.md: Set title and description"
echo "  - mkdocs.yml: Set site_name"
echo "🧠 Setup Github Repository"
echo "  - Copy origin URL"
echo "🧠 Setup Git"
echo "  - git init"
echo "  - git add ."
echo "  - make pre-commit"
echo "  - git commit -m 'feat: Initial commit'"
echo "  - git remote add origin <..origin..>"
echo "  - git branch -M main"
echo "  - git push -u origin main"
echo "🧠 Add secrets for Github repo"
echo "  - PYPI_TOKEN"
echo "  - PERSONAL_GH_TOKEN" # Required to kickoff another workflow
