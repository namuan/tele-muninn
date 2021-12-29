import logging
from dataclasses import dataclass


async def download_web_page(url: str) -> None:
    logging.info("Downloading web page: %s", url)


def _handle_web_page(web_page_url: str) -> str:
    return f"✅ Processed web page: {web_page_url}"


def _process_message(update_message_text: str) -> str:
    if update_message_text.startswith("http"):
        return _handle_web_page(update_message_text)

    return f'Unknown command "{update_message_text}"'


@dataclass
class IncomingMessage:
    text: str


def handle_cmd(incoming_message: IncomingMessage) -> str:
    update_message_text = incoming_message.text
    logging.info("Received message: %s", update_message_text)
    return _process_message(update_message_text)
