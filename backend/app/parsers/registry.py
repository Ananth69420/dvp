from typing import Dict, Type, List, Tuple, Any, Optional
from app.parsers.base import BaseParser
from app.parsers.app_log import AppLogParser
from app.parsers.python_log import PythonLogParser
from app.parsers.access_log import AccessLogParser
from app.parsers.json_log import JsonLogParser
from app.parsers.csv_log import CsvLogParser


class ParserRegistry:
    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}
        # Register standard parsers
        self.register(AppLogParser())
        self.register(PythonLogParser())
        self.register(AccessLogParser())
        self.register(JsonLogParser())
        self.register(CsvLogParser())

    def register(self, parser: BaseParser):
        self._parsers[parser.name] = parser

    def get(self, name: str) -> Optional[BaseParser]:
        return self._parsers.get(name)

    def list_all(self) -> List[Dict[str, str]]:
        return [
            {
                "id": p.name,
                "name": p.display_name,
                "description": p.description,
            }
            for p in self._parsers.values()
        ]

    def detect_format(self, lines: List[str]) -> Tuple[str, float, List[Dict[str, Any]]]:
        scores = []
        best_name = "app_log"
        best_score = -1.0

        for name, parser in self._parsers.items():
            try:
                score = parser.can_parse(lines)
            except Exception:
                score = 0.0

            scores.append({
                "format_id": name,
                "name": parser.display_name,
                "confidence": round(score, 3)
            })

            if score > best_score:
                best_score = score
                best_name = name

        # Sort scores descending
        scores.sort(key=lambda s: s["confidence"], reverse=True)

        # Fallback if all scores are 0
        if best_score <= 0.0:
            best_name = "app_log"
            best_score = 0.1

        return best_name, best_score, scores


# Global singleton registry
parser_registry = ParserRegistry()

