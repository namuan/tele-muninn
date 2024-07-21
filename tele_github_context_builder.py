#!/usr/bin/env python3
"""
Telegram bot to generate LLM context from GitHub repositories
This script downloads a GitHub repository, extracts it, and builds a context
from specified folder and file types.

Usage:
Run as a telegram bot
./tele_github_context_builder.py -v -v

Single use
./tele_github_context_builder.py -u https://github.com/motion-canvas/motion-canvas/tree/main/packages/docs/docs -t md mdx -v

"""
import logging
import os
import shutil
import tempfile
import zipfile
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

import telegram
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)

from common_utils import retry, setup_logging

load_dotenv()

BOT_TOKEN = os.getenv("DGV82116QE_BOT_TOKEN")

# States
WAITING_FOR_URL, WAITING_FOR_FILTERS = range(2)

# Setup Output Directory
OUTPUT_DIR = os.path.join(os.getcwd(), "output_dir")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_github_url(url):
    """Parse GitHub URL to extract repository URL and folder path."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")

    if len(path_parts) < 2:
        raise ValueError("Invalid GitHub URL")

    repo_url = f"https://github.com/{path_parts[0]}/{path_parts[1]}"

    folder_path = ""
    if len(path_parts) > 4 and path_parts[2] == "tree":
        folder_path = "/".join(path_parts[4:])

    return repo_url, folder_path


def download_github_repo(repo_url, output_dir):
    """Download GitHub repository as a zip file if it doesn't exist."""
    repo_name = os.path.basename(urlparse(repo_url).path)
    zip_url = f"{repo_url}/archive/main.zip"

    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, f"{repo_name}.zip")

    if os.path.exists(zip_path):
        logging.info(f"Zip file already exists at {zip_path}. Skipping download.")
        return zip_path

    try:
        with urlopen(zip_url) as response, open(zip_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        logging.info(f"Repository downloaded to {zip_path}")
    except URLError as e:
        raise Exception(f"Failed to download repository: {str(e)}")

    return zip_path


def extract_zip(zip_path, extract_path):
    """Extract the zip file and return the path to the extracted repository folder."""
    logging.info(f"Extracting zip file: {zip_path}")
    logging.info(f"Extraction path: {extract_path}")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    logging.info("Zip file extracted successfully")

    # Find the extracted repository folder
    repo_name = os.path.splitext(os.path.basename(zip_path))[0]
    logging.info(f"Looking for extracted folder starting with: {repo_name}")

    extracted_folder = None
    for item in os.listdir(extract_path):
        logging.debug(f"Checking item: {item}")
        if item.startswith(repo_name) and item.endswith("-main"):
            extracted_folder = os.path.join(extract_path, item)
            logging.info(f"Found extracted folder: {extracted_folder}")
            break

    if not extracted_folder:
        logging.error(f"Could not find extracted repository folder in {extract_path}")
        logging.debug(f"Contents of {extract_path}:")
        for item in os.listdir(extract_path):
            logging.debug(f"  {item}")
        raise Exception(f"Could not find extracted repository folder in {extract_path}")

    # Rename the folder to remove the '-main' suffix
    renamed_folder = os.path.join(extract_path, repo_name)
    logging.info(f"Renaming {extracted_folder} to {renamed_folder}")

    if os.path.exists(renamed_folder):
        logging.warning(f"Destination folder {renamed_folder} already exists. Removing it.")
        shutil.rmtree(renamed_folder)

    os.rename(extracted_folder, renamed_folder)
    logging.info("Folder renamed successfully")

    return renamed_folder


def collect_files(base_path, folder_path, file_types):
    """Collect files matching the specified types in the given folder and its subdirectories."""
    logging.info(f"Collecting files from base path: {base_path}")
    logging.info(f"Folder path: {folder_path}")
    logging.info(f"File types to collect: {file_types}")

    context = []
    full_path = os.path.join(base_path, folder_path)
    logging.info(f"Full path to search: {full_path}")

    if not os.path.exists(full_path):
        logging.warning(f"Folder not found: {full_path}")
        return context

    logging.info(f"Starting file collection in: {full_path} (including all subdirectories)")

    for root, dirs, files in os.walk(full_path):
        logging.info(f"Searching in directory: {root}")
        logging.debug(f"Subdirectories: {dirs}")
        logging.debug(f"Files in this directory: {files}")

        for file in files:
            logging.debug(f"Checking file: {file}")
            if any(file.endswith(ft) for ft in file_types):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, base_path)
                logging.info(f"Matched file: {relative_path}")
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                    context.append(f"File: {relative_path}\n\n{content}\n\n")
                    logging.info(f"Added content from {relative_path} to context")
                except Exception as e:
                    logging.error(f"Error reading file {file_path}: {str(e)}")
            else:
                logging.debug(f"File {file} does not match specified types")

    logging.info(f"File collection complete. Total files collected: {len(context)}")
    if len(context) == 0:
        logging.warning("No files were added to the context. This may indicate an issue.")
    return context


def generate_output(context, output_dir):
    """Generate an output file with the collected context."""
    output_file = os.path.join(output_dir, "context_output.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(context)
    return output_file


def process_repo(url, file_filters):
    logging.info("Starting GitHub Context Builder")

    try:
        # Parse the GitHub URL
        repo_url, folder_path = parse_github_url(url)
        logging.info(f"Repository URL: {repo_url}")
        logging.info(f"Folder path: {folder_path}")

        # Download the repository if needed
        zip_path = download_github_repo(repo_url, OUTPUT_DIR)

        # Extract the repository
        extracted_path = extract_zip(zip_path, OUTPUT_DIR)
        logging.info(f"Repository extracted to {extracted_path}")

        # Collect files and build context
        context = collect_files(extracted_path, folder_path, file_filters)
        logging.info(f"Collected {len(context)} files")

        shutil.rmtree(extracted_path)
        logging.info(f"Deleted {extracted_path}")

        return "\n".join(context), len(context)

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-b", "--run-as-bot", action="store_true", default=False, help="Run as telegram bot")
    parser.add_argument("-u", "--url", required=False, help="GitHub URL (repository or specific folder)")
    parser.add_argument("-t", "--types", required=False, nargs="+", help="File types to include (e.g., .py .js)")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbose",
        help="Increase verbosity of logging output. Display context variables between each step run",
    )
    return parser.parse_args()


def start(update: Update, _) -> int:
    update.message.reply_text("👋 Welcome! Please send me a GitHub repository URL.")
    return WAITING_FOR_URL


def help_command(update: Update, _) -> None:
    update.message.reply_text("Help: Send a GitHub URL, then provide file filters when prompted.")


@retry(telegram.error.TimedOut, tries=3)
def process_url(update: Update, context: CallbackContext) -> int:
    url = update.message.text
    if not url.startswith("https://github.com/"):
        update.message.reply_text("That doesn't look like a valid GitHub URL. Please try again.")
        return WAITING_FOR_URL

    context.user_data["repo_url"] = url
    update.message.reply_text(
        "Great! Now, please provide file filters (comma-separated file extensions, e.g., .py,.js,.md)"
    )
    return WAITING_FOR_FILTERS


@retry(telegram.error.TimedOut, tries=3)
def process_filters(update: Update, context: CallbackContext) -> int:
    filters = [f.strip() for f in update.message.text.split(",")]
    context.user_data["filters"] = filters

    update.message.reply_text("⚡ Processing the repository. Please wait...")

    try:
        context_content, files_processed = process_repo(context.user_data["repo_url"], filters)

        # Create a temporary file to store the context
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(context_content)
            temp_file_path = temp_file.name

        # Create a zip file containing the context file
        zip_file_path = temp_file_path + ".zip"
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(temp_file_path, arcname="context.txt")

        # Send the zip file as an attachment
        update.message.reply_document(document=open(zip_file_path, "rb"), filename="context.zip")

        # Delete the temporary files
        os.unlink(temp_file_path)
        os.unlink(zip_file_path)

        update.message.reply_text(f"Context size: {len(context_content)}. Files processed: {files_processed}.")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")

    update.message.reply_text("Done. You can send another GitHub URL if you'd like.")
    return WAITING_FOR_URL


def main():
    """Start the bot."""
    logging.info("Starting bot")
    updater = Updater(BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_URL: [MessageHandler(Filters.text & ~Filters.command, process_url)],
            WAITING_FOR_FILTERS: [MessageHandler(Filters.text & ~Filters.command, process_filters)],
        },
        fallbacks=[CommandHandler("help", help_command)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    if args.run_as_bot:
        main()
    else:
        context_content, files_processed = process_repo(args.url, args.types)
        # Generate output file
        output_file = generate_output(context_content, OUTPUT_DIR)
        logging.info(f"Context size: {len(context_content)}. Files process {files_processed}.")
        print(f"Output file generated: {output_file}")
