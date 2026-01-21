"""
Passive brain health diagnostics module.

This module defines structures and functions to analyze the activity of the brain
process based on the timestamp of the last log entry.

Assumptions:
- Logs for the brain process are written to a file called ``brain.log``.
- Activity is deduced from the timestamps in that log; no action is taken here.
- Functions here are purely observational and return data structures without
  side effects. They do not read or write any files or restart processes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Union


@dataclass
class BrainHealthReport:
    """Structured report describing the health of the brain process."""

    last_log_time: datetime
    """Timestamp of the last observed log entry."""

    status: str
    """Either ``"alive"`` if the brain is considered active or ``"inactive"`` otherwise."""

    inactive_duration: Optional[str] = None
    """Optional human‑readable duration of inactivity (e.g., ``"2 days, 3:04:05"``)."""


def analyze_brain_health(
    last_log_time: Union[str, datetime], *, threshold_hours: float = 24.0
) -> BrainHealthReport:
    """
    Analyze the brain's health based on the timestamp of its last log entry.

    :param last_log_time: A ``datetime`` instance or ISO‑formatted string representing
        the time of the last log entry. If a string is provided it is parsed
        using :func:`datetime.fromisoformat`.
    :param threshold_hours: Number of hours after which the brain is considered
        inactive. Defaults to 24 hours. This value is not used to trigger
        any actions but merely to label the status in the returned report.
    :returns: A :class:`BrainHealthReport` describing the current health status.

    The function makes no external calls and performs no side effects. It
    computes the difference between ``last_log_time`` and the current UTC time.
    If the difference exceeds ``threshold_hours``, the status is marked as
    ``"inactive"``; otherwise, it is marked as ``"alive"``.
    """
    # Normalize the timestamp to a datetime instance
    if isinstance(last_log_time, str):
        try:
            last_log_dt = datetime.fromisoformat(last_log_time)
        except ValueError:
            raise ValueError(
                "last_log_time string must be in ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
    elif isinstance(last_log_time, datetime):
        last_log_dt = last_log_time
    else:
        raise TypeError(
            "last_log_time must be a datetime instance or an ISO-formatted string"
        )

    now = datetime.utcnow()
    delta = now - last_log_dt

    # Determine status based on threshold
    threshold = timedelta(hours=threshold_hours)
    status = "alive" if delta <= threshold else "inactive"

    # Human-readable inactivity duration
    inactive_duration: Optional[str] = None
    if status == "inactive":
        inactive_duration = str(delta)

    return BrainHealthReport(
        last_log_time=last_log_dt,
        status=status,
        inactive_duration=inactive_duration,
    )


__all__ = [
    "BrainHealthReport",
    "analyze_brain_health",
]
