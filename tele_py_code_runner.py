#!/usr/bin/env python3
"""
Telegram bot to run Python code
"""
import os
import re
import subprocess
import tempfile
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from common_utils import setup_logging


class CodeExecutor:
    def __init__(self, code):
        self.code = code

    def parse_and_install_packages(self):
        # Regular expression to find pip install commands
        pip_commands = re.findall(r"#\s*pip\s*install\s*([a-zA-Z0-9\-_]+)", self.code)
        for package in pip_commands:
            print(f"Installing package: {package}")
            subprocess.run(["pip", "install", package], check=True)

    def execute_code(self):
        output = []
        # Write code to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as tmp_file:
            tmp_file.write(self.code)
            tmp_file_path = tmp_file.name

        with subprocess.Popen(
            ["python", tmp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,  # Set to line buffered
            text=True,  # Handles output as text, easier for line reading
        ) as proc:
            try:
                for line in iter(proc.stdout.readline, ""):
                    output.append(line)
            except Exception as e:
                print(e)
            finally:
                proc.stdout.close()

        # Clean up the temporary file
        os.remove(tmp_file_path)
        return "".join(output)

    def run(self):
        self.parse_and_install_packages()
        return self.execute_code()


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-b", "--run-as-bot", action="store_true", default=False, help="Run as telegram bot")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbose",
        help="Increase verbosity of logging output. Display context variables between each step run",
    )
    return parser.parse_args()


def main():
    pass


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    if args.run_as_bot:
        main()
    else:
        test_code = """
# pip install requests
import time
for i in range(3):
    print(f"Sleeping {i+1}")
    time.sleep(1)
print("Finished sleeping.")
    """
        executor = CodeExecutor(test_code)
        output = executor.run()
        print(output)
