import os

import pytest


@pytest.mark.skipif(
    os.getenv("RUNNING_UNDER_TOX") is not None, reason="Skip this test under tox."
)
@pytest.mark.failing
def test_get_price_dict() -> None:
    raise NotImplementedError
