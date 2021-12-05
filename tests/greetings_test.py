from tele_muninn.greetings import greet


def test_greet() -> None:
    assert greet() == "Hello, world!"
