"""Data analysis and visualization plugin."""
from __future__ import annotations

import io
import json
from typing import Any

from core.plugins import Plugin
from core.tools import Tool


class DataAnalysisPlugin(Plugin):
    @property
    def name(self) -> str:
        return "data_analysis"

    @property
    def description(self) -> str:
        return "Data analysis, CSV/JSON processing, and statistics tools"

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="analyze_csv",
                description="Analyze a CSV file — get stats, column info, and sample rows.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to CSV file"},
                        "columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific columns to analyze (optional)",
                        },
                    },
                    "required": ["path"],
                },
                execute=self._analyze_csv,
            ),
            Tool(
                name="json_stats",
                description="Compute statistics on a JSON array of objects.",
                parameters={
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "JSON array string"},
                        "field": {"type": "string", "description": "Field to compute stats on"},
                    },
                    "required": ["data", "field"],
                },
                execute=self._json_stats,
            ),
            Tool(
                name="convert_format",
                description="Convert data between formats (CSV to JSON, JSON to CSV).",
                parameters={
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "Input data string"},
                        "from_format": {
                            "type": "string",
                            "enum": ["csv", "json"],
                            "description": "Source format",
                        },
                        "to_format": {
                            "type": "string",
                            "enum": ["csv", "json"],
                            "description": "Target format",
                        },
                    },
                    "required": ["data", "from_format", "to_format"],
                },
                execute=self._convert_format,
            ),
        ]

    def _analyze_csv(self, path: str, columns: list[str] | None = None) -> str:
        import csv
        from pathlib import Path
        from collections import Counter

        p = Path(path)
        if not p.exists():
            return f"Error: File not found: {path}"

        try:
            with open(p, newline="", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                return "CSV file is empty."

            all_columns = list(rows[0].keys())
            target_cols = columns if columns else all_columns

            lines = [f"CSV Analysis: {path} ({len(rows)} rows, {len(all_columns)} columns)\n"]
            lines.append(f"Columns: {', '.join(all_columns)}\n")

            for col in target_cols:
                if col not in all_columns:
                    lines.append(f"  {col}: Column not found")
                    continue

                values = [r.get(col, "") for r in rows]
                non_empty = [v for v in values if v]
                counter = Counter(non_empty)

                lines.append(f"\n  {col}:")
                lines.append(f"    Non-empty: {len(non_empty)}/{len(values)}")
                lines.append(f"    Unique: {len(counter)}")

                # Try numeric stats
                try:
                    nums = [float(v) for v in non_empty]
                    lines.append(f"    Min: {min(nums)}")
                    lines.append(f"    Max: {max(nums)}")
                    lines.append(f"    Avg: {sum(nums) / len(nums):.2f}")
                except ValueError:
                    top3 = counter.most_common(3)
                    if top3:
                        lines.append(f"    Top values: {', '.join(f'{v}({c})' for v, c in top3)}")

            # Sample rows
            lines.append("\nSample (first 3 rows):")
            for row in rows[:3]:
                lines.append(f"  {json.dumps(row)}")

            return "\n".join(lines)
        except Exception as e:
            return f"Error analyzing CSV: {e}"

    def _json_stats(self, data: str, field_name: str) -> str:
        try:
            items = json.loads(data)
            if not isinstance(items, list):
                return "Error: Input must be a JSON array."

            values = [item.get(field_name) for item in items if isinstance(item, dict)]
            non_none = [v for v in values if v is not None]

            if not non_none:
                return f"No values found for field '{field_name}'"

            lines = [f"Statistics for '{field_name}' ({len(non_none)} values):\n"]

            # Numeric stats
            try:
                nums = [float(v) for v in non_none]
                nums_sorted = sorted(nums)
                lines.append(f"  Count: {len(nums)}")
                lines.append(f"  Min: {min(nums)}")
                lines.append(f"  Max: {max(nums)}")
                lines.append(f"  Mean: {sum(nums) / len(nums):.4f}")
                lines.append(f"  Median: {nums_sorted[len(nums_sorted) // 2]}")
                lines.append(f"  Sum: {sum(nums):.4f}")
            except (ValueError, TypeError):
                from collections import Counter

                counter = Counter(str(v) for v in non_none)
                lines.append(f"  Count: {len(non_none)}")
                lines.append(f"  Unique: {len(counter)}")
                for val, count in counter.most_common(10):
                    lines.append(f"    {val}: {count}")

            return "\n".join(lines)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {e}"

    def _convert_format(self, data: str, from_format: str, to_format: str) -> str:
        try:
            if from_format == "csv" and to_format == "json":
                import csv
                import io

                reader = csv.DictReader(io.StringIO(data))
                result = json.dumps(list(reader), indent=2, ensure_ascii=False)
                return result

            elif from_format == "json" and to_format == "csv":
                items = json.loads(data)
                if not isinstance(items, list) or not items:
                    return "Error: Input must be a non-empty JSON array."
                import csv
                import io

                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=items[0].keys())
                writer.writeheader()
                writer.writerows(items)
                return output.getvalue()

            return f"Unsupported conversion: {from_format} -> {to_format}"
        except Exception as e:
            return f"Conversion error: {e}"


def register(registry: Any) -> None:
    from core.tools import ToolRegistry

    if isinstance(registry, ToolRegistry):
        plugin = DataAnalysisPlugin()
        for tool in plugin.get_tools():
            registry.register(tool)
