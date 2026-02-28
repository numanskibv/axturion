import logging


def test_sensitive_fields_are_redacted(capsys):
    from app.core.structured_logging import configure_logging

    configure_logging()

    logger = logging.getLogger("test.redaction")
    logger.info(
        "user_login email=test@example.com password=abc",
        extra={
            "email": "test@example.com",
            "password": "abc",
        },
    )

    captured = capsys.readouterr()
    output = (captured.err or "") + (captured.out or "")

    assert "***REDACTED***" in output
    assert "test@example.com" not in output
    assert "password=abc" not in output
    assert '"password": "abc"' not in output
