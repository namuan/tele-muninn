#!/usr/bin/env python3
"""
A simple script to regenerate the token file for the Google Drive API.

Usage:
./google-token.py -s secret-keys/desktop-app-credentials.json -o secret-keys/token.json
"""
import logging
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from common_utils import GDRIVE_SCOPES


def setup_logging(verbosity):
    logging_level = logging.WARNING
    if verbosity == 1:
        logging_level = logging.INFO
    elif verbosity >= 2:
        logging_level = logging.DEBUG

    logging.basicConfig(
        handlers=[
            logging.StreamHandler(),
        ],
        format="%(asctime)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging_level,
    )
    logging.captureWarnings(capture=True)


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument(
        "-s",
        "--secret-file",
        type=Path,
        required=True,
        help="Path to the secret file",
    )
    parser.add_argument(
        "-o",
        "--output-token-file",
        type=Path,
        required=True,
        help="Path to the token file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbose",
        help="Increase verbosity of logging output",
    )
    return parser.parse_args()


def main(args):
    secret_file = args.secret_file
    output_token_file = args.output_token_file
    flow = InstalledAppFlow.from_client_secrets_file(secret_file.as_posix(), GDRIVE_SCOPES)
    creds = flow.run_local_server(port=0)
    output_token_file.write_text(creds.to_json())


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    main(args)
