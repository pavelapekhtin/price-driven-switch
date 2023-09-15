import pandas as pd
import pytest

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.backend.switch_logic import load_appliances_df


@pytest.mark.unit
def test_load_appliances_df(settings_dict_fixture) -> None:
    assert isinstance(load_appliances_df(settings_dict_fixture), pd.DataFrame)
    assert load_appliances_df(settings_dict_fixture).index.name == "Appliance"
    assert load_appliances_df(settings_dict_fixture).columns.equals(
        pd.Index(
            [
                "Setpoint",
                "Power",
                "Priority",
                "Group",
            ]
        )
    )
