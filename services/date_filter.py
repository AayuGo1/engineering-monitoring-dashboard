"""
date_filter.py

Single source of truth for all date-based filtering used throughout the
Engineering Monitoring Dashboard.

This module is intentionally UI-agnostic and format-agnostic:
    - No Streamlit
    - No Plotly
    - No Excel / workbook loading
    - No engineering calculations or other business logic

It operates exclusively on pandas DataFrames that have already been
extracted and handed to it by upstream services (e.g.
services/engineering_parser.py). Every method is a pure function: given
the same input, it always returns the same output, it never mutates the
caller's DataFrame, and it always returns a copy.
"""

from __future__ import annotations

import datetime as dt
from typing import List, Tuple, Union

import pandas as pd

DateLike = Union[str, dt.date, dt.datetime, pd.Timestamp]


# =========================================================
# Exceptions
# =========================================================

class DateFilterError(Exception):
    """Base exception for all date_filter errors."""


class MissingDateColumnError(DateFilterError):
    """Raised when the requested date column does not exist in the
    DataFrame."""


class InvalidDateFormatError(DateFilterError):
    """Raised when a date value (either in the DataFrame or supplied by
    the caller) cannot be parsed."""


class EmptyDataFrameError(DateFilterError):
    """Raised when the input DataFrame contains no rows, or contains no
    valid dates after parsing."""


class InvalidDateRangeError(DateFilterError):
    """Raised when a supplied date range is logically invalid (e.g.
    ``start_date`` is after ``end_date``)."""


# =========================================================
# DateFilter
# =========================================================

class DateFilter:
    """
    Collection of static, reusable date-based filtering utilities.

    All methods accept a pandas DataFrame and the name of the column
    holding date/timestamp values, validate the input, and return a new
    DataFrame (or derived list) without mutating the original.
    """

    # -----------------------------------------------------
    # Private helpers
    # -----------------------------------------------------

    @staticmethod
    def _ensure_dataframe(dataframe: pd.DataFrame) -> None:
        """
        Validate that the input is a non-empty pandas DataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            The object to validate.

        Raises
        ------
        DateFilterError
            If ``dataframe`` is not a pandas DataFrame.
        EmptyDataFrameError
            If ``dataframe`` contains no rows.
        """
        if not isinstance(dataframe, pd.DataFrame):
            raise DateFilterError(
                f"Expected a pandas DataFrame, got {type(dataframe).__name__}."
            )
        if dataframe.empty:
            raise EmptyDataFrameError("The provided DataFrame is empty.")

    @staticmethod
    def _ensure_date_column(dataframe: pd.DataFrame, date_column: str) -> None:
        """
        Validate that ``date_column`` exists in ``dataframe``.

        Parameters
        ----------
        dataframe : pd.DataFrame
            The DataFrame to check.
        date_column : str
            Name of the expected date column.

        Raises
        ------
        MissingDateColumnError
            If ``date_column`` is not a column in ``dataframe``.
        """
        if date_column not in dataframe.columns:
            raise MissingDateColumnError(
                f"Date column '{date_column}' was not found in the DataFrame. "
                f"Available columns: {list(dataframe.columns)}"
            )

    @staticmethod
    def _prepare(dataframe: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """
        Validate the DataFrame and date column, then return a working
        copy with the date column parsed to ``datetime64``.

        Rows whose date value cannot be parsed are dropped from the
        working copy (they are considered invalid, not fatal, unless
        this leaves no valid rows at all).

        Parameters
        ----------
        dataframe : pd.DataFrame
            Source DataFrame.
        date_column : str
            Name of the column holding date/timestamp values.

        Returns
        -------
        pd.DataFrame
            A copy of ``dataframe`` with ``date_column`` coerced to
            ``datetime64[ns]`` and invalid dates removed.

        Raises
        ------
        EmptyDataFrameError
            If the DataFrame is empty, or no valid dates remain after
            parsing.
        MissingDateColumnError
            If ``date_column`` is missing.
        """
        DateFilter._ensure_dataframe(dataframe)
        DateFilter._ensure_date_column(dataframe, date_column)

        working = dataframe.copy()
        working[date_column] = pd.to_datetime(working[date_column], errors="coerce")
        working = working.dropna(subset=[date_column])

        if working.empty:
            raise EmptyDataFrameError(
                f"No valid dates found in column '{date_column}' after parsing."
            )

        return working

    @staticmethod
    def _parse_single_date(value: DateLike, label: str = "date") -> pd.Timestamp:
        """
        Safely parse a single caller-supplied date-like value.

        Parameters
        ----------
        value : DateLike
            The value to parse (string, date, datetime, or Timestamp).
        label : str, default "date"
            Human-readable label used in error messages.

        Returns
        -------
        pd.Timestamp
            The parsed timestamp.

        Raises
        ------
        InvalidDateFormatError
            If ``value`` cannot be parsed into a valid date.
        """
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            raise InvalidDateFormatError(
                f"Could not parse {label} value: {value!r}"
            )
        return parsed

    # -----------------------------------------------------
    # Public filtering methods
    # -----------------------------------------------------

    @staticmethod
    def filter_by_date(
        dataframe: pd.DataFrame, date_column: str, date: DateLike
    ) -> pd.DataFrame:
        """
        Return rows matching a single, specific calendar date.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Source DataFrame.
        date_column : str
            Name of the column holding date/timestamp values.
        date : DateLike
            The target date (string, date, datetime, or Timestamp). Only
            the calendar-date portion is compared; time-of-day is
            ignored.

        Returns
        -------
        pd.DataFrame
            Copy of the rows whose date matches ``date``.

        Raises
        ------
        MissingDateColumnError
            If ``date_column`` is missing.
        EmptyDataFrameError
            If ``dataframe`` is empty or has no valid dates.
        InvalidDateFormatError
            If ``date`` cannot be parsed.
        """
        working = DateFilter._prepare(dataframe, date_column)
        target = DateFilter._parse_single_date(date, label="date").date()

        mask = working[date_column].dt.date == target
        return working.loc[mask].copy()

    @staticmethod
    def filter_by_month(
        dataframe: pd.DataFrame, date_column: str, year: int, month: int
    ) -> pd.DataFrame:
        """
        Return rows belonging to a specific year/month.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Source DataFrame.
        date_column : str
            Name of the column holding date/timestamp values.
        year : int
            Target calendar year (e.g. 2024).
        month : int
            Target calendar month (1-12).

        Returns
        -------
        pd.DataFrame
            Copy of the rows falling within the requested month.

        Raises
        ------
        MissingDateColumnError
            If ``date_column`` is missing.
        EmptyDataFrameError
            If ``dataframe`` is empty or has no valid dates.
        InvalidDateFormatError
            If ``month`` is not in the range 1-12.
        """
        working = DateFilter._prepare(dataframe, date_column)

        if not 1 <= month <= 12:
            raise InvalidDateFormatError(
                f"Invalid month: {month!r}. Month must be between 1 and 12."
            )

        mask = (working[date_column].dt.year == year) & (
            working[date_column].dt.month == month
        )
        return working.loc[mask].copy()

    @staticmethod
    def filter_by_year(
        dataframe: pd.DataFrame, date_column: str, year: int
    ) -> pd.DataFrame:
        """
        Return rows belonging to a specific calendar year.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Source DataFrame.
        date_column : str
            Name of the column holding date/timestamp values.
        year : int
            Target calendar year (e.g. 2024).

        Returns
        -------
        pd.DataFrame
            Copy of the rows falling within the requested year.

        Raises
        ------
        MissingDateColumnError
            If ``date_column`` is missing.
        EmptyDataFrameError
            If ``dataframe`` is empty or has no valid dates.
        """
        working = DateFilter._prepare(dataframe, date_column)
        mask = working[date_column].dt.year == year
        return working.loc[mask].copy()

    @staticmethod
    def filter_by_range(
        dataframe: pd.DataFrame,
        date_column: str,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.DataFrame:
        """
        Return rows within an inclusive date range.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Source DataFrame.
        date_column : str
            Name of the column holding date/timestamp values.
        start_date : DateLike
            Start of the range (inclusive).
        end_date : DateLike
            End of the range (inclusive).

        Returns
        -------
        pd.DataFrame
            Copy of the rows whose date falls within
            ``[start_date, end_date]`` inclusive.

        Raises
        ------
        MissingDateColumnError
            If ``date_column`` is missing.
        EmptyDataFrameError
            If ``dataframe`` is empty or has no valid dates.
        InvalidDateFormatError
            If ``start_date`` or ``end_date`` cannot be parsed.
        InvalidDateRangeError
            If ``start_date`` is later than ``end_date``.
        """
        working = DateFilter._prepare(dataframe, date_column)

        start = DateFilter._parse_single_date(start_date, label="start_date")
        end = DateFilter._parse_single_date(end_date, label="end_date")

        if start > end:
            raise InvalidDateRangeError(
                f"start_date ({start.date()}) must not be later than "
                f"end_date ({end.date()})."
            )

        # Normalize to full-day boundaries so the range is inclusive of
        # the entire end_date, regardless of time-of-day components.
        start_bound = start.normalize()
        end_bound = end.normalize() + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)

        mask = (working[date_column] >= start_bound) & (
            working[date_column] <= end_bound
        )
        return working.loc[mask].copy()

    @staticmethod
    def latest_period(dataframe: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """
        Return rows corresponding to the most recent available date.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Source DataFrame.
        date_column : str
            Name of the column holding date/timestamp values.

        Returns
        -------
        pd.DataFrame
            Copy of the rows whose date equals the latest date present
            in ``date_column``.

        Raises
        ------
        MissingDateColumnError
            If ``date_column`` is missing.
        EmptyDataFrameError
            If ``dataframe`` is empty or has no valid dates.
        """
        working = DateFilter._prepare(dataframe, date_column)
        latest_date = working[date_column].dt.date.max()

        mask = working[date_column].dt.date == latest_date
        return working.loc[mask].copy()

    # -----------------------------------------------------
    # Public discovery methods
    # -----------------------------------------------------

    @staticmethod
    def available_dates(
        dataframe: pd.DataFrame, date_column: str
    ) -> List[dt.date]:
        """
        Return the sorted list of distinct calendar dates present in
        the DataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Source DataFrame.
        date_column : str
            Name of the column holding date/timestamp values.

        Returns
        -------
        List[datetime.date]
            Sorted (ascending) list of unique dates.

        Raises
        ------
        MissingDateColumnError
            If ``date_column`` is missing.
        EmptyDataFrameError
            If ``dataframe`` is empty or has no valid dates.
        """
        working = DateFilter._prepare(dataframe, date_column)
        unique_dates = working[date_column].dt.date.unique()
        return sorted(unique_dates)

    @staticmethod
    def available_months(
        dataframe: pd.DataFrame, date_column: str
    ) -> List[Tuple[int, int]]:
        """
        Return the sorted list of distinct (year, month) tuples present
        in the DataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Source DataFrame.
        date_column : str
            Name of the column holding date/timestamp values.

        Returns
        -------
        List[Tuple[int, int]]
            Sorted (ascending) list of unique ``(year, month)`` tuples.

        Raises
        ------
        MissingDateColumnError
            If ``date_column`` is missing.
        EmptyDataFrameError
            If ``dataframe`` is empty or has no valid dates.
        """
        working = DateFilter._prepare(dataframe, date_column)
        pairs = set(
            zip(working[date_column].dt.year, working[date_column].dt.month)
        )
        return sorted(pairs)

    @staticmethod
    def available_years(dataframe: pd.DataFrame, date_column: str) -> List[int]:
        """
        Return the sorted list of distinct years present in the
        DataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Source DataFrame.
        date_column : str
            Name of the column holding date/timestamp values.

        Returns
        -------
        List[int]
            Sorted (ascending) list of unique years.

        Raises
        ------
        MissingDateColumnError
            If ``date_column`` is missing.
        EmptyDataFrameError
            If ``dataframe`` is empty or has no valid dates.
        """
        working = DateFilter._prepare(dataframe, date_column)
        unique_years = working[date_column].dt.year.unique()
        return sorted(int(year) for year in unique_years)
