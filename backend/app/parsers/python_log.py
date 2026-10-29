import re
from typing import List, Tuple, Optional, Dict, Any
from app.models.schemas import LogEntry
from app.parsers.base import BaseParser, normalize_level, parse_timestamp_iso


class PythonLogParser(BaseParser):
    name: str = "python_log"
    display_name: str = "Python Logging (with Multiline Stack Traces)"
    description: str = "Standard Python logging format (e.g., asctime - name - levelname - message) with multiline traceback grouping"

    # Pattern: 2026-10-28 10:15:22,100 - auth - INFO - User authenticated
    # Or: 2026-10-28 10:15:22,100 [INFO] auth: User authenticated
    HEADER_PATTERNS = [
        re.compile(
            r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:,\d+)?)\s*-\s*"
            r"(?P<service>[^-]+)\s*-\s*"
            r"(?P<level>[A-Za-z]+)\s*-\s*"
            r"(?P<message>.*)$"
        ),
        re.compile(
            r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:,\d+)?)\s+\[(?P<level>[A-Za-z]+)\]\s+"
            r"(?P<service>[^:]+):\s*"
            r"(?P<message>.*)$"
        ),
    ]

    def can_parse(self, sample_lines: List[str]) -> float:
        valid_lines = [l.strip() for l in sample_lines if l.strip()]
        if not valid_lines:
            return 0.0
        matches = 0
        for l in valid_lines[:30]:
            if any(p.match(l) for p in self.HEADER_PATTERNS):
                matches += 1
        return matches / min(len(valid_lines), 30)

    def parse_lines(self, lines: List[str], options: Optional[Dict[str, Any]] = None) -> Tuple[List[LogEntry], List[LogEntry]]:
        parsed: List[LogEntry] = []
        malformed: List[LogEntry] = []

        entry_id = 1
        current_entry: Optional[LogEntry] = None

        for idx, line in enumerate(lines, start=1):
            raw = line.rstrip("\r\n")
            if not raw.strip() and not current_entry:
                continue

            matched = None
            for p in self.HEADER_PATTERNS:
                m = p.match(raw)
                if m:
                    matched = m
                    break

            if matched:
                # Flush previous entry if any
                if current_entry:
                    parsed.append(current_entry)
                    current_entry = None

                gd = matched.groupdict()
                ts_str = parse_timestamp_iso(gd.get("timestamp"))
                level_str = normalize_level(gd.get("level"))
                service_str = gd.get("service", "python").strip()
                message_str = gd.get("message", "").strip()

                current_entry = LogEntry(
                    id=entry_id,
                    timestamp=ts_str,
                    level=level_str,
                    service=service_str,
                    message=message_str,
                    source_ip=None,
                    http_method=None,
                    request_path=None,
                    status_code=None,
                    response_time_ms=None,
                    raw_line=raw,
                    line_number=idx,
                    parse_status="parsed",
                    error_details=None,
                )
                entry_id += 1
            else:
                # Multiline continuation (e.g. stack trace or wrapped message)
                if current_entry is not None:
                    current_entry.raw_line += "\n" + raw
                    current_entry.message = (current_entry.message or "") + "\n" + raw
                else:
                    # Line without header and no current entry => malformed
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
                        error_details="Orphan line without Python log header pattern",
                    )
                    malformed.append(malformed_entry)
                    entry_id += 1

        if current_entry:
            parsed.append(current_entry)

        return parsed, malformed

