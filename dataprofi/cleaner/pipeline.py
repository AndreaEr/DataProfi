from __future__ import annotations

import pandas as pd

from dataprofi.core.types import CleaningAction, CleaningReport
from dataprofi.cleaner.missing import handle_missing
from dataprofi.cleaner.duplicates import remove_duplicates
from dataprofi.cleaner.outliers import handle_outliers
from dataprofi.cleaner.types import coerce_types
from dataprofi.cleaner.normalize import normalize_column
from dataprofi.profiler.quality_scorer import score_quality


class CleaningPipeline:
    def __init__(self):
        self._steps: list[dict] = []
        self._actions: list[CleaningAction] = []
        self._report: CleaningReport | None = None

    def add_step(self, step_type: str, **kwargs) -> "CleaningPipeline":
        self._steps.append({"type": step_type, **kwargs})
        return self

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        self._actions = []
        score_before = score_quality(df).overall_score
        rows_before = len(df)

        for step in self._steps:
            step_type = step["type"]
            params = {k: v for k, v in step.items() if k != "type"}

            if step_type == "missing":
                df, actions = handle_missing(df, **params)
            elif step_type == "duplicates":
                df, actions = remove_duplicates(df, **params)
            elif step_type == "outliers":
                df, actions = handle_outliers(df, **params)
            elif step_type == "types":
                df, actions = coerce_types(df, **params)
            elif step_type == "normalize":
                col = params.pop("column", params.pop("columns", [None])[0])
                if col:
                    df, action = normalize_column(df, column=col, **params)
                    actions = [action]
                else:
                    actions = []
            else:
                raise ValueError(f"Unknown step type: {step_type}")

            self._actions.extend(actions)

        score_after = score_quality(df).overall_score

        self._report = CleaningReport(
            actions=self._actions,
            rows_before=rows_before,
            rows_after=len(df),
            score_before=score_before,
            score_after=score_after,
        )

        return df

    def report(self) -> CleaningReport:
        if self._report is None:
            raise RuntimeError("Pipeline has not been run yet. Call .run(df) first.")
        return self._report

    def summary(self) -> str:
        if self._report is None:
            return "Pipeline has not been run yet."

        lines = [
            f"Cleaning Pipeline Report",
            f"{'=' * 40}",
            f"Rows: {self._report.rows_before} → {self._report.rows_after}",
            f"Quality Score: {self._report.score_before:.1f} → {self._report.score_after:.1f}",
            f"Actions taken: {len(self._report.actions)}",
            "",
        ]
        for action in self._report.actions:
            lines.append(f"  • {action.description}")

        return "\n".join(lines)


def auto_clean(df: pd.DataFrame) -> pd.DataFrame:
    pipeline = CleaningPipeline()
    pipeline.add_step("types")
    pipeline.add_step("duplicates", method="exact")
    pipeline.add_step("missing", strategy="median")
    pipeline.add_step("outliers", method="iqr", action="clip")
    return pipeline.run(df)
