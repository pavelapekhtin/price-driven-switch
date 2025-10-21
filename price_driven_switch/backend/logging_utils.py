"""
Improved structured logging utilities for the price-driven switch system.
Provides clear, concise, and non-duplicate logging for user-facing status display.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd
from loguru import logger


class LogLevel(Enum):
    """Log levels for switch logic events."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


class EventType(Enum):
    """Types of switch logic events."""

    PRICE_DECISION = "PRICE_DECISION"
    POWER_LIMIT = "POWER_LIMIT"
    APPLIANCE_ON = "APPLIANCE_ON"
    APPLIANCE_OFF = "APPLIANCE_OFF"
    SYSTEM_STATUS = "SYSTEM_STATUS"
    POWER_RECOVERY = "POWER_RECOVERY"
    CONFIGURATION = "CONFIGURATION"


class SwitchLogger:
    """
    Structured logger for switch logic events.
    Provides clear, user-friendly messages while avoiding duplicates.
    """

    def __init__(self) -> None:
        self._last_logged_states: dict[str, bool] = {}
        self._last_power_status: str | None = None
        self._last_price_offset: float | None = None
        self._session_start = datetime.now()

    def log_price_based_decision(
        self, appliance_states: pd.DataFrame, price_offset: float
    ) -> None:
        """Log price-based switching decisions."""
        # Only log if price offset changed significantly or first time
        if (
            self._last_price_offset is None
            or abs(price_offset - self._last_price_offset) > 0.01
        ):
            on_count = sum(appliance_states["on"])
            total_count = len(appliance_states)

            if on_count == 0:
                message = f"Price too high ({price_offset:.3f}) - all appliances OFF"
            elif on_count == total_count:
                message = (
                    f"Price favorable ({price_offset:.3f}) - all appliances allowed ON"
                )
            else:
                on_appliances = appliance_states[appliance_states["on"]].index.tolist()
                message = f"Price moderate ({price_offset:.3f}) - {on_count}/{total_count} appliances allowed: {', '.join(str(app) for app in on_appliances)}"

            logger.info(f"[PRICE] {message}")
            self._last_price_offset = price_offset

    def log_power_limiting_decision(
        self,
        current_power: int,
        power_limit: float,
        action: str,
        details: str | None = None,
    ) -> None:
        """Log power limiting decisions with clear context."""
        power_limit_w = int(power_limit * 1000)

        if action == "OK":
            status = f"Power within limit ({current_power}W / {power_limit_w}W)"
            if self._last_power_status != "OK":
                logger.info(f"[POWER] {status}")
                self._last_power_status = "OK"

        elif action == "OVER":
            excess = current_power - power_limit_w
            status = f"Power limit exceeded by {excess}W ({current_power}W / {power_limit_w}W)"
            logger.info(f"[POWER] {status}")
            if details:
                logger.info(f"[POWER] Action: {details}")
            self._last_power_status = "OVER"

        elif action == "RESERVE":
            reserve = power_limit_w - current_power
            status = f"Power reserve available: {reserve}W ({current_power}W / {power_limit_w}W)"
            logger.info(f"[POWER] {status}")
            if details:
                logger.info(f"[POWER] Action: {details}")
            self._last_power_status = "RESERVE"

    def log_appliance_state_change(
        self,
        appliance_name: str,
        new_state: bool,
        reason: str,
        power_kw: float,
        priority: int,
    ) -> None:
        """Log individual appliance state changes with context."""
        # Only log actual state changes
        if (
            appliance_name not in self._last_logged_states
            or self._last_logged_states[appliance_name] != new_state
        ):
            action = "ON" if new_state else "OFF"
            reason_text = {
                "price": "price conditions",
                "power_limit": "power limit exceeded",
                "power_recovery": "power became available",
                "priority": "priority-based selection",
            }.get(reason, reason)

            message = f"{appliance_name} → {action} ({power_kw}kW, priority {priority}) - {reason_text}"
            logger.info(f"[SWITCH] {message}")

            self._last_logged_states[appliance_name] = new_state

    def log_system_summary(
        self,
        final_states: pd.DataFrame,
        total_power_kw: float,
        power_limit_kw: float,
        price_offset: float,
    ) -> None:
        """Log concise system summary."""
        on_appliances = final_states[final_states["on"]].index.tolist()
        off_appliances = final_states[~final_states["on"]].index.tolist()

        summary_parts = []

        if on_appliances:
            summary_parts.append(f"ON: {', '.join(str(app) for app in on_appliances)}")

        if off_appliances:
            summary_parts.append(
                f"OFF: {', '.join(str(app) for app in off_appliances)}"
            )

        power_status = f"Power: {total_power_kw:.1f}/{power_limit_kw:.1f}kW"
        price_status = f"Price: {price_offset:.3f}"

        summary = " | ".join([power_status, price_status, *summary_parts])
        logger.info(f"[SUMMARY] {summary}")

    def log_configuration_change(self, change_type: str, details: str) -> None:
        """Log configuration changes that affect switch logic."""
        logger.info(f"[CONFIG] {change_type}: {details}")

    def log_error(self, error_message: str, context: str | None = None) -> None:
        """Log errors with context."""
        full_message = f"{error_message}"
        if context:
            full_message += f" - Context: {context}"
        logger.error(f"[ERROR] {full_message}")

    def log_debug_state(self, state_info: dict[str, Any]) -> None:
        """Log detailed debug information."""
        logger.debug(f"[DEBUG] State: {json.dumps(state_info, default=str, indent=2)}")

    def reset_session(self) -> None:
        """Reset session state for fresh logging."""
        self._last_logged_states.clear()
        self._last_power_status = None
        self._last_price_offset = None
        self._session_start = datetime.now()
        logger.info("[SESSION] New switch logic session started")


class StructuredSwitchLogger:
    """
    Enhanced switch logger that provides structured, user-friendly messages
    for display on the Status page with minimal duplication.
    """

    def __init__(self) -> None:
        self.logger = SwitchLogger()

    def log_price_logic_start(self, price_offset: float, appliance_count: int) -> None:
        """Log start of price-based logic evaluation."""
        # Only log if significant change
        pass

    def log_price_logic_result(
        self, appliance_states: pd.DataFrame, price_offset: float
    ) -> None:
        """Log the result of price-based logic."""
        self.logger.log_price_based_decision(appliance_states, price_offset)

    def log_power_limit_start(
        self, current_power: int, power_limit: float, prev_states: pd.DataFrame
    ) -> None:
        """Log start of power limiting logic."""
        # Determine what type of power limiting scenario this is
        if current_power == 0 or power_limit == 0:
            logger.info("[POWER] Power limiting bypassed (zero power or limit)")
        else:
            power_limit_w = int(power_limit * 1000)
            if current_power > power_limit_w:
                self.logger.log_power_limiting_decision(
                    current_power, power_limit, "OVER"
                )
            elif current_power < power_limit_w:
                reserve = power_limit_w - current_power
                if any(prev_states["on"] != True):  # noqa: E712
                    self.logger.log_power_limiting_decision(
                        current_power,
                        power_limit,
                        "RESERVE",
                        f"Checking if appliances can be turned ON with {reserve}W reserve",
                    )
                else:
                    self.logger.log_power_limiting_decision(
                        current_power, power_limit, "OK"
                    )

    def log_appliance_turned_off(
        self,
        appliance_name: str,
        power_kw: float,
        priority: int,
        reason: str = "power_limit",
    ) -> None:
        """Log when an appliance is turned OFF."""
        self.logger.log_appliance_state_change(
            appliance_name, False, reason, power_kw, priority
        )

    def log_appliance_turned_on(
        self,
        appliance_name: str,
        power_kw: float,
        priority: int,
        reason: str = "power_recovery",
    ) -> None:
        """Log when an appliance is turned ON."""
        self.logger.log_appliance_state_change(
            appliance_name, True, reason, power_kw, priority
        )

    def log_power_limit_complete(
        self,
        final_states: pd.DataFrame,
        estimated_power: float,
        power_limit: float,
        price_offset: float,
    ) -> None:
        """Log completion of power limiting with final summary."""
        self.logger.log_system_summary(
            final_states, estimated_power, power_limit, price_offset
        )

    def log_no_action_needed(self, reason: str) -> None:
        """Log when no action is needed."""
        if reason == "power_ok":
            # Don't log - already handled in power_limit_start
            pass
        elif reason == "no_changes":
            # Only log occasionally to avoid spam
            pass

    def log_error_state(self, error_message: str) -> None:
        """Log error states."""
        self.logger.log_error(error_message)

    def get_recent_logs(self, lines: int = 20, level_filter: str = "INFO") -> list[str]:
        """Get recent log entries for display (placeholder for future implementation)."""
        # This would integrate with the log file reading functionality
        # For now, return empty list as the actual log reading is done in the Status page
        return []


# Global structured logger instance
structured_logger = StructuredSwitchLogger()


def log_switch_decision_summary(
    price_states: pd.DataFrame,
    final_states: pd.DataFrame,
    current_power: int,
    power_limit: float,
    price_offset: float,
) -> None:
    """
    Log a comprehensive but concise summary of switching decisions.
    This replaces multiple scattered log statements with one clear summary.
    """
    changes = []

    # Find what changed between price-only and final states
    for appliance in price_states.index:
        price_want = price_states.loc[appliance, "on"]
        final_state = final_states.loc[appliance, "on"]

        if price_want and not final_state:
            changes.append(f"{appliance} blocked by power limit")
        elif not price_want and final_state:
            changes.append(f"{appliance} unexpected ON state")  # Should not happen
        elif price_want and final_state:
            changes.append(f"{appliance} allowed ON")
        # Don't log appliances that stay OFF

    # Create summary message
    total_power = sum(final_states.loc[final_states["on"], "Power"])
    on_count = sum(final_states["on"])

    summary_parts = [
        f"Power: {current_power}W → {total_power:.1f}kW used / {power_limit:.1f}kW limit",
        f"Price: {price_offset:.3f}",
        f"Active: {on_count}/{len(final_states)} appliances",
    ]

    if changes:
        summary_parts.append(f"Changes: {'; '.join(changes[:3])}")  # Limit to 3 changes
        if len(changes) > 3:
            summary_parts.append(f"and {len(changes) - 3} more")

    logger.info(f"[DECISION] {' | '.join(summary_parts)}")


def format_appliance_list(appliances: list[str], max_items: int = 3) -> str:
    """Format appliance list for logging with truncation."""
    if len(appliances) <= max_items:
        return ", ".join(str(app) for app in appliances)
    else:
        shown = ", ".join(str(app) for app in appliances[:max_items])
        remaining = len(appliances) - max_items
        return f"{shown} (+{remaining} more)"


def should_log_state_change(
    appliance: str, new_state: bool, last_states: dict[str, bool]
) -> bool:
    """Determine if a state change should be logged to avoid duplicates."""
    return appliance not in last_states or last_states[appliance] != new_state


# State tracking for duplicate prevention
_last_logged_summary: str | None = None
_last_summary_time: datetime | None = None


def log_if_changed(message: str, min_interval_seconds: int = 30) -> None:
    """Log message only if it has changed or enough time has passed."""
    global _last_logged_summary, _last_summary_time

    now = datetime.now()

    if (
        _last_logged_summary != message
        or _last_summary_time is None
        or (now - _last_summary_time).total_seconds() > min_interval_seconds
    ):
        logger.info(message)
        _last_logged_summary = message
        _last_summary_time = now
