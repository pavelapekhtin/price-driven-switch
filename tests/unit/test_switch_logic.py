import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.backend.switch_logic import limit_power, load_appliances_df


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


# Test data
data = {
    "Setpoint": [0.5, 0.5, 0.5],
    "Power": [1.5, 1.0, 0.8],
    "Priority": [2, 1, 3],
    "Group": ["Boilers", "Boilers", ""],
    "on": [True, True, True],
}

index = ["Boiler 1", "Boiler 2", "Floor"]
test_df = pd.DataFrame(data, index=index)
