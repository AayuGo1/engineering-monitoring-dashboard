"""
data/validator.py

Validation utilities for the Engineering Monitoring Dashboard.

This module performs structural validation of the Excel workbook and
individual worksheets before any downstream processing occurs.

Responsibilities
----------------
- Validate workbook structure.
- Validate worksheet integrity.
- Validate required columns.
- Validate date columns.
- Validate numeric columns.
- Summarize missing values.
- Normalize and validate headers.

This module intentionally does NOT validate:
- Department names
- Excel column letters
- Business logic
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd

from data.loader import (
    InvalidWorkbook,
    WorkbookNotFound,
    get_sheet_names,
    load_workbook,
)

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================


class ValidationError(Exception):
    """Base validation exception."""


class MissingColumnError(ValidationError):
    """Raised when required columns are missing."""


class DuplicateDateError(ValidationError):
    """Raised when duplicate dates are detected."""


class InvalidDateError(ValidationError):
    """Raised when a date column is invalid."""


# =============================================================================
# Workbook Validation
# =============================================================================


def validate_workbook(workbook_path: str) -> bool:
    """
    Validate that the workbook can be loaded and contains at least two sheets.

    Parameters
    ----------
    workbook_path : str
        Workbook path.

    Returns
    -------
    bool
        True when validation succeeds.

    Raises
    ------
    WorkbookNotFound
        Workbook does not exist.

    InvalidWorkbook
        Workbook cannot be loaded.

    ValidationError
        Workbook structure is invalid.
    """
    LOGGER.info("Validation Started: Workbook")

    workbook = load_workbook(workbook_path)

    sheet_names = get_sheet_names(workbook)

    if len(sheet_names) < 2:
        LOGGER.error("Validation Failed: Workbook has fewer than two sheets.")
        raise ValidationError(
            "Workbook must contain at least two worksheets."
        )

    LOGGER.info("Validation Passed: Workbook")

    return True


def validate_sheet_names(workbook_path: str) -> List[str]:
    """
    Validate workbook sheet names.

    Parameters
    ----------
    workbook_path : str

    Returns
    -------
    list[str]
        Workbook sheet names.

    Raises
    ------
    ValidationError
        Workbook has fewer than two sheets.
    """
    workbook = load_workbook(workbook_path)

    sheet_names = get_sheet_names(workbook)

    if len(sheet_names) < 2:
        LOGGER.error("Validation Failed: Missing worksheets.")
        raise ValidationError(
            "Workbook must contain at least two worksheets."
        )

    return sheet_names


# =============================================================================
# Sheet Validation
# =============================================================================


def validate_sheet(dataframe: pd.DataFrame) -> bool:
    """
    Validate a worksheet.

    Parameters
    ----------
    dataframe : pandas.DataFrame

    Returns
    -------
    bool
        True when validation succeeds.

    Raises
    ------
    ValidationError
        Worksheet validation fails.
    """
    LOGGER.info("Validation Started: Worksheet")

    if dataframe.empty:
        LOGGER.error("Validation Failed: Empty DataFrame.")
        raise ValidationError("Worksheet is empty.")

    if dataframe.shape[0] == 0:
        LOGGER.error("Validation Failed: No rows.")
        raise ValidationError("Worksheet contains no rows.")

    if dataframe.shape[1] == 0:
        LOGGER.error("Validation Failed: No columns.")
        raise ValidationError("Worksheet contains no columns.")

    if dataframe.columns.duplicated().any():
        duplicates = dataframe.columns[dataframe.columns.duplicated()].tolist()

        LOGGER.error("Validation Failed: Duplicate columns %s", duplicates)

        raise ValidationError(
            f"Duplicate column names detected: {duplicates}"
        )

    LOGGER.info("Validation Passed: Worksheet")

    return True


# =============================================================================
# Header Validation
# =============================================================================


def validate_headers(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize and validate DataFrame headers.

    Parameters
    ----------
    dataframe : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
        DataFrame with cleaned headers.

    Raises
    ------
    ValidationError
        Invalid headers detected.
    """
    cleaned = dataframe.copy()

    cleaned.columns = (
        cleaned.columns.astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    blank_headers = [
        column
        for column in cleaned.columns
        if column == "" or column.lower() == "nan"
    ]

    if blank_headers:
        LOGGER.error("Invalid Headers: Blank header(s) detected.")
        raise ValidationError(
            "Worksheet contains blank column headers."
        )

    if cleaned.columns.duplicated().any():
        duplicates = cleaned.columns[
            cleaned.columns.duplicated()
        ].tolist()

        LOGGER.error("Invalid Headers: Duplicate headers %s", duplicates)

        raise ValidationError(
            f"Duplicate headers detected: {duplicates}"
        )

    return cleaned


# =============================================================================
# Required Columns
# =============================================================================


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: List[str],
) -> bool:
    """
    Validate required columns.

    Parameters
    ----------
    dataframe : pandas.DataFrame

    required_columns : list[str]

    Returns
    -------
    bool
        True if all columns exist.

    Raises
    ------
    MissingColumnError
        Missing required columns.
    """
    missing = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing:
        LOGGER.error("Missing Columns: %s", missing)

        raise MissingColumnError(
            f"Missing required columns: {missing}"
        )

    return True


# =============================================================================
# Date Validation
# =============================================================================


def validate_dates(
    dataframe: pd.DataFrame,
    date_column: str,
) -> pd.DataFrame:
    """
    Validate a date column.

    Parameters
    ----------
    dataframe : pandas.DataFrame

    date_column : str

    Returns
    -------
    pandas.DataFrame
        Sorted DataFrame.

    Raises
    ------
    MissingColumnError
        Date column missing.

    InvalidDateError
        Invalid date values.

    DuplicateDateError
        Duplicate dates exist.
    """
    if date_column not in dataframe.columns:
        raise MissingColumnError(
            f"Date column '{date_column}' not found."
        )

    cleaned = dataframe.copy()

    converted = pd.to_datetime(
        cleaned[date_column],
        errors="coerce",
    )

    if converted.isna().any():
        LOGGER.error("Validation Failed: Invalid dates.")

        raise InvalidDateError(
            f"Invalid date values detected in '{date_column}'."
        )

    if converted.duplicated().any():
        LOGGER.error("Duplicate Dates Detected.")

        raise DuplicateDateError(
            f"Duplicate dates detected in '{date_column}'."
        )

    cleaned[date_column] = converted

    cleaned = cleaned.sort_values(
        by=date_column
    ).reset_index(drop=True)

    return cleaned


# =============================================================================
# Numeric Validation
# =============================================================================


def validate_numeric_columns(
    dataframe: pd.DataFrame,
    numeric_columns: List[str],
) -> Dict[str, Any]:
    """
    Validate numeric columns.

    Invalid values are safely converted to NaN.

    Parameters
    ----------
    dataframe : pandas.DataFrame

    numeric_columns : list[str]

    Returns
    -------
    dict
        {
            "dataframe": DataFrame,
            "invalid_columns": {
                column_name: invalid_count
            }
        }
    """
    cleaned = dataframe.copy()

    invalid_columns: Dict[str, int] = {}

    for column in numeric_columns:

        if column not in cleaned.columns:
            continue

        original_missing = cleaned[column].isna().sum()

        cleaned[column] = pd.to_numeric(
            cleaned[column],
            errors="coerce",
        )

        current_missing = cleaned[column].isna().sum()

        invalid_count = current_missing - original_missing

        if invalid_count > 0:
            invalid_columns[column] = invalid_count

    if invalid_columns:
        LOGGER.warning(
            "Numeric validation produced invalid values: %s",
            invalid_columns,
        )

    return {
        "dataframe": cleaned,
        "invalid_columns": invalid_columns,
    }


# =============================================================================
# Missing Value Validation
# =============================================================================


def validate_missing_values(
    dataframe: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Generate a missing value summary.

    Parameters
    ----------
    dataframe : pandas.DataFrame

    Returns
    -------
    dict
        Structured summary of missing values.
    """
    rows_with_missing = int(
        dataframe.isna().any(axis=1).sum()
    )

    columns_with_missing = (
        dataframe.isna()
        .sum()
        .loc[lambda x: x > 0]
        .to_dict()
    )

    total_cells = dataframe.shape[0] * dataframe.shape[1]

    missing_cells = int(
        dataframe.isna().sum().sum()
    )

    percentage_missing = (
        (missing_cells / total_cells) * 100
        if total_cells
        else 0.0
    )

    return {
        "rows_with_missing": rows_with_missing,
        "columns_with_missing": columns_with_missing,
        "missing_cells": missing_cells,
        "percentage_missing": round(
            percentage_missing,
            2,
        ),
    }
