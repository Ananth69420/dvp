import re
from typing import List, Tuple, Optional, Dict, Any
from app.models.schemas import LogEntry
from app.parsers.base import BaseParser, normalize_level, parse_timestamp_iso


class AppLogParser(BaseParser):
    name: str = "app_log"
    display_name: str = "Timestamped Application Log"
    description: str = "Standard application logs with timestamp, level, optional [service], and message"

    # Pattern variants:
    # 1. 2026-10-28 10:15:22 INFO [auth-service] Message
    # 2. [2026-10-28 10:15:22] [INFO] [auth-service] Message
    # 3. 2026-10-28 10:15:22.123 [ERROR] auth-service - Message
    PATTERNS = [
        # YYYY-MM-DD HH:MM:SS LEVEL [service] message
        re.compile(
            r"^\[?(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)\]?\s+"
            r"\[?(?P<level>[A-Za-z]+)\]?\s+"
            r"(?:\[(?P<service>[^\]]+)\]|(?P<service2>[a-zA-Z0-9_\-\.]+):|-)?\s*"
            r"(?P<message>.*)$"
        ),
        # YYYY-MM-DD HH:MM:SS [service] LEVEL message
        re.compile(
            r"^\[?(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)\]?\s+"
            r"\[(?P<service>[^\]]+)\]\s+"
            r"\[?(?P<level>[A-Za-z]+)\]?\s*[:-]?\s*"
            r"(?P<message>.*)$"
        ),
    ]

    STATUS_CODE_REGEX = re.compile(r"\b(status(?:_code)?[:= ]|HTTP\s*)?([1-5]\d{2})\b")
    DURATION_REGEX = re.compile(r"\b(?:took|latency|duration|time)[:= ]?\s*([0-9.]+)\s*(ms|s)\b", re.IGNORECASE)
    IP_REGEX = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

    def can_parse(self, sample_lines: List[str]) -> float:
        valid_lines = [line.strip() for line in sample_lines if line.strip()]
        if not valid_lines:
            return 0.0
        
        matches = 0
        for line in valid_lines[:30]:
            if any(p.match(line) for p in self.PATTERNS):
                matches += 1
        return matches / min(len(valid_lines), 30)

    def parse_lines(self, lines: List[str], options: Optional[Dict[str, Any]] = None) -> Tuple[List[LogEntry], List[LogEntry]]:
        parsed: List[LogEntry] = []
        malformed: List[LogEntry] = []

        entry_id = 1
        for idx, line in enumerate(lines, start=1):
            raw = line.rstrip("\r\n")
            if not raw.strip():
                continue

            matched = None
            for p in self.PATTERNS:
                m = p.match(raw)
                if m:
                    matched = m
                    break

            if not matched:
                # Malformed or unparsed line
                malformed_entry = LogEntry(
                    id=entry_id,
                    timestamp=None,
                    level=None,
                    service=None,
                    message=raw,
                    source_ip=None,
                    http_method=None,
                    request_path=None,
                    status_code=None,
                    response_time_ms=None,
                    raw_line=raw,
                    line_number=idx,
                    parse_status="malformed",
                    error_details="Line does not match expected application log timestamp/level structure",
                )
                malformed.append(malformed_entry)
                entry_id += 1
                continue

            gd = matched.groupdict()
            ts_str = parse_timestamp_iso(gd.get("timestamp"))
            level_str = normalize_level(gd.get("level"))
            service_str = (gd.get("service") or gd.get("service2") or "").strip()
            if not service_str:
                service_str = "app"
            message_str = gd.get("message", "").strip()

            # Attempt auxiliary field extraction (status code, duration, IP) if present in message
            status_code = None
            sc_match = self.STATUS_CODE_REGEX.search(message_str)
            if sc_match:
                try:
                    code = int(sc_match.group(2))
                    if 100 <= code <= 599:
                        status_code = code
                except ValueError:
                    pass

            response_time_ms = None
            dur_match = self.DURATION_REGEX.search(message_str)
            if dur_match:
                try:
                    val = float(dur_match.group(1))
                    unit = dur_match.group(2).lower()
                    response_time_ms = val if unit == "ms" else val * 1000.0
                except ValueError:
                    pass

            source_ip = None
            ip_match = self.IP_REGEX.search(message_str)
            if ip_match:
                source_ip = ip_match.group(0)

            entry = LogEntry(
                id=entry_id,
                timestamp=ts_str,
                level=level_str,
                service=service_str,
                message=message_str,
                source_ip=source_ip,
                http_method=None,
                request_path=None,
                status_code=status_code,
                response_time_ms=response_time_ms,
                raw_line=raw,
                line_number=idx,
                parse_status="parsed",
                error_details=None,
            )
            parsed.append(entry)
            entry_id += 1

        return parsed, malformed

