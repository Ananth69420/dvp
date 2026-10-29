from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import re
from app.models.schemas import LogEntry

# Standard level mapping
SEVERITY_MAP = {
    "DEBUG": "DEBUG",
    "DBG": "DEBUG",
    "TRACE": "DEBUG",
    "INFO": "INFO",
    "INF": "INFO",
    "NOTICE": "INFO",
    "WARN": "WARNING",
    "WARNING": "WARNING",
    "ERR": "ERROR",
    "ERROR": "ERROR",
    "CRIT": "CRITICAL",
    "CRITICAL": "CRITICAL",
    "FATAL": "CRITICAL",
    "EMERG": "CRITICAL",
    "ALERT": "CRITICAL",
}


def normalize_level(raw_level: Optional[str]) -> Optional[str]:
    if not raw_level:
        return None
    cleaned = raw_level.strip().upper().strip("[](){}:- ")
    return SEVERITY_MAP.get(cleaned, cleaned if cleaned in SEVERITY_MAP.values() else "INFO")


def parse_timestamp_iso(raw_ts: Optional[str]) -> Optional[str]:
    """Parse various timestamp strings into ISO 8601 string YYYY-MM-DDTHH:MM:SS."""
    if not raw_ts:
        return None
    raw_ts = raw_ts.strip().strip("[]")
    
    # Python-style comma milliseconds: 2026-10-28 10:15:22,100
    if "," in raw_ts:
        raw_ts = raw_ts.replace(",", ".")

    formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%b/%Y:%H:%M:%S %z",
        "%d/%b/%Y:%H:%M:%S",
        "%b %d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(raw_ts, fmt)
            # If year missing (like syslog "%b %d %H:%M:%S"), set current year
            if dt.year == 1900:
                dt = dt.replace(year=datetime.now().year)
            return dt.isoformat()
        except (ValueError, TypeError):
            continue

    return None


class BaseParser(ABC):
    name: str = "base"
    display_name: str = "Base Parser"
    description: str = ""

    @abstractmethod
    def can_parse(self, sample_lines: List[str]) -> float:
        """Returns confidence score between 0.0 and 1.0 indicating fit for sample lines."""
        pass

    @abstractmethod
    def parse_lines(self, lines: List[str], options: Optional[Dict[str, Any]] = None) -> Tuple[List[LogEntry], List[LogEntry]]:
        """
        Parses list of lines.
        Returns (parsed_entries, malformed_entries).
        """
        pass

