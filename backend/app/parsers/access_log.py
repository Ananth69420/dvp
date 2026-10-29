import re
from typing import List, Tuple, Optional, Dict, Any
from app.models.schemas import LogEntry
from app.parsers.base import BaseParser, parse_timestamp_iso


class AccessLogParser(BaseParser):
    name: str = "access_log"
    display_name: str = "Web Server Access Log (Nginx / Apache)"
    description: str = "Common/Combined web server logs including IP, HTTP method, path, status code, size, and response duration"

    # Apache/Nginx Combined/Common regex
    # ^(?P<ip>\S+)\s+(?P<identd>\S+)\s+(?P<user>\S+)\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<method>\S+)\s+(?P<path>\S+)(?:\s+(?P<protocol>\S+))?"\s+(?P<status>\d{3})\s+(?P<bytes>\S+)(?:\s+"(?P<referrer>[^"]*)"\s+"(?P<agent>[^"]*)")?(?:\s+(?P<duration>[0-9.]+))?
    REGEX = re.compile(
        r"^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+"
        r'"(?P<method>[A-Z]+)\s+(?P<path>[^\s"]+)(?:\s+[^\s"]+)?"\s+'
        r"(?P<status>\d{3})\s+(?P<bytes>\S+)"
        r'(?:\s+"(?P<referrer>[^"]*)"\s+"(?P<agent>[^"]*)")?'
        r"(?:\s+(?P<duration>[0-9.]+))?"
    )

    def can_parse(self, sample_lines: List[str]) -> float:
        valid_lines = [l.strip() for l in sample_lines if l.strip()]
        if not valid_lines:
            return 0.0
        matches = sum(1 for l in valid_lines[:30] if self.REGEX.match(l))
        return matches / min(len(valid_lines), 30)

    def parse_lines(self, lines: List[str], options: Optional[Dict[str, Any]] = None) -> Tuple[List[LogEntry], List[LogEntry]]:
        parsed: List[LogEntry] = []
        malformed: List[LogEntry] = []

        entry_id = 1
        for idx, line in enumerate(lines, start=1):
            raw = line.rstrip("\r\n")
            if not raw.strip():
                continue

            m = self.REGEX.match(raw)
            if not m:
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
                    error_details="Line does not match Nginx/Apache access log pattern",
                ))
                entry_id += 1
                continue

            gd = m.groupdict()
            ts_str = parse_timestamp_iso(gd.get("timestamp"))
            ip_str = gd.get("ip")
            method_str = gd.get("method")
            path_str = gd.get("path")
            
            try:
                status_code = int(gd.get("status", 0))
            except (ValueError, TypeError):
                status_code = None

            # Infer level from status code
            if status_code is not None:
                if status_code >= 500:
                    level = "ERROR"
                elif status_code >= 400:
                    level = "WARNING"
                else:
                    level = "INFO"
            else:
                level = "INFO"

            # Parse duration: if <= 10.0, assume seconds -> convert to ms; if > 10.0, may already be ms
            dur_val = gd.get("duration")
            response_time_ms = None
            if dur_val:
                try:
                    f = float(dur_val)
                    response_time_ms = f * 1000.0 if f < 100.0 else f
                except ValueError:
                    pass

            msg = f"{method_str} {path_str} -> {status_code}"

            parsed.append(LogEntry(
                id=entry_id,
                timestamp=ts_str,
                level=level,
                service="web-server",
                message=msg,
                source_ip=ip_str,
                http_method=method_str,
                request_path=path_str,
                status_code=status_code,
                response_time_ms=response_time_ms,
                raw_line=raw,
                line_number=idx,
                parse_status="parsed",
                error_details=None,
            ))
            entry_id += 1

        return parsed, malformed

