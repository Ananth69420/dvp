import math
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from app.models.schemas import (
    LogEntry,
    LogAnalytics,
    TopErrorItem,
    ServiceStatItem,
    ResponseTimeStats,
    TimeVolumePoint,
    AnomalyItem,
    HeatmapPoint,
)

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class AnalyticsEngine:
    def compute_analytics(self, parsed_entries: List[LogEntry], total_lines: int, malformed_count: int) -> LogAnalytics:
        parsed_count = len(parsed_entries)
        unparsed_count = malformed_count
        success_rate = round((parsed_count / total_lines * 100.0), 2) if total_lines > 0 else 0.0

        if not parsed_entries:
            return LogAnalytics(
                total_lines=total_lines,
                parsed_lines=0,
                unparsed_lines=unparsed_count,
                success_rate=success_rate,
                error_count=0,
                warning_count=0,
                info_count=0,
                debug_count=0,
                critical_count=0,
                distinct_services_count=0,
                most_active_service=None,
                top_errors=[],
                service_stats=[],
                status_code_distribution={},
                response_time_stats=None,
                time_series=[],
                anomalies=[],
                heatmap=[],
                time_range=None,
            )

        # Convert to Pandas DataFrame for vector operations
        records = [
            {
                "id": e.id,
                "timestamp": e.timestamp,
                "level": e.level,
                "service": e.service or "unknown",
                "message": e.message or "",
                "status_code": e.status_code,
                "response_time_ms": e.response_time_ms,
            }
            for e in parsed_entries
        ]
        df = pd.DataFrame(records)

        # Level counts
        level_counts = df["level"].value_counts().to_dict()
        error_count = int(level_counts.get("ERROR", 0))
        critical_count = int(level_counts.get("CRITICAL", 0))
        total_errors = error_count + critical_count
        warning_count = int(level_counts.get("WARNING", 0))
        info_count = int(level_counts.get("INFO", 0))
        debug_count = int(level_counts.get("DEBUG", 0))

        # Services
        service_counts = df["service"].value_counts()
        distinct_services = len(service_counts)
        most_active_service = str(service_counts.index[0]) if not service_counts.empty else None

        # Service breakdown
        service_stats: List[ServiceStatItem] = []
        for service, group in df.groupby("service"):
            s_total = len(group)
            s_levels = group["level"].value_counts().to_dict()
            s_err = int(s_levels.get("ERROR", 0) + s_levels.get("CRITICAL", 0))
            s_warn = int(s_levels.get("WARNING", 0))
            s_info = int(s_levels.get("INFO", 0))
            s_rate = round((s_err / s_total * 100.0), 2) if s_total > 0 else 0.0

            service_stats.append(ServiceStatItem(
                service=str(service),
                total_entries=s_total,
                error_count=s_err,
                warning_count=s_warn,
                info_count=s_info,
                error_rate=s_rate,
            ))
        service_stats.sort(key=lambda s: (s.error_count, s.total_entries), reverse=True)

        # Top Recurring Errors
        top_errors: List[TopErrorItem] = []
        error_df = df[df["level"].isin(["ERROR", "CRITICAL"]) | (df["status_code"] >= 500)]
        if not error_df.empty:
            for msg, group in error_df.groupby("message"):
                cnt = len(group)
                pct = round((cnt / total_errors * 100.0), 2) if total_errors > 0 else 100.0
                services_affected = [str(s) for s in group["service"].dropna().unique().tolist()][:5]
                valid_ts = group["timestamp"].dropna()
                first_seen = str(valid_ts.min()) if not valid_ts.empty else None
                last_seen = str(valid_ts.max()) if not valid_ts.empty else None

                top_errors.append(TopErrorItem(
                    message=str(msg)[:200],  # truncate extremely long messages
                    count=cnt,
                    percentage=pct,
                    services=services_affected,
                    first_seen=first_seen,
                    last_seen=last_seen,
                ))
            top_errors.sort(key=lambda x: x.count, reverse=True)
            top_errors = top_errors[:15]

        # Status Code Distribution
        status_dist: Dict[str, int] = {}
        valid_status = df["status_code"].dropna()
        if not valid_status.empty:
            for sc, count in valid_status.value_counts().items():
                status_dist[str(int(sc))] = int(count)

        # Response Time Stats
        rt_stats: Optional[ResponseTimeStats] = None
        valid_rt = df["response_time_ms"].dropna()
        if not valid_rt.empty and len(valid_rt) > 0:
            rt_stats = ResponseTimeStats(
                count=int(len(valid_rt)),
                avg_ms=round(float(valid_rt.mean()), 2),
                median_ms=round(float(valid_rt.median()), 2),
                p90_ms=round(float(np.percentile(valid_rt, 90)), 2),
                p95_ms=round(float(np.percentile(valid_rt, 95)), 2),
                p99_ms=round(float(np.percentile(valid_rt, 99)), 2),
                min_ms=round(float(valid_rt.min()), 2),
                max_ms=round(float(valid_rt.max()), 2),
            )

        # Time Series and Heatmap
        time_series: List[TimeVolumePoint] = []
        heatmap: List[HeatmapPoint] = []
        anomalies: List[AnomalyItem] = []
        time_range = None

        valid_time_df = df.dropna(subset=["timestamp"]).copy()
        if not valid_time_df.empty:
            try:
                valid_time_df["dt"] = pd.to_datetime(valid_time_df["timestamp"], errors="coerce")
                valid_time_df = valid_time_df.dropna(subset=["dt"]).sort_values("dt")
            except Exception:
                valid_time_df["dt"] = None

        if not valid_time_df.empty and "dt" in valid_time_df and not valid_time_df["dt"].isna().all():
            min_time = valid_time_df["dt"].min()
            max_time = valid_time_df["dt"].max()
            time_range = {
                "start": min_time.isoformat() if pd.notna(min_time) else None,
                "end": max_time.isoformat() if pd.notna(max_time) else None,
            }

            span_seconds = (max_time - min_time).total_seconds() if pd.notna(min_time) and pd.notna(max_time) else 0

            # Dynamic interval rule
            if span_seconds < 3600:       # < 1 hour -> group by minute
                resample_rule = "1min"
            elif span_seconds < 86400 * 2: # < 2 days -> group by 5 min or hour
                resample_rule = "5min" if span_seconds < 14400 else "1h"
            elif span_seconds < 86400 * 14: # < 2 weeks -> group by hour
                resample_rule = "1h"
            else:
                resample_rule = "1D"

            try:
                time_indexed = valid_time_df.set_index("dt")
                grouped = time_indexed.resample(resample_rule)

                error_counts_list = []
                total_counts_list = []
                intervals_list = []

                for interval_start, group in grouped:
                    g_total = len(group)
                    if g_total == 0 and span_seconds > 86400:
                        continue
                    lvl_c = group["level"].value_counts().to_dict()
                    g_err = int(lvl_c.get("ERROR", 0) + lvl_c.get("CRITICAL", 0))
                    g_warn = int(lvl_c.get("WARNING", 0))
                    g_info = int(lvl_c.get("INFO", 0))
                    g_dbg = int(lvl_c.get("DEBUG", 0))

                    interval_str = interval_start.strftime("%Y-%m-%d %H:%M")
                    time_series.append(TimeVolumePoint(
                        interval=interval_str,
                        total=g_total,
                        error=g_err,
                        warning=g_warn,
                        info=g_info,
                        debug=g_dbg,
                    ))
                    error_counts_list.append(g_err)
                    total_counts_list.append(g_total)
                    intervals_list.append(interval_str)

                # Statistical Anomaly Detection on Intervals
                if len(error_counts_list) >= 4:
                    err_arr = np.array(error_counts_list)
                    err_mean = float(np.mean(err_arr))
                    err_std = float(np.std(err_arr))
                    err_thresh = max(3.0, err_mean + 2.0 * err_std)

                    tot_arr = np.array(total_counts_list)
                    tot_mean = float(np.mean(tot_arr))
                    tot_std = float(np.std(tot_arr))
                    tot_thresh = max(10.0, tot_mean + 2.5 * tot_std)

                    for i, (interval_str, err_val, tot_val) in enumerate(zip(intervals_list, error_counts_list, total_counts_list)):
                        if err_val >= err_thresh and err_val > 0:
                            anomalies.append(AnomalyItem(
                                id=f"spike-{i}",
                                type="error_spike",
                                title="Sudden Increase in Error Volume",
                                description=f"Potential anomaly: Error count reached {err_val} at {interval_str} (baseline mean: {err_mean:.1f}, threshold: {err_thresh:.1f}).",
                                timestamp_interval=interval_str,
                                severity="high" if err_val > err_mean + 3.0 * err_std else "medium",
                                metric_value=float(err_val),
                                baseline_value=round(err_mean, 1),
                            ))
                        elif tot_val >= tot_thresh and tot_val > 0:
                            anomalies.append(AnomalyItem(
                                id=f"burst-{i}",
                                type="activity_burst",
                                title="Unusual Surge in Total Log Volume",
                                description=f"Potential anomaly: Volume reached {tot_val} entries at {interval_str} (baseline mean: {tot_mean:.1f}).",
                                timestamp_interval=interval_str,
                                severity="medium",
                                metric_value=float(tot_val),
                                baseline_value=round(tot_mean, 1),
                            ))
            except Exception:
                pass

            # Heatmap calculation (day of week 0-6 x hour 0-23)
            try:
                if hasattr(valid_time_df["dt"].dt, "day_of_week"):
                    valid_time_df["dow"] = valid_time_df["dt"].dt.day_of_week
                else:
                    valid_time_df["dow"] = valid_time_df["dt"].dt.dayofweek
                valid_time_df["hour"] = valid_time_df["dt"].dt.hour
                valid_time_df["is_error"] = valid_time_df["level"].isin(["ERROR", "CRITICAL"])

                # Group by dow, hour
                hm_grouped = valid_time_df.groupby(["dow", "hour"]).agg(
                    total_count=("id", "count"),
                    error_count=("is_error", "sum")
                ).reset_index()

                for _, row in hm_grouped.iterrows():
                    d = int(row["dow"])
                    h = int(row["hour"])
                    heatmap.append(HeatmapPoint(
                        day_of_week=d,
                        day_name=DAYS_OF_WEEK[d] if 0 <= d < 7 else f"Day {d}",
                        hour=h,
                        error_count=int(row["error_count"]),
                        total_count=int(row["total_count"]),
                    ))
            except Exception:
                pass

        # Service level anomaly detection
        for s in service_stats:
            if s.total_entries >= 8 and s.error_rate >= 35.0:
                anomalies.append(AnomalyItem(
                    id=f"svc-err-{s.service}",
                    type="service_failure_rate",
                    title=f"Elevated Failure Rate in Service: {s.service}",
                    description=f"Potential anomaly: Service '{s.service}' recorded an error rate of {s.error_rate}% ({s.error_count} errors out of {s.total_entries} total events).",
                    timestamp_interval=None,
                    severity="high" if s.error_rate >= 50.0 else "medium",
                    metric_value=float(s.error_rate),
                    baseline_value=10.0,
                ))

        return LogAnalytics(
            total_lines=total_lines,
            parsed_lines=parsed_count,
            unparsed_lines=unparsed_count,
            success_rate=success_rate,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            debug_count=debug_count,
            critical_count=critical_count,
            distinct_services_count=distinct_services,
            most_active_service=most_active_service,
            top_errors=top_errors,
            service_stats=service_stats,
            status_code_distribution=status_dist,
            response_time_stats=rt_stats,
            time_series=time_series,
            anomalies=anomalies[:10],
            heatmap=heatmap,
            time_range=time_range,
        )


analytics_engine = AnalyticsEngine()
