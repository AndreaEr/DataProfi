"""DataProfi scoring methodology.

Quality dimensions are aligned with ISO/IEC 25012 (Data Quality Model)
and DAMA DMBOK (Data Management Body of Knowledge) frameworks.
"""

METHODOLOGY = {
    "framework": "ISO/IEC 25012 / DAMA DMBOK aligned",
    "version": "1.0",
    "description": (
        "DataProfi scores data quality across 5 dimensions derived from "
        "ISO/IEC 25012 (Software product Quality Requirements and Evaluation - "
        "SQuaRE - Data quality model) and the DAMA DMBOK Data Quality framework. "
        "Each dimension is scored 0-100 using deterministic statistical methods."
    ),
    "dimensions": [
        {
            "name": "Completeness",
            "weight": 0.25,
            "iso_25012_mapping": "Completeness (inherent)",
            "dama_mapping": "Completeness",
            "definition": (
                "The degree to which data has values for all expected attributes. "
                "Measures the proportion of non-null values across all cells."
            ),
            "formula": "score = (non_null_cells / total_cells) * 100",
            "thresholds": {
                "excellent": ">= 98%",
                "good": ">= 95%",
                "fair": ">= 90%",
                "poor": "< 90%",
            },
            "issues_detected": [
                "Columns with > 5% null values",
            ],
        },
        {
            "name": "Consistency",
            "weight": 0.20,
            "iso_25012_mapping": "Consistency (inherent)",
            "dama_mapping": "Consistency",
            "definition": (
                "The degree to which data values conform to a consistent format "
                "and representation. Checks for mixed case, whitespace issues, "
                "and mixed data types within columns."
            ),
            "formula": "score = 100 - (inconsistencies / total_checks * 50)",
            "checks_performed": [
                "Mixed case formatting (upper and lower in same column)",
                "Inconsistent whitespace (leading/trailing spaces)",
                "Mixed numeric and text values in same column",
            ],
        },
        {
            "name": "Uniqueness",
            "weight": 0.20,
            "iso_25012_mapping": "Uniqueness (inherent)",
            "dama_mapping": "Uniqueness",
            "definition": (
                "The degree to which there are no duplicate records. "
                "Measures both exact row duplication and suspicious "
                "low-cardinality patterns."
            ),
            "formula": "score = (total_rows - duplicate_rows) / total_rows * 100",
            "checks_performed": [
                "Exact duplicate row detection",
                "Low-cardinality column flagging (< 5 unique values with > 80% duplicates)",
            ],
        },
        {
            "name": "Validity",
            "weight": 0.20,
            "iso_25012_mapping": "Accuracy (inherent)",
            "dama_mapping": "Validity / Accuracy",
            "definition": (
                "The degree to which data values conform to the defined domain "
                "constraints. Checks for impossible values, infinities, "
                "and suspicious patterns like excessive zeros."
            ),
            "formula": "score = 100 - (invalid_count / total_checks * 30)",
            "checks_performed": [
                "Extreme negative values (< -1e10)",
                "Infinite values",
                "Excessive zeros (> 90% of column)",
                "Empty strings (non-null but zero-length)",
            ],
        },
        {
            "name": "Timeliness",
            "weight": 0.15,
            "iso_25012_mapping": "Currentness (system-dependent)",
            "dama_mapping": "Timeliness",
            "definition": (
                "The degree to which temporal data is current, regular, "
                "and free of unexpected gaps. Assesses whether datetime "
                "columns have consistent intervals."
            ),
            "formula": "score = 100 - penalties (uniform dates: -10, large gaps: -5 each)",
            "checks_performed": [
                "Uniform date detection (all same value)",
                "Unusual temporal gaps (> 3x median interval)",
                "Date column auto-detection from string columns",
            ],
            "note": "Score defaults to 80 if no datetime columns are present.",
        },
    ],
    "overall_score": {
        "formula": "weighted_average = sum(dimension_score * weight)",
        "range": "0-100",
        "interpretation": {
            "90-100": "Excellent quality - ready for production use",
            "75-89": "Good quality - minor issues to address",
            "60-74": "Fair quality - requires cleaning before analysis",
            "below_60": "Poor quality - significant data issues present",
        },
    },
    "outlier_detection": {
        "method": "IQR (Interquartile Range)",
        "formula": "outlier if value < Q1 - 1.5*IQR or value > Q3 + 1.5*IQR",
        "alternative": "Z-score method available (threshold = 3 standard deviations)",
        "reference": "Tukey, J.W. (1977). Exploratory Data Analysis.",
    },
    "column_role_classification": {
        "method": "Heuristic rule-based classification",
        "roles": {
            "id": "unique_ratio > 0.95 and total_rows > 50",
            "boolean": "unique_count <= 2 or dtype is bool",
            "datetime": "dtype is datetime64 or > 80% values parseable as dates",
            "category": "string dtype with unique_count <= max(50, 5% of total)",
            "free_text": "string dtype with avg_length > 50 or unique_ratio > 0.8",
            "measure": "numeric dtype not classified as ID or boolean",
        },
    },
    "references": [
        "ISO/IEC 25012 - Software product Quality Requirements and Evaluation (SQuaRE) - Data quality model.",
        "DAMA International (2017). DAMA-DMBOK: Data Management Body of Knowledge, 2nd Edition. Technics Publications.",
        "Tukey, J.W. (1977). Exploratory Data Analysis. Addison-Wesley.",
        "Cramer, H. (1946). Mathematical Methods of Statistics. Princeton University Press.",
    ],
}


def get_methodology() -> dict:
    return METHODOLOGY
