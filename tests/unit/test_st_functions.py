"""Unit tests for st_functions module."""


from price_driven_switch.frontend.st_functions import format_switch_states


class TestFormatSwitchStates:
    """Test suite for format_switch_states function."""

    def test_format_switch_states_with_valid_data(self):
        """Test formatting with valid appliance states data."""
        test_data = {
            "Boiler 1": 1,
            "Boiler 2": 0,
            "Bathroom Floor": 1
        }

        result = format_switch_states(test_data)

        assert "🟢 Boiler 1: ON" in result
        assert "🔴 Boiler 2: OFF" in result
        assert "🟢 Bathroom Floor: ON" in result
        assert result.count("\n") == 2  # Three lines separated by two newlines

    def test_format_switch_states_with_all_on(self):
        """Test formatting when all appliances are on."""
        test_data = {
            "Appliance A": 1,
            "Appliance B": 1
        }

        result = format_switch_states(test_data)

        assert "🟢 Appliance A: ON" in result
        assert "🟢 Appliance B: ON" in result
        assert "OFF" not in result

    def test_format_switch_states_with_all_off(self):
        """Test formatting when all appliances are off."""
        test_data = {
            "Appliance A": 0,
            "Appliance B": 0
        }

        result = format_switch_states(test_data)

        assert "🔴 Appliance A: OFF" in result
        assert "🔴 Appliance B: OFF" in result
        assert "ON" not in result

    def test_format_switch_states_with_empty_data(self):
        """Test formatting with empty data."""
        test_data = {}

        result = format_switch_states(test_data)

        assert result == "⚠️ No appliances configured"

    def test_format_switch_states_with_string_error(self):
        """Test formatting when passed an error string."""
        error_message = "Connection failed"

        result = format_switch_states(error_message)

        assert result == "❌ Error: Connection failed"

    def test_format_switch_states_with_invalid_data_type(self):
        """Test formatting with invalid data type."""
        invalid_data = 123

        result = format_switch_states(invalid_data)

        assert result == "❌ Error: Invalid data format"

    def test_format_switch_states_with_none(self):
        """Test formatting with None data."""
        result = format_switch_states(None)

        assert result == "❌ Error: Invalid data format"

    def test_format_switch_states_preserves_appliance_order(self):
        """Test that appliance order is preserved in output."""
        test_data = {
            "Z Appliance": 1,
            "A Appliance": 0,
            "M Appliance": 1
        }

        result = format_switch_states(test_data)
        lines = result.split("\n")

        # Order should be preserved as provided in the dict
        assert "Z Appliance" in lines[0]
        assert "A Appliance" in lines[1]
        assert "M Appliance" in lines[2]

    def test_format_switch_states_with_special_characters_in_names(self):
        """Test formatting with special characters in appliance names."""
        test_data = {
            "Boiler #1": 1,
            "Floor (Main)": 0,
            "Water Heater - Garage": 1
        }

        result = format_switch_states(test_data)

        assert "🟢 Boiler #1: ON" in result
        assert "🔴 Floor (Main): OFF" in result
        assert "🟢 Water Heater - Garage: ON" in result

    def test_format_switch_states_with_unexpected_state_values(self):
        """Test formatting with unexpected state values (not 0 or 1)."""
        test_data = {
            "Appliance 1": 2,  # Unexpected value
            "Appliance 2": 0,
            "Appliance 3": 1
        }

        result = format_switch_states(test_data)

        # Values other than 1 should be treated as OFF
        assert "🔴 Appliance 1: OFF" in result
        assert "🔴 Appliance 2: OFF" in result
        assert "🟢 Appliance 3: ON" in result
