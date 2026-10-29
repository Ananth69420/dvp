import json
from typing import List, Tuple, Optional, Dict, Any
from app.models.schemas import LogEntry
from app.parsers.base import BaseParser, normalize_level, parse_timestamp_iso


class JsonLogParser(BaseParser):
    name: str = "json_log"
    display_name: str = "JSON Lines Log (JSONL)"
    description: str = "One JSON object per line with automatic schema mapping for timestamp, level, service, message, etc."

    # Priority key aliases
    TIMESTAMP_KEYS = ["timestamp", "@timestamp", "time", "ts", "datetime", "date"]
    LEVEL_KEYS = ["level", "severity", "loglevel", "log_level", "type"]
    SERVICE_KEYS = ["service", "app", "application", "component", "logger", "module", "service_name"]
    MESSAGE_KEYS = ["message", "msg", "log", "text", "error", "event"]
    STATUS_KEYS = ["status_code", "status", "http_status", "response_code", "code"]
    DURATION_KEYS = ["response_time_ms", "duration_ms", "latency_ms", "response_time", "duration", "latency", "elapsed"]
    IP_KEYS = ["source_ip", "client_ip", "remote_ip", "ip", "remote_addr"]
    METHOD_KEYS = ["http_method", "method", "verb"]
    PATH_KEYS = ["request_path", "path", "url", "uri", "endpoint"]

    def can_parse(self, sample_lines: List[str]) -> float:
        valid_lines = [l.strip() for l in sample_lines if l.strip()]
        if not valid_lines:
            return 0.0
        json_count = 0
        for l in valid_lines[:30]:
            if (l.startswith("{") and l.endswith("}")) or (l.startswith("[") and l.endswith("]")):
                try:
                    json.loads(l)
                    json_count += 1
                except Exception:
                    pass
        return json_count / min(len(valid_lines), 30)

    def _find_field(self, data: Dict[str, Any], candidate_keys: List[str]) -> Any:
        for k in candidate_keys:
            if k in data and data[k] is not None:
                return data[k]
            # case-insensitive check
            for actual_k in data.keys():
                if actual_k.lower() == k.lower() and data[actual_k] is not None:
                    return data[actual_k]
        return None

    def parse_lines(self, lines: List[str], options: Optional[Dict[str, Any]] = None) -> Tuple[List[LogEntry], List[LogEntry]]:
        parsed: List[LogEntry] = []
        malformed: List[LogEntry] = []

        entry_id = 1
        for idx, line in enumerate(lines, start=1):
            raw = line.rstrip("\r\n")
            if not raw.strip():
                continue

            try:
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError("JSON line is not a dictionary/object")
            except Exception as e:
                malformed.append(LogEntry(
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
                    error_details=f"Invalid JSON: {str(e)}",
                ))
                entry_id += 1
                continue

            # Extract fields
            raw_ts = self._find_field(data, self.TIMESTAMP_KEYS)
            ts_str = parse_timestamp_iso(str(raw_ts)) if raw_ts is not None else None

            raw_level = self._find_field(data, self.LEVEL_KEYS)
            level_str = normalize_level(str(raw_level)) if raw_level is not None else None

            raw_service = self._find_field(data, self.SERVICE_KEYS)
            service_str = str(raw_service).strip() if raw_service is not None else None

            raw_msg = self._find_field(data, self.MESSAGE_KEYS)
            if raw_msg is not None:
                message_str = str(raw_msg)
            else:
                # If no direct message field, summarize data
                message_str = json.dumps(data)

            raw_ip = self._find_field(data, self.IP_KEYS)
            source_ip = str(raw_ip) if raw_ip is not None else None

            raw_method = self._find_field(data, self.METHOD_KEYS)
            http_method = str(raw_method).upper() if raw_method is not None else None

            raw_path = self._find_field(data, self.PATH_KEYS)
            request_path = str(raw_path) if raw_path is not None else None

            status_code = None
            raw_status = self._find_field(data, self.STATUS_KEYS)
            if raw_status is not None:
                try:
                    status_code = int(raw_status)
                except (ValueError, TypeError):
                    pass

            response_time_ms = None
            raw_dur = self._find_field(data, self.DURATION_KEYS)
            if raw_dur is not None:
                try:
                    val = float(raw_dur)
                    # Heuristic: if key name ends in ms, it's ms; if latency < 10.0, probably seconds
                    if "ms" in str(raw_dur).lower() or val > 10.0:
                        response_time_ms = val
                    else:
                        response_time_ms = val * 1000.0
                except (ValueError, TypeError):
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
                raw_line=raw,
                line_number=idx,
                parse_status="parsed",
                error_details=None,
            ))
            entry_id += 1

        return parsed, malformed

