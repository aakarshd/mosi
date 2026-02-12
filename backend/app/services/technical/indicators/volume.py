"""Volume analysis — current volume vs N-day average."""


def compute_volume_ratio(volumes: list[float], avg_period: int = 20) -> float:
    """Compute ratio of current volume to N-day average volume.

    Args:
        volumes: Volume data (oldest first).
        avg_period: Period for average calculation.

    Returns:
        Ratio (e.g., 1.5 means 50% above average). Returns 0 if insufficient data.
    """
    if len(volumes) < 2:
        return 0.0

    current = volumes[-1]
    history = volumes[-avg_period - 1:-1] if len(volumes) > avg_period else volumes[:-1]

    if not history:
        return 0.0

    avg = sum(history) / len(history)
    return current / avg if avg > 0 else 0.0
