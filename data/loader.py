"""
data/loader.py

Centralized workbook loader for the Engineering Monitoring Dashboard.

This module is intentionally responsible ONLY for loading workbook data.
It never interprets workbook structure, headers, departments, meters,
sections, dates, engineering data, or business rules.

Responsibilities
----------------
- Verify workbook existence
- Load workbook
- Load raw worksheets exactly as stored
- Provide lightly cleaned worksheet loaders
- Cache workbook reads
- Provide reusable loading APIs

This module intentionally contains:
- No workbook parsing
- No department discovery
- No meter discovery
- No engineering calculations
- No business logic
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

LOGGER = logging.getLogger(__name__)

WORKBOOK_NAME = "Daily energy Monitoring.xlsx"


# =============================================================================
# Exceptions
# =============================================================================


class WorkbookNotFound(FileNotFoundError):
    """Raised when the workbook cannot be located."""


class InvalidWorkbook(Exception):
    """Raised when the workbook cannot be opened."""


class SheetNotFound(Exception):
    """Raised when the requested worksheet is unavailable."""


# =============================================================================
# Helpers
# =============================================================================


def validate_workbook_exists(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> Path:
    """
    Validate that the workbook exists.

    Parameters
    ----------
    workbook_path:
        Workbook path.

    Returns
    -------
    pathlib.Path
        Valid workbook path.

    Raises
    ------
    WorkbookNotFound
        If the workbook does not exist.
    """
    path = Path(workbook_path)

    if not path.exists():
        LOGGER.error("Workbook Missing: %s", path)
        raise WorkbookNotFound(
            f"Workbook not found: '{path}'."
        )

    return path


@st.cache_data(show_spinner=False)
def load_workbook(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> pd.ExcelFile:
    """
    Load the workbook.

    Parameters
    ----------
    workbook_path:
        Workbook path.

    Returns
    -------
    pandas.ExcelFile
        Workbook object.
    """
    path = validate_workbook_exists(workbook_path)

    try:
        workbook = pd.ExcelFile(path)

        LOGGER.info("Workbook Loaded: %s", path)

        return workbook

    except WorkbookNotFound:
        raise

    except Exception as exc:
        LOGGER.exception("Unable to load workbook.")

        raise InvalidWorkbook(
            f"Unable to open workbook '{path}'."
        ) from exc


def get_sheet_names(
    workbook: pd.ExcelFile,
) -> List[str]:
    """
    Return workbook sheet names.

    Parameters
    ----------
    workbook:
        Loaded workbook.

    Returns
    -------
    list[str]
    """
    return workbook.sheet_names


# =============================================================================
# Internal Loaders
# =============================================================================


def _sheet_name(
    workbook: pd.ExcelFile,
    sheet_index: int,
) -> str:
    """
    Resolve worksheet name from index.

    Parameters
    ----------
    workbook:
        Workbook.

    sheet_index:
        Zero-based sheet index.

    Returns
    -------
    str
        Worksheet name.
    """
    try:
        return get_sheet_names(workbook)[sheet_index]

    except IndexError as exc:
        LOGGER.exception("Sheet not found.")

        raise SheetNotFound(
            f"Worksheet index {sheet_index} does not exist."
        ) from exc


def _read_sheet(
    workbook_path: str | Path,
    sheet_index: int,
    *,
    header: int | None,
) -> pd.DataFrame:
    """
    Read a worksheet.

    Parameters
    ----------
    workbook_path:
        Workbook path.

    sheet_index:
        Zero-based worksheet index.

    header:
        pandas header argument.

    Returns
    -------
    pandas.DataFrame
    """
    workbook = load_workbook(workbook_path)

    sheet_name = _sheet_name(workbook, sheet_index)

    dataframe = pd.read_excel(
        workbook,
        sheet_name=sheet_name,
        header=header,
    )

    LOGGER.info("Sheet Loaded: %s", sheet_name)

    return dataframe


def _clean_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Remove completely empty rows and columns.

    Parameters
    ----------
    dataframe:
        Raw worksheet.

    Returns
    -------
    pandas.DataFrame
    """
    return (
        dataframe
        .dropna(axis=0, how="all")
        .dropna(axis=1, how="all")
        .reset_index(drop=True)
    )


# =============================================================================
# Raw Workbook API
# =============================================================================


@st.cache_data(show_spinner=False)
def load_raw_sheet1(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> pd.DataFrame:
    """
    Load Sheet 1 exactly as stored.

    No row is promoted to headers.

    Returns
    -------
    pandas.DataFrame
    """
    return _read_sheet(
        workbook_path,
        sheet_index=0,
        header=None,
    )


@st.cache_data(show_spinner=False)
def load_raw_sheet2(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> pd.DataFrame:
    """
    Load Sheet 2 exactly as stored.

    No row is promoted to headers.

    Returns
    -------
    pandas.DataFrame
    """
    return _read_sheet(
        workbook_path,
        sheet_index=1,
        header=None,
    )


@st.cache_data(show_spinner=False)
def load_raw_workbook(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> Dict[str, pd.DataFrame]:
    """
    Load the workbook exactly as stored.

    Returns
    -------
    dict
        {
            "sheet1": raw dataframe,
            "sheet2": raw dataframe
        }
    """
    return {
        "sheet1": load_raw_sheet1(workbook_path),
        "sheet2": load_raw_sheet2(workbook_path),
    }


# =============================================================================
# Clean Worksheet API
# =============================================================================


@st.cache_data(show_spinner=False)
def load_sheet1(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> pd.DataFrame:
    """
    Load a lightly cleaned version of Sheet 1.

    Cleaning performed:
    - Remove completely empty rows.
    - Remove completely empty columns.

    No workbook interpretation is performed.

    Returns
    -------
    pandas.DataFrame
    """
    return _clean_dataframe(
        load_raw_sheet1(workbook_path)
    )


@st.cache_data(show_spinner=False)
def load_sheet2(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> pd.DataFrame:
    """
    Load a lightly cleaned version of Sheet 2.

    Cleaning performed:
    - Remove completely empty rows.
    - Remove completely empty columns.

    No workbook interpretation is performed.

    Returns
    -------
    pandas.DataFrame
    """
    return _clean_dataframe(
        load_raw_sheet2(workbook_path)
    )


@st.cache_data(show_spinner=False)
def load_all_data(
    workbook_path: str | Path = WORKBOOK_NAME,
) -> Dict[str, pd.DataFrame]:
    """
    Load cleaned workbook sheets.

    Returns
    -------
    dict
        {
            "sheet1": DataFrame,
            "sheet2": DataFrame
        }
    """
    return {
        "sheet1": load_sheet1(workbook_path),
        "sheet2": load_sheet2(workbook_path),
    }
