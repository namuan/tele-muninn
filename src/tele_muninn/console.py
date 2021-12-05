import logging

from tele_muninn.bot import start_bot

logging.basicConfig(
    handlers=[
        logging.StreamHandler(),
    ],
    format="%(asctime)s - %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logging.captureWarnings(capture=True)


def cli() -> None:
    print("Starting with bot wrapper")
    start_bot()


if __name__ == "__main__":
    cli()
