import uuid
from typing import Dict, Optional, List, Any
from datetime import datetime
from app.models.schemas import (
    LogEntry,
    DataQualityReport,
    DatasetProfile,
    RecommendationEvaluation,
    EvaluationSummary,
    ChartRecommendation,
)


class DatasetSession:
    def __init__(self, dataset_id: str, filename: str, file_path: str, file_size: int, detected_format: str):
        self.dataset_id = dataset_id
        self.filename = filename
        self.file_path = file_path
        self.file_size = file_size
        self.detected_format = detected_format
        self.created_at = datetime.now().isoformat()
        
        self.raw_lines: List[str] = []
        self.parsed_entries: List[LogEntry] = []
        self.malformed_entries: List[LogEntry] = []
        self.data_quality: Optional[DataQualityReport] = None
        self.recommendations: List[ChartRecommendation] = []
        self.evaluations: Dict[str, RecommendationEvaluation] = {}

    def get_available_fields(self) -> List[str]:
        if not self.parsed_entries:
            return []
        fields = set()
        for e in self.parsed_entries:
            if e.timestamp:
                fields.add("timestamp")
            if e.level:
                fields.add("level")
            if e.service:
                fields.add("service")
            if e.message:
                fields.add("message")
            if e.source_ip:
                fields.add("source_ip")
            if e.http_method:
                fields.add("http_method")
            if e.request_path:
                fields.add("request_path")
            if e.status_code is not None:
                fields.add("status_code")
            if e.response_time_ms is not None:
                fields.add("response_time_ms")
        return sorted(list(fields))

    def get_profile(self) -> DatasetProfile:
        avail_fields = self.get_available_fields()
        dq = self.data_quality or DataQualityReport(
            total_lines=len(self.raw_lines),
            parsed_lines=len(self.parsed_entries),
            unparsed_lines=len(self.malformed_entries),
            success_rate=0.0,
            field_presence={},
            detected_format=self.detected_format,
            sample_failures=[],
        )
        return DatasetProfile(
            dataset_id=self.dataset_id,
            filename=self.filename,
            file_size_bytes=self.file_size,
            created_at=self.created_at,
            format=self.detected_format,
            data_quality=dq,
            available_fields=avail_fields,
        )

    def get_evaluation_summary(self) -> EvaluationSummary:
        total = len(self.recommendations)
        accepted = sum(1 for e in self.evaluations.values() if e.status == "accepted")
        rejected = sum(1 for e in self.evaluations.values() if e.status == "rejected")
        modified = sum(1 for e in self.evaluations.values() if e.status == "modified")
        rate = (accepted / total * 100.0) if total > 0 else 0.0

        return EvaluationSummary(
            total_recommendations=total,
            accepted_count=accepted,
            rejected_count=rejected,
            modified_count=modified,
            acceptance_rate=round(rate, 1),
            evaluations=list(self.evaluations.values()),
        )


class StorageService:
    def __init__(self):
        self._datasets: Dict[str, DatasetSession] = {}

    def create_dataset(self, filename: str, file_path: str, file_size: int, detected_format: str) -> DatasetSession:
        ds_id = str(uuid.uuid4())
        session = DatasetSession(
            dataset_id=ds_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            detected_format=detected_format,
        )
        self._datasets[ds_id] = session
        return session

    def get(self, dataset_id: str) -> Optional[DatasetSession]:
        return self._datasets.get(dataset_id)

    def delete(self, dataset_id: str) -> bool:
        if dataset_id in self._datasets:
            del self._datasets[dataset_id]
            return True
        return False


storage_service = StorageService()

