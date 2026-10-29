import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from app.config import SAMPLES_DIR


def generate_all_samples():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    base_time = datetime(2026, 10, 28, 8, 0, 0)

    # 1. Application Log (application.log)
    app_log_path = SAMPLES_DIR / "application.log"
    services = ["auth-service", "payment-service", "order-api", "inventory-service", "database-service"]
    levels = ["INFO", "INFO", "INFO", "WARNING", "ERROR", "DEBUG"]

    app_lines = [
        "# SYNTHETIC SAMPLE LOG: Timestamped Microservices Application",
        "# Created for Data Visualization Project demonstration",
    ]
    cur_time = base_time
    for i in range(120):
        cur_time += timedelta(seconds=random.randint(15, 65))
        ts_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        svc = random.choice(services)
        
        # Inject error burst around minute 30-45
        if 30 <= cur_time.minute <= 45 and svc in ["database-service", "payment-service"]:
            lvl = "ERROR" if random.random() < 0.75 else "WARNING"
            if svc == "database-service":
                msg = random.choice([
                    "Connection pool exhausted (max_connections=50)",
                    "Timeout waiting for query lock on table 'orders'",
                    "Deadlock detected during batch update",
                ])
            else:
                msg = random.choice([
                    "Payment gateway timeout after 5000ms",
                    "Invalid merchant signature token",
                    "Transaction 504 Gateway Timeout",
                ])
        else:
            lvl = random.choice(levels)
            if lvl == "INFO":
                msg = random.choice([
                    "User authentication successful",
                    "Processed order submission successfully",
                    "Cache hit for key 'product_catalog_44'",
                    "Health check probe healthy",
                ])
            elif lvl == "WARNING":
                msg = random.choice([
                    "Rate limit approaching threshold (85%)",
                    "Disk write latency higher than normal (120ms)",
                    "Retry attempt 2 of 3 for upstream RPC",
                ])
            elif lvl == "ERROR":
                msg = "Upstream socket closed prematurely"
            else:
                msg = "Debug payload serialization complete"

        app_lines.append(f"{ts_str} {lvl} [{svc}] {msg}")

        # Inject malformed lines periodically
        if i == 25:
            app_lines.append("MALFORMED_ENTRY_NO_TIMESTAMP_OR_LEVEL ::: raw dump error stack corrupt buffer")
        if i == 70:
            app_lines.append(">>> CORRUPTED TRUNCATED PACKET: 0x9948271048201 <<<")

    with open(app_log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(app_lines))

    # 2. Python App Log with Multiline Stack Traces (python_app.log)
    py_log_path = SAMPLES_DIR / "python_app.log"
    py_lines = [
        "# SYNTHETIC SAMPLE LOG: Python Application with Tracebacks",
        "# Created for Data Visualization Project demonstration",
    ]
    cur_time = base_time
    for i in range(90):
        cur_time += timedelta(seconds=random.randint(20, 80))
        ts_str = cur_time.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        svc = random.choice(["api_gateway", "worker_celery", "ml_inference", "user_service"])
        
        if i in [14, 38, 62]:
            # Multiline traceback!
            py_lines.append(f"{ts_str} - {svc} - ERROR - Unhandled exception during request dispatch")
            py_lines.append("Traceback (most recent call last):")
            py_lines.append('  File "/var/app/handlers/dispatch.py", line 142, in process_event')
            py_lines.append("    result = await target_worker.execute(payload)")
            py_lines.append('  File "/var/app/workers/target.py", line 88, in execute')
            py_lines.append("    raise ConnectionRefusedError('Backend Redis cluster unreachable on port 6379')")
            py_lines.append("ConnectionRefusedError: Backend Redis cluster unreachable on port 6379")
        elif i in [22, 54]:
            py_lines.append(f"{ts_str} - {svc} - ERROR - KeyError: 'user_permissions'")
            py_lines.append("Traceback (most recent call last):")
            py_lines.append('  File "/var/app/auth/middleware.py", line 55, in check_auth')
            py_lines.append("    role = claims['user_permissions']['role']")
            py_lines.append("KeyError: 'user_permissions'")
        elif i == 45:
            # Malformed line
            py_lines.append("??? BROKEN SYS LOG LINE WITHOUT PROPER PYTHON FORMATTING ???")
        else:
            lvl = random.choice(["INFO", "INFO", "WARNING", "DEBUG"])
            msg = f"Task worker loop executed iteration {i}" if lvl == "INFO" else "Memory footprint above 400MB threshold"
            py_lines.append(f"{ts_str} - {svc} - {lvl} - {msg}")

    with open(py_log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(py_lines))

    # 3. Web Access Log (web_access.log)
    web_log_path = SAMPLES_DIR / "web_access.log"
    web_lines = [
        "# SYNTHETIC SAMPLE LOG: Nginx / Apache Access Log",
        "# Created for Data Visualization Project demonstration",
    ]
    endpoints = [
        ("/api/v1/login", "POST", [200, 200, 401, 401, 500]),
        ("/api/v1/orders", "GET", [200, 200, 200, 504]),
        ("/api/v1/products", "GET", [200, 200, 304, 200]),
        ("/checkout", "POST", [200, 400, 500, 200]),
        ("/wp-login.php", "GET", [404, 404, 403]),
        ("/static/bundle.js", "GET", [200, 304, 200]),
    ]
    cur_time = base_time
    for i in range(150):
        cur_time += timedelta(seconds=random.randint(10, 40))
        ts_str = cur_time.strftime("%d/%b/%Y:%H:%M:%S +0000")
        ip = f"192.168.{random.randint(1, 10)}.{random.randint(10, 250)}"
        path, method, codes = random.choice(endpoints)
        code = random.choice(codes)
        bytes_sent = random.randint(200, 8500)
        # Latency in seconds
        duration = round(random.uniform(0.015, 0.450) if code < 500 else random.uniform(2.5, 6.2), 3)

        web_lines.append(
            f'{ip} - - [{ts_str}] "{method} {path} HTTP/1.1" {code} {bytes_sent} "https://company.org" "Mozilla/5.0" {duration}'
        )

        if i == 50:
            web_lines.append("MALFORMED INCOMPLETE ACCESS RECORD 400 BAD_REQUEST")

    with open(web_log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(web_lines))

    # 4. JSON Lines Log (service_events.jsonl)
    json_log_path = SAMPLES_DIR / "service_events.jsonl"
    json_lines = []
    cur_time = base_time
    import json as py_json
    for i in range(110):
        cur_time += timedelta(seconds=random.randint(15, 60))
        lvl = random.choice(["INFO", "INFO", "WARNING", "ERROR"])
        svc = random.choice(["billing-engine", "notification-hub", "search-indexer", "analytics-pipeline"])
        duration_ms = round(random.uniform(12.5, 340.0) if lvl != "ERROR" else random.uniform(800.0, 4500.0), 1)
        
        status_code = 200 if lvl == "INFO" else (429 if lvl == "WARNING" else random.choice([500, 502, 504]))

        item = {
            "timestamp": cur_time.isoformat(),
            "level": lvl,
            "service": svc,
            "message": f"Processed batch event #{i} for entity" if lvl != "ERROR" else "Circuit breaker OPEN: backend query timeout",
            "status_code": status_code,
            "response_time_ms": duration_ms,
            "source_ip": f"10.0.{random.randint(1, 5)}.{random.randint(10, 100)}",
            "request_path": f"/services/{svc}/process",
            "http_method": "POST",
        }
        json_lines.append(py_json.dumps(item))

        if i == 33:
            json_lines.append("{CORRUPT_JSON_SYNTAX_LINE: missing_quotes_or_braces,")

    with open(json_log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(json_lines))

    # 5. CSV Log (system_audit.csv)
    csv_log_path = SAMPLES_DIR / "system_audit.csv"
    csv_lines = [
        "timestamp,severity,service,message,source_ip,status_code,latency_ms",
    ]
    cur_time = base_time
    for i in range(100):
        cur_time += timedelta(seconds=random.randint(20, 75))
        ts_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        sev = random.choice(["INFO", "INFO", "WARN", "ERR", "CRIT"])
        svc = random.choice(["audit-logger", "rbac-service", "key-vault", "cluster-mgr"])
        msg = f"Audit log verification checkpoint #{i}" if sev in ["INFO", "WARN"] else "TLS handshake failure with peer node"
        ip = f"172.16.0.{random.randint(1, 50)}"
        code = 200 if sev == "INFO" else (403 if sev == "WARN" else 500)
        lat = round(random.uniform(5.0, 150.0), 1)

        csv_lines.append(f'"{ts_str}","{sev}","{svc}","{msg}","{ip}",{code},{lat}')

        if i == 40:
            csv_lines.append("MALFORMED_CSV_ROW_TOO_FEW_COLUMNS")

    with open(csv_log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(csv_lines))


if __name__ == "__main__":
    generate_all_samples()

