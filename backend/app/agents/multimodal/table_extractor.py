"""
Structured Table Extractor & Parser (SIH26117).
Extracts and converts CSV, JSON, Markdown, and tabular text into structured numerical datasets.
Integrates with calculation_tool for deterministic arithmetic.
"""

import os
import csv
import io
import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class StructuredTable(BaseModel):
    title: str = "Table Dataset"
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    column_count: int
    numeric_summaries: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    source_type: str = "csv"  # "csv", "json", "markdown", "text"

    def get_column_values(self, col_name: str) -> List[Any]:
        idx = -1
        for i, c in enumerate(self.columns):
            if c.lower().strip() == col_name.lower().strip():
                idx = i
                break
        if idx == -1:
            return []
        return [row[idx] for row in self.rows if len(row) > idx]

    def get_numeric_values(self, col_name: str) -> List[float]:
        vals = self.get_column_values(col_name)
        nums = []
        for v in vals:
            try:
                # Clean currency, percent, units
                cleaned = re.sub(r"[^\d.-]", "", str(v))
                if cleaned:
                    nums.append(float(cleaned))
            except Exception:
                pass
        return nums


class TableExtractor:
    """
    Parses and summarizes tabular data from industrial files.
    """

    @staticmethod
    def extract_from_csv(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {"found": False, "error": f"File not found: {file_path}", "row_count": 0, "headers": []}
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        table = TableExtractor.from_csv_string(content, title=os.path.basename(file_path))
        return {
            "found": True,
            "title": table.title,
            "headers": table.columns,
            "row_count": table.row_count,
            "column_count": table.column_count,
            "rows": table.rows,
            "summary": table.numeric_summaries
        }

    @staticmethod
    def from_csv_string(csv_content: str, title: str = "CSV Table") -> StructuredTable:
        reader = csv.reader(io.StringIO(csv_content.strip()))
        rows_list = list(reader)
        if not rows_list:
            return StructuredTable(title=title, columns=[], rows=[], row_count=0, column_count=0, source_type="csv")

        headers = [h.strip() for h in rows_list[0]]
        data_rows = rows_list[1:]

        table = StructuredTable(
            title=title,
            columns=headers,
            rows=data_rows,
            row_count=len(data_rows),
            column_count=len(headers),
            source_type="csv"
        )
        TableExtractor._compute_summaries(table)
        return table

    @staticmethod
    def from_json_string(json_content: str, title: str = "JSON Table") -> StructuredTable:
        data = json.loads(json_content)
        if isinstance(data, dict):
            # Try to locate records array
            for k, v in data.items():
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    data = v
                    break

        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            headers = list(data[0].keys())
            rows = [[item.get(h, "") for h in headers] for item in data]
            table = StructuredTable(
                title=title,
                columns=headers,
                rows=rows,
                row_count=len(rows),
                column_count=len(headers),
                source_type="json"
            )
            TableExtractor._compute_summaries(table)
            return table

        return StructuredTable(title=title, columns=[], rows=[], row_count=0, column_count=0, source_type="json")

    @staticmethod
    def from_markdown_table(md_content: str, title: str = "Markdown Table") -> StructuredTable:
        lines = [l.strip() for l in md_content.splitlines() if "|" in l]
        if len(lines) < 2:
            return StructuredTable(title=title, columns=[], rows=[], row_count=0, column_count=0, source_type="markdown")

        header_line = lines[0].strip("|")
        headers = [h.strip() for h in header_line.split("|")]

        data_rows = []
        for line in lines[1:]:
            # Skip separator line (e.g. |---|---|)
            if re.match(r"^\|?[\s:-|-]+\|?$", line):
                continue
            row_vals = [c.strip() for c in line.strip("|").split("|")]
            if len(row_vals) == len(headers):
                data_rows.append(row_vals)

        table = StructuredTable(
            title=title,
            columns=headers,
            rows=data_rows,
            row_count=len(data_rows),
            column_count=len(headers),
            source_type="markdown"
        )
        TableExtractor._compute_summaries(table)
        return table

    @staticmethod
    def _compute_summaries(table: StructuredTable):
        summaries = {}
        for col in table.columns:
            nums = table.get_numeric_values(col)
            if nums and len(nums) >= max(1, int(table.row_count * 0.5)):
                summaries[col] = {
                    "count": float(len(nums)),
                    "min": min(nums),
                    "max": max(nums),
                    "sum": sum(nums),
                    "mean": round(sum(nums) / len(nums), 4)
                }
        table.numeric_summaries = summaries


# Global singleton
table_extractor = TableExtractor()
