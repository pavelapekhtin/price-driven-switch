import os

import pytest

from price_driven_switch.__main__ import get_price_dict, get_switch_states


@pytest.mark.skipif(
    os.getenv("RUNNING_UNDER_TOX") is not None, reason="Skip this test under tox."
)
def test_get_price_dict() -> None:
    assert isinstance((get_switch_states(get_price_dict())), dict)
