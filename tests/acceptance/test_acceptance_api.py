from price_driven_switch.__main__ import get_price_dict, get_switch_states


def test_get_price_dict() -> None:
    assert isinstance((get_switch_states(get_price_dict())), dict)
