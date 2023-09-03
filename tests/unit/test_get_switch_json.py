from price_driven_switch.__main__ import (
    check_on_off,
    get_current_price_ratio,
    get_switch_states,
)


def test_get_current_price_ratio(api_response_fixture) -> None:
    assert isinstance(get_current_price_ratio(api_response_fixture), float)


def test_get_switch_states(
    mock_get_current_price_ratio,
    mock_load_setpoints,
    mock_get_switch_states,
    api_response_fixture,
) -> None:
    assert isinstance(get_switch_states(api_response_fixture), dict)
    assert get_switch_states(api_response_fixture) == mock_get_switch_states


def test_check_price_level() -> None:
    assert check_on_off(setpoint=0.5, curr_price_ratio=0.6) is False
    assert check_on_off(setpoint=0.9, curr_price_ratio=0.8) is True
