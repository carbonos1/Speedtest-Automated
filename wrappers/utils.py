"""Shared utility helpers for bandwidth conversions and common operations."""
import logging

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'


def setup_logging(level=logging.INFO):
    """Configure root logging with a standard format."""
    logging.basicConfig(level=level, format=LOG_FORMAT)


def bps_to_mbps(bps):
    """Convert bits per second to megabits per second."""
    if bps is None:
        return None
    return bps / 1e6


def Bps_to_mbps(bps):
    """Convert bytes per second to megabits per second (bytes * 8 / 1e6)."""
    if bps is None:
        return None
    return bps / 125000
