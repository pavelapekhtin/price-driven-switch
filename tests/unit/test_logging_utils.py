"""
Tests for the improved logging utilities.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from price_driven_switch.backend.logging_utils import (
    StructuredSwitchLogger,
    SwitchLogger,
    format_appliance_list,
    log_if_changed,
    log_switch_decision_summary,
    should_log_state_change,
)


class TestSwitchLogger:
    """Test the SwitchLogger class."""

    @pytest.fixture
    def switch_logger(self):
        """Create a fresh SwitchLogger instance."""
        return SwitchLogger()

    def test_log_price_based_decision_first_time(self, switch_logger):
        """Test logging price decision for the first time."""
        appliance_states = pd.DataFrame(
            {"on": [True, False, True], "Setpoint": [0.3, 0.6, 0.4]},
            index=["Boiler 1", "Boiler 2", "Floor"],
        )

        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            switch_logger.log_price_based_decision(appliance_states, 0.5)
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "[PRICE]" in call_args
            assert "0.500" in call_args
            assert "2/3" in call_args

    def test_log_price_based_decision_no_duplicate(self, switch_logger):
        """Test that similar price decisions don't create duplicate logs."""
        appliance_states = pd.DataFrame(
            {"on": [True, False, True]}, index=["Boiler 1", "Boiler 2", "Floor"]
        )

        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            # First call
            switch_logger.log_price_based_decision(appliance_states, 0.5)
            # Second call with very similar price
            switch_logger.log_price_based_decision(appliance_states, 0.505)

            # Should only log once due to small difference
            assert mock_logger.info.call_count == 1

    def test_log_power_limiting_decision_ok(self, switch_logger):
        """Test logging when power is within limits."""
        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            switch_logger.log_power_limiting_decision(1500, 2.0, "OK")
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "[POWER]" in call_args
            assert "within limit" in call_args
            assert "1500W / 2000W" in call_args

    def test_log_power_limiting_decision_over(self, switch_logger):
        """Test logging when power limit is exceeded."""
        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            switch_logger.log_power_limiting_decision(
                2500, 2.0, "OVER", "reducing load"
            )

            assert mock_logger.info.call_count == 2  # Status + action
            first_call = mock_logger.info.call_args_list[0][0][0]
            assert "exceeded by 500W" in first_call

    def test_log_appliance_state_change_tracks_states(self, switch_logger):
        """Test that appliance state changes are tracked to prevent duplicates."""
        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            # First state change
            switch_logger.log_appliance_state_change("Boiler 1", True, "price", 2.0, 1)
            # Same state change again
            switch_logger.log_appliance_state_change("Boiler 1", True, "price", 2.0, 1)

            # Should only log once
            mock_logger.info.assert_called_once()

    def test_log_system_summary(self, switch_logger):
        """Test system summary logging."""
        final_states = pd.DataFrame(
            {"on": [True, False, True], "Power": [1.5, 1.0, 0.8]},
            index=["Boiler 1", "Boiler 2", "Floor"],
        )

        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            switch_logger.log_system_summary(final_states, 2.3, 3.0, 0.45)

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "[SUMMARY]" in call_args
            assert "2.3/3.0kW" in call_args
            assert "0.450" in call_args
            assert "Boiler 1" in call_args
            assert "Floor" in call_args

    def test_reset_session(self, switch_logger):
        """Test session reset functionality."""
        # Set some state
        switch_logger._last_logged_states["Boiler 1"] = True
        switch_logger._last_power_status = "OVER"

        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            switch_logger.reset_session()

            assert switch_logger._last_logged_states == {}
            assert switch_logger._last_power_status is None
            mock_logger.info.assert_called_with(
                "[SESSION] New switch logic session started"
            )


class TestStructuredSwitchLogger:
    """Test the StructuredSwitchLogger class."""

    @pytest.fixture
    def structured_logger(self):
        """Create a StructuredSwitchLogger instance."""
        return StructuredSwitchLogger()

    def test_log_appliance_turned_off(self, structured_logger):
        """Test logging when appliance is turned off."""
        with patch.object(
            structured_logger.logger, "log_appliance_state_change"
        ) as mock_method:
            structured_logger.log_appliance_turned_off(
                "Boiler 1", 2.0, 1, "power_limit"
            )
            mock_method.assert_called_once_with(
                "Boiler 1", False, "power_limit", 2.0, 1
            )

    def test_log_appliance_turned_on(self, structured_logger):
        """Test logging when appliance is turned on."""
        with patch.object(
            structured_logger.logger, "log_appliance_state_change"
        ) as mock_method:
            structured_logger.log_appliance_turned_on("Floor", 0.8, 3, "power_recovery")
            mock_method.assert_called_once_with("Floor", True, "power_recovery", 0.8, 3)

    def test_log_power_limit_start_over_limit(self, structured_logger):
        """Test logging when starting power limit logic with over-limit condition."""
        prev_states = pd.DataFrame({"on": [True, True, False]}, index=["A", "B", "C"])

        with patch.object(
            structured_logger.logger, "log_power_limiting_decision"
        ) as mock_method:
            structured_logger.log_power_limit_start(2500, 2.0, prev_states)
            mock_method.assert_called_once_with(2500, 2.0, "OVER")

    def test_log_power_limit_start_reserve_available(self, structured_logger):
        """Test logging when reserve power is available."""
        prev_states = pd.DataFrame({"on": [True, False, False]}, index=["A", "B", "C"])

        with patch.object(
            structured_logger.logger, "log_power_limiting_decision"
        ) as mock_method:
            structured_logger.log_power_limit_start(1500, 2.5, prev_states)
            mock_method.assert_called_once()
            args = mock_method.call_args[0]
            assert args[2] == "RESERVE"
            assert "1000W reserve" in args[3]


class TestUtilityFunctions:
    """Test utility functions."""

    def test_format_appliance_list_short(self):
        """Test formatting short appliance list."""
        appliances = ["Boiler 1", "Floor"]
        result = format_appliance_list(appliances)
        assert result == "Boiler 1, Floor"

    def test_format_appliance_list_long(self):
        """Test formatting long appliance list with truncation."""
        appliances = ["Boiler 1", "Boiler 2", "Floor", "Garage", "Lights"]
        result = format_appliance_list(appliances, max_items=3)
        assert result == "Boiler 1, Boiler 2, Floor (+2 more)"

    def test_should_log_state_change_new_appliance(self):
        """Test state change detection for new appliance."""
        result = should_log_state_change("New Boiler", True, {})
        assert result is True

    def test_should_log_state_change_same_state(self):
        """Test state change detection for same state."""
        last_states = {"Boiler 1": True}
        result = should_log_state_change("Boiler 1", True, last_states)
        assert result is False

    def test_should_log_state_change_different_state(self):
        """Test state change detection for different state."""
        last_states = {"Boiler 1": True}
        result = should_log_state_change("Boiler 1", False, last_states)
        assert result is True

    def test_log_if_changed_first_time(self):
        """Test log_if_changed logs message first time."""
        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            log_if_changed("Test message")
            mock_logger.info.assert_called_once_with("Test message")

    def test_log_if_changed_same_message(self):
        """Test log_if_changed doesn't log same message twice."""
        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            log_if_changed("Same message")
            log_if_changed("Same message")
            # Should only be called once
            mock_logger.info.assert_called_once_with("Same message")

    def test_log_switch_decision_summary(self):
        """Test comprehensive switch decision summary logging."""
        price_states = pd.DataFrame(
            {"on": [True, True, False], "Power": [1.5, 1.0, 0.8]},
            index=["Boiler 1", "Boiler 2", "Floor"],
        )

        final_states = pd.DataFrame(
            {"on": [True, False, False], "Power": [1.5, 1.0, 0.8]},
            index=["Boiler 1", "Boiler 2", "Floor"],
        )

        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            log_switch_decision_summary(price_states, final_states, 2000, 2.0, 0.45)

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "[DECISION]" in call_args
            assert "2000W → 1.5kW used / 2.0kW limit" in call_args
            assert "Price: 0.450" in call_args
            assert "Active: 1/3 appliances" in call_args
            assert "Boiler 2 blocked by power limit" in call_args


class TestLoggingIntegration:
    """Test integration of logging components."""

    def test_full_logging_workflow(self):
        """Test complete logging workflow from price decision to final summary."""
        logger = StructuredSwitchLogger()

        # Create test data
        appliance_states = pd.DataFrame(
            {"on": [True, True, True], "Power": [1.5, 1.2, 0.8], "Priority": [1, 2, 3]},
            index=["Boiler 1", "Boiler 2", "Floor"],
        )

        final_states = pd.DataFrame(
            {
                "on": [True, False, True],
                "Power": [1.5, 1.2, 0.8],
                "Priority": [1, 2, 3],
            },
            index=["Boiler 1", "Boiler 2", "Floor"],
        )

        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            # Simulate full workflow
            logger.log_price_logic_result(appliance_states, 0.4)
            logger.log_power_limit_start(2800, 2.5, appliance_states)
            logger.log_appliance_turned_off("Boiler 2", 1.2, 2)
            logger.log_power_limit_complete(final_states, 2.3, 2.5, 0.4)

            # Verify multiple log calls were made
            assert mock_logger.info.call_count >= 3

    def test_no_spam_logging(self):
        """Test that repeated similar states don't spam logs."""
        logger = SwitchLogger()

        appliance_states = pd.DataFrame(
            {"on": [True, False]}, index=["Boiler", "Floor"]
        )

        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            # Log same state multiple times
            for _ in range(5):
                logger.log_price_based_decision(appliance_states, 0.5)
                logger.log_appliance_state_change("Boiler", True, "price", 2.0, 1)

            # Should have minimal log calls due to deduplication
            assert mock_logger.info.call_count <= 2  # One for price, one for appliance

    def test_error_logging(self):
        """Test error logging functionality."""
        logger = StructuredSwitchLogger()

        with patch("price_driven_switch.backend.logging_utils.logger") as mock_logger:
            logger.log_error_state("Test error occurred")

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "[ERROR]" in call_args
            assert "Test error occurred" in call_args
