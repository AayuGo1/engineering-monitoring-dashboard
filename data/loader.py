"""
data/loader.py

Centralized Excel workbook loader for the Engineering Monitoring Dashboard.

This module is the single source of truth for reading the project's Excel
workbook. No other module should access the workbook directly.

Responsibilities
----------------
- Validate workbook availability.
- Load the Excel workbook.
- Read worksheet data dynamically.
- Remove completely empty rows and columns.
- Cache workbook reads.
- Provide reusable helper functions.
- Log workbook operations.
- Raise meaningful exceptions.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

WORKBOOK_NAME = "Daily energy Monitoring.xlsx"

LOGGER = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Custom Exceptions
# -----------------------------------------------------------------------------

class WorkbookNotFound(FileNotFoundError):
    """Raised when the Excel workbook cannot be found."""


class InvalidWorkbook(Exception):
    """Raised when the workbook cannot be opened or is invalid."""


class SheetNotFound(Exception):
    """Raised when the requested worksheet does not exist."""


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def validate_workbook_exists(workbook_path: str | Path = WORKBOOK_NAME) -> Path:
    """
    Validate that the workbook exists.

    Parameters
    ----------
    workbook_path : str | Path
        Path to the Excel workbook.

    Returns
    -------
    Path
        Resolved workbook path.

    Raises
    ------
    WorkbookNotFound
        If the workbook does not exist.
    """
    path = Path(workbook_path)

    if not path.exists():
        LOGGER.error("Workbook Missing: %s", path)
        raise WorkbookNotFound(
            f"Workbook not found: '{path}'. "
            "Ensure the Excel workbook exists and the path is correct."
        )

    return path


@st.cache_data(show_spinner=False)
def load_workbook(workbook_path: str | Path = WORKBOOK_NAME) -> pd.ExcelFile:
    """
    Load the Excel workbook.

    The workbook is cached to avoid repeated disk reads.

    Parameters
    ----------
    workbook_path : str | Path
        Workbook location.

    Returns
    -------
    pandas.ExcelFile
        Loaded workbook object.

    Raises
    ------
    WorkbookNotFound
        Workbook does not exist.

    InvalidWorkbook
        Workbook cannot be opened.
    """
    path = validate_workbook_exists(workbook_path)

    try:
        workbook = pd.ExcelFile(path)

        LOGGER.info("Workbook Loaded: %s", path)

        return workbook

    except WorkbookNotFound:
        raise

    except Exception as exc:
        LOGGER.exception("Failed loading workbook.")
        raise InvalidWorkbook(
            f"Unable to read workbook '{path}'."
        ) from exc


def get_sheet_names(workbook: pd.ExcelFile) -> List[str]:
    """
    Return workbook sheet names.

    Parameters
    ----------
    workbook : pandas.ExcelFile

    Returns
    -------
    list[str]
        Sheet names.
    """
    return workbook.sheet_names


def _load_sheet(
    workbook: pd.ExcelFile,
    sheet_index: int,
) -> pd.DataFrame:
    """
    Load a worksheet dynamically using its index.

    Parameters
    ----------
    workbook : pandas.ExcelFile
        Loaded workbook.

    sheet_index : int
        Zero-based worksheet index.

    Returns
    -------
    pandas.DataFrame
        Cleaned worksheet.

    Raises
    ------
    SheetNotFound
        If the worksheet index is unavailable.
    """
    sheet_names = get_sheet_names(workbook)

    try:
        sheet_name = sheet_names[sheet_index]
    except IndexError as exc:
        LOGGER.exception("Requested sheet index does not exist.")
        raise SheetNotFound(
            f"Worksheet index {sheet_index} not found."
        ) from exc

    dataframe = pd.read_excel(
        workbook,
        sheet_name=sheet_name,
    )

    dataframe = dataframe.dropna(axis=0, how="all")
    dataframe = dataframe.dropna(axis=1, how="all")

    LOGGER.info("Sheet Loaded: %s", sheet_name)

    return dataframe


@st.cache_data(show_spinner=False)
def load_sheet1(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> pd.DataFrame:
    """
    Load the first worksheet dynamically.

    Completely empty rows and columns are removed while preserving
    the original column headers.

    Parameters
    ----------
    workbook_path : str | Path
        Workbook path.

    Returns
    -------
    pandas.DataFrame
        First worksheet.
    """
    workbook = load_workbook(workbook_path)
    return _load_sheet(workbook, 0)


@st.cache_data(show_spinner=False)
def load_sheet2(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> pd.DataFrame:
    """
    Load the second worksheet dynamically.

    Completely empty rows and columns are removed.

    Parameters
    ----------
    workbook_path : str | Path
        Workbook path.

    Returns
    -------
    pandas.DataFrame
        Second worksheet.
    """
    workbook = load_workbook(workbook_path)
    return _load_sheet(workbook, 1)


@st.cache_data(show_spinner=False)
def load_all_data(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> Dict[str, pd.DataFrame]:
    """
    Load all required workbook data.

    Returns
    -------
    dict
        Dictionary containing both worksheets.

        {
            "sheet1": DataFrame,
            "sheet2": DataFrame
        }
    """
    return {
        "sheet1": load_sheet1(workbook_path),
        "sheet2": load_sheet2(workbook_path),
    }
