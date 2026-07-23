import pytest


def test_student_remaining_calc():
    total_required = 100000.0
    paid = 40000.0
    remaining = total_required - paid
    assert remaining == 60000.0
