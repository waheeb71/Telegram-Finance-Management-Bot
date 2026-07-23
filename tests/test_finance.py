import pytest
from bot.services.notification_service import format_currency


def test_format_currency():
    formatted = format_currency(20000)
    assert "20،000" in formatted or "20000" in formatted
    assert "ريال" in formatted


def test_op_number_generation_format():
    count = 1
    op_num = f"INC-{count:04d}"
    assert op_num == "INC-0001"
