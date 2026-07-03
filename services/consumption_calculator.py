"""
consumption_calculator.py

Single source of truth for low-level engineering meter calculations used
throughout the Engineering Monitoring Dashboard.

This module is intentionally UI-agnostic and format-agnostic:
    - No Streamlit
    - No Plotly
    - No Excel / workbook loading
    - No parser or business-level aggregation logic

It operates exclusively on pandas Series/DataFrame objects that have
already been extracted and handed to it by upstream services
(e.g. services/engineering_parser.py). Every function here is a pure
function: given the same input, it always returns the same output, and
it never mutates the input or has side effects.

All functions treat the input series as CHRONOLOGICAL CUMULATIVE
engineering meter readings (e.g. kWh, m3, liters), unless otherwise
noted.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


# =========================================================
# Exceptions
# =========================================================

class ConsumptionCalculatorError(Exception):
    """Base exception for all consumption_calculator errors."""


class EmptySeriesError(ConsumptionCalculatorError):
    """Raised when a series contains no valid (non-null, numeric) data."""


class InsufficientDataError(ConsumptionCalculatorError):
    """Raised when an operation needs at least two valid readings but
    fewer are available (e.g. computing consumption from a single
    reading)."""


class InvalidInputTypeError(ConsumptionCalculatorError):
    """Raised when the input provided is not a supported pandas type."""


# =========================================================
# Private helpers
# =========================================================

def _ensure_series(series: pd.Series) -> pd.Series:
    """
    Validate that the input is a pandas Series and return it unchanged.

    Parameters
    ----------
    series : pd.Series
        The object to validate.

    Returns
    -------
    pd.Series
        The same series, unmodified.

    Raises
    ------
    InvalidInputTypeError
        If ``series`` is not a pandas Series.
    """
    if not isinstance(series, pd.Series):
        raise InvalidInputTypeError(
            f"Expected a pandas Series, got {type(series).__name__}."
        )
    return series


def _to_clean_numeric_series(series: pd.Series) -> pd.Series:
    """
    Coerce a raw meter-reading series into a clean numeric series.

    Performs the following, in order:
        1. Validates the input is a pandas Series.
        2. Safely converts values (including numeric strings such as
           "125" or "1,250") to numeric dtype, turning anything
           unparsable into NaN.
        3. Drops NaN and blank (empty-string / whitespace-only) values.

    Parameters
    ----------
    series : pd.Series
        Raw series of engineering meter readings. May contain numeric
        strings, blanks, or NaN values.

    Returns
    -------
    pd.Series
        A cleaned series containing only valid numeric readings, with
        the original index preserved for the retained entries.

    Raises
    ------
    InvalidInputTypeError
        If ``series`` is not a pandas Series.
    """
    series = _ensure_series(series)

    # Normalize string entries: strip whitespace and remove thousands
    # separators (e.g. "1,250" -> "1250") before numeric conversion.
    if series.dtype == object:
        series = series.astype(str).str.strip().str.replace(",", "", regex=False)
        series = series.replace({"": np.nan, "nan": np.nan, "None": np.nan})

    numeric_series = pd.to_numeric(series, errors="coerce")
    return numeric_series.dropna()


def _require_non_empty(series: pd.Series) -> pd.Series:
    """
    Return a cleaned numeric series, raising if it ends up empty.

    Parameters
    ----------
    series : pd.Series
        Raw series of engineering meter readings.

    Returns
    -------
    pd.Series
        Cleaned, non-empty numeric series.

    Raises
    ------
    EmptySeriesError
        If no valid numeric readings remain after cleaning.
    """
    cleaned = _to_clean_numeric_series(series)
    if cleaned.empty:
        raise EmptySeriesError(
            "Series contains no valid (non-null, numeric) readings."
        )
    return cleaned


def _require_min_readings(series: pd.Series, minimum: int = 2) -> pd.Series:
    """
    Return a cleaned numeric series, raising if it has too few readings.

    Parameters
    ----------
    series : pd.Series
        Raw series of engineering meter readings.
    minimum : int, default 2
        The minimum number of valid readings required.

    Returns
    -------
    pd.Series
        Cleaned numeric series with at least ``minimum`` entries.

    Raises
    ------
    EmptySeriesError
        If no valid numeric readings remain after cleaning.
    InsufficientDataError
        If fewer than ``minimum`` valid readings remain after cleaning.
    """
    cleaned = _require_non_empty(series)
    if len(cleaned) < minimum:
        raise InsufficientDataError(
            f"At least {minimum} valid readings are required, "
            f"but only {len(cleaned)} were found."
        )
    return cleaned


# =========================================================
# Public calculation functions
# =========================================================

def latest_reading(series: pd.Series) -> float:
    """
    Return the most recent valid reading in a chronological series.

    Parameters
    ----------
    series : pd.Series
        Chronological cumulative meter readings (oldest first).

    Returns
    -------
    float
        The latest valid (non-NaN, numeric) reading.

    Raises
    ------
    EmptySeriesError
        If the series contains no valid readings.
    """
    cleaned = _require_non_empty(series)
    return float(cleaned.iloc[-1])


def previous_reading(series: pd.Series) -> float:
    """
    Return the second-most-recent valid reading in a chronological series.

    Parameters
    ----------
    series : pd.Series
        Chronological cumulative meter readings (oldest first).

    Returns
    -------
    float
        The valid reading immediately preceding the latest one.

    Raises
    ------
    InsufficientDataError
        If fewer than two valid readings are available.
    """
    cleaned = _require_min_readings(series, minimum=2)
    return float(cleaned.iloc[-2])


def consumption(series: pd.Series) -> float:
    """
    Return the consumption between the latest and previous readings.

    Computed as ``latest_reading(series) - previous_reading(series)``.

    Parameters
    ----------
    series : pd.Series
        Chronological cumulative meter readings (oldest first).

    Returns
    -------
    float
        The difference between the latest and previous valid readings.

    Raises
    ------
    InsufficientDataError
        If fewer than two valid readings are available.
    """
    cleaned = _require_min_readings(series, minimum=2)
    return float(cleaned.iloc[-1] - cleaned.iloc[-2])


def daily_consumption(series: pd.Series) -> pd.Series:
    """
    Return the period-over-period (first-difference) consumption series.

    Uses ``pandas.Series.diff()`` on the cleaned readings, so each value
    represents the consumption between one reading and the reading
    immediately before it. The first entry is always NaN, as there is
    no prior reading to diff against.

    Parameters
    ----------
    series : pd.Series
        Chronological cumulative meter readings (oldest first).

    Returns
    -------
    pd.Series
        Series of first differences, indexed like the cleaned input.

    Raises
    ------
    EmptySeriesError
        If the series contains no valid readings.
    """
    cleaned = _require_non_empty(series)
    return cleaned.diff()


def total_consumption(series: pd.Series) -> float:
    """
    Return the total consumption across the entire series.

    Computed as the last valid reading minus the first valid reading.

    Parameters
    ----------
    series : pd.Series
        Chronological cumulative meter readings (oldest first).

    Returns
    -------
    float
        Total consumption over the full period covered by the series.

    Raises
    ------
    InsufficientDataError
        If fewer than two valid readings are available.
    """
    cleaned = _require_min_readings(series, minimum=2)
    return float(cleaned.iloc[-1] - cleaned.iloc[0])


def maximum_reading(series: pd.Series) -> float:
    """
    Return the maximum valid reading in the series.

    Parameters
    ----------
    series : pd.Series
        Chronological cumulative meter readings.

    Returns
    -------
    float
        The maximum valid reading.

    Raises
    ------
    EmptySeriesError
        If the series contains no valid readings.
    """
    cleaned = _require_non_empty(series)
    return float(cleaned.max())


def minimum_reading(series: pd.Series) -> float:
    """
    Return the minimum valid reading in the series.

    Parameters
    ----------
    series : pd.Series
        Chronological cumulative meter readings.

    Returns
    -------
    float
        The minimum valid reading.

    Raises
    ------
    EmptySeriesError
        If the series contains no valid readings.
    """
    cleaned = _require_non_empty(series)
    return float(cleaned.min())


def average_reading(series: pd.Series) -> float:
    """
    Return the arithmetic mean of all valid readings in the series.

    Parameters
    ----------
    series : pd.Series
        Chronological cumulative meter readings.

    Returns
    -------
    float
        The mean of all valid readings.

    Raises
    ------
    EmptySeriesError
        If the series contains no valid readings.
    """
    cleaned = _require_non_empty(series)
    return float(cleaned.mean())


def latest_timestamp(df: pd.DataFrame, date_column: str) -> Optional[pd.Timestamp]:
    """
    Return the most recent timestamp found in a DataFrame's date column.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame expected to contain a date/timestamp column.
    date_column : str
        Name of the column holding date/timestamp values.

    Returns
    -------
    Optional[pd.Timestamp]
        The latest valid timestamp, or ``None`` if the date column is
        missing from ``df`` or contains no valid, parseable dates.

    Raises
    ------
    InvalidInputTypeError
        If ``df`` is not a pandas DataFrame.
    """
    if not isinstance(df, pd.DataFrame):
        raise InvalidInputTypeError(
            f"Expected a pandas DataFrame, got {type(df).__name__}."
        )

    if date_column not in df.columns:
        return None

    parsed_dates = pd.to_datetime(df[date_column], errors="coerce").dropna()
    if parsed_dates.empty:
        return None

    return parsed_dates.max()
