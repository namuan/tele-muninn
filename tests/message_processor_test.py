from ward import test

from tele_muninn.message_processor import IncomingMessage, handle_cmd


@test("Notify user if command is not recognized")
def test_handle_unknown_command() -> None:
    incoming_message = IncomingMessage(text="hi there")
    response_to_user = handle_cmd(incoming_message)
    assert response_to_user == 'Unknown command "hi there"'


@test("Notify user when webpage is processed")
def test_handle_webpage_command() -> None:
    incoming_message = IncomingMessage(text="https://example.com")
    response_to_user = handle_cmd(incoming_message)
    assert response_to_user == "✅ Processed web page: https://example.com"
