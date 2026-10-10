"""Pure helpers for formatting and validating system telemetry values."""
from __future__ import annotations
from typing import Optional, Tuple
import math

NetworkSnapshot = Tuple[int, int, float]


def format_rate(value: float) -> str:
    """Format a non-negative byte rate using binary units."""
    try:
        rate = float(value)
    except (TypeError, ValueError, OverflowError):
        return "Unavailable"
    if rate < 0 or rate != rate or rate == float("inf"):
        return "Unavailable"
    units = ("B/s", "KB/s", "MB/s", "GB/s", "TB/s")
    unit = 0
    while rate >= 1024 and unit < len(units) - 1:
        rate /= 1024
        unit += 1
    return f"{rate:.1f} {units[unit]}"


def network_rates(
    received: object,
    sent: object,
    now: object,
    previous: Optional[NetworkSnapshot],
) -> tuple[float, float, Optional[NetworkSnapshot]]:
    """Return RX/TX byte rates and a safe snapshot for the next sample.

    Invalid samples do not poison the baseline. Counter resets and monotonic
    clock regressions yield zero for that interval rather than negative or
    implausibly large rates.
    """
    try:
        rx_count = int(received)
        tx_count = int(sent)
        timestamp = float(now)
    except (TypeError, ValueError, OverflowError):
        return 0.0, 0.0, previous
    if rx_count < 0 or tx_count < 0 or not math.isfinite(timestamp):
        return 0.0, 0.0, previous

    current: NetworkSnapshot = (rx_count, tx_count, timestamp)
    if previous is None:
        return 0.0, 0.0, current
    try:
        old_rx, old_tx, old_time = previous
        old_rx, old_tx, old_time = int(old_rx), int(old_tx), float(old_time)
    except (TypeError, ValueError, OverflowError):
        return 0.0, 0.0, current
    if old_rx < 0 or old_tx < 0 or not math.isfinite(old_time):
        return 0.0, 0.0, current

    elapsed = timestamp - old_time
    if elapsed <= 0:
        return 0.0, 0.0, current
    rx = max(0, rx_count - old_rx) / elapsed
    tx = max(0, tx_count - old_tx) / elapsed
    return rx, tx, current


def parse_gpu_output(output: object) -> tuple[str, int]:
    """Parse the first NVIDIA-SMI CSV row; never substitute guessed values.

    Expected columns are utilization.gpu and temperature.gpu, without units.
    Missing devices, malformed output, and N/A sensor values are unavailable.
    """
    if not isinstance(output, str):
        return "Unavailable (invalid GPU telemetry)", 0
    for line in output.splitlines():
        columns = [part.strip() for part in line.split(",")]
        if len(columns) < 2:
            continue
        try:
            utilization = float(columns[0])
            temperature = float(columns[1])
        except (TypeError, ValueError, OverflowError):
            continue
        if not math.isfinite(utilization) or not math.isfinite(temperature):
            continue
        if not 0 <= utilization <= 100 or temperature < 0:
            continue
        return (f"{utilization:.0f}% · {temperature:.0f} °C", int(utilization))
    return "Unavailable (no supported GPU telemetry)", 0


def bounded_percent(value: object) -> int:
    """Convert a telemetry percentage into a safe 0..100 integer."""
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    if number != number or number in (float("inf"), float("-inf")):
        return 0
    return int(max(0, min(100, number)))
