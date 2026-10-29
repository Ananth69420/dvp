import csv
import io
from typing import List, Tuple, Optional, Dict, Any
from app.models.schemas import LogEntry
from app.parsers.base import BaseParser, normalize_level, parse_timestamp_iso


class CsvLogParser(BaseParser):
    name: str = "csv_log"
    display_name: str = "CSV / Delimited Log"
    description: str = "Delimited log files (comma, tab, semicolon) with column mapping for timestamps, levels, and messages"

    FIELD_ALIASES = {
        "timestamp": ["timestamp", "time", "date", "datetime", "logged_at", "@timestamp", "ts"],
        "level": ["level", "severity", "loglevel", "log_level", "priority", "status_level"],
        "service": ["service", "app", "application", "component", "logger", "source", "module"],
        "message": ["message", "msg", "log", "text", "description", "event", "details"],
        "source_ip": ["source_ip", "ip", "client_ip", "remote_addr", "remote_ip"],
        "http_method": ["http_method", "method", "verb"],
        "request_path": ["request_path", "path", "endpoint", "url", "uri"],
        "status_code": ["status_code", "status", "http_status", "code", "response_code"],
        "response_time_ms": ["response_time_ms", "latency_ms", "latency", "duration", "duration_ms", "time_taken", "response_time", "elapsed_ms"],
    }

    def can_parse(self, sample_lines: List[str]) -> float:
        valid_lines = [l.strip() for l in sample_lines if l.strip()]
        if len(valid_lines) < 2:
            return 0.0
        
        # Check first line for comma, tab, or semicolon
        header_line = valid_lines[0]
        delimiters = [",", "\t", ";"]
        best_delim = None
        max_cols = 0
        for d in delimiters:
            cols = len(header_line.split(d))
            if cols > max_cols:
                max_cols = cols
                best_delim = d

        if max_cols >= 3:
            # Check if columns look like log headers
            header_lower = header_line.lower()
            matched_aliases = sum(
                1 for aliases in self.FIELD_ALIASES.values() if any(a in header_lower for a in aliases)
            )
            if matched_aliases >= 2:
                return 0.95
            return 0.65
        return 0.0

    def parse_lines(self, lines: List[str], options: Optional[Dict[str, Any]] = None) -> Tuple[List[LogEntry], List[LogEntry]]:
        parsed: List[LogEntry] = []
        malformed: List[LogEntry] = []

        valid_raw_lines = [l for l in lines if l.strip()]
        if not valid_raw_lines:
            return parsed, malformed

        # Determine delimiter
        first_line = valid_raw_lines[0]
        delimiter = ","
        for d in ["\t", ";", ","]:
            if d in first_line and len(first_line.split(d)) >= 3:
                delimiter = d
                break

        custom_mapping = (options or {}).get("column_mapping", {})

        stream = io.StringIO("\n".join(lines))
        reader = csv.reader(stream, delimiter=delimiter)

        headers = None
        try:
            headers = next(reader)
        except StopIteration:
            return parsed, malformed

        # Build column index map
        col_map: Dict[str, int] = {}
        header_cleaned = [h.strip().lower() for h in headers]

        for target_field, aliases in self.FIELD_ALIASES.items():
            if target_field in custom_mapping and custom_mapping[target_field] in header_cleaned:
                col_map[target_field] = header_cleaned.index(custom_mapping[target_field])
            else:
                for idx, h in enumerate(header_cleaned):
                    if h in aliases:
                        col_map[target_field] = idx
                        break

        entry_id = 1
        for line_num, row in enumerate(reader, start=2):
            raw_line = delimiter.join(row)
            if not row or not any(row):
                continue

            if len(row) < len(headers) * 0.5:
                malformed.append(LogEntry(
                    id=entry_id,
                    timestamp=None,
                    level=None,
                    service=None,
                    message=raw_line,
                    source_ip=None,
                    http_method=None,
                    request_path=None,
                    status_code=None,
                    response_time_ms=None,
                    raw_line=raw_line,
                    line_number=line_num,
                    parse_status="malformed",
                    error_details="CSV row column count mismatch with header",
                ))
                entry_id += 1
                continue

            def get_val(field_name: str) -> Optional[str]:
                if field_name in col_map and col_map[field_name] < len(row):
                    val = row[col_map[field_name]].strip()
                    return val if val else None
                return None

            raw_ts = get_val("timestamp")
            ts_str = parse_timestamp_iso(raw_ts) if raw_ts else None

            raw_lvl = get_val("level")
            level_str = normalize_level(raw_lvl) if raw_lvl else None

            service_str = get_val("service")
            message_str = get_val("message") or raw_line
            source_ip = get_val("source_ip")
            http_method = get_val("http_method")
            if http_method:
                http_method = http_method.upper()
            request_path = get_val("request_path")

            status_code = None
            raw_code = get_val("status_code")
            if raw_code:
                try:
                    status_code = int(raw_code)
                except ValueError:
                    pass

            response_time_ms = None
            raw_dur = get_val("response_time_ms")
            if raw_dur:
                try:
                    response_time_ms = float(raw_dur)
                except ValueError:
                    pass

            parsed.append(LogEntry(
                id=entry_id,
                timestamp=ts_str,
                level=level_str,
                service=service_str,
                message=message_str,
                source_ip=source_ip,
                http_method=http_method,
                request_path=request_path,
                status_code=status_code,
                response_time_ms=response_time_ms,
                raw_line=raw_line,
                line_number=line_num,
                parse_status="parsed",
                error_details=None,
            ))
            entry_id += 1

        return parsed, malformed
