"""
services/date_filter.py

Reusable date filtering service for the Engineering Monitoring Dashboard.

This module provides generic date filtering utilities that operate on
already-loaded pandas DataFrames. It is intentionally independent of
Excel loading, workbook parsing, Streamlit, and business logic.

Responsibilities
----------------
- Filter the latest record
- Filter by calendar day
- Filter by month and year
- Filter by date range
- Discover available years
- Discover available months
- Safely convert columns to datetime

This module intentionally contains:
- No Streamlit
- No UI
- No workbook parsing
- No Excel loading
- No engineering-specific logic
"""

from __future__ import annotations

from datetime import date
from typing import List

import pandas as pd


class DateFilter:
    """
    Generic date filtering service.

    All methods operate on copies of the supplied DataFrame and never
    mutate caller-owned data.
    """

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_like(dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Return an empty DataFrame preserving the original columns.

        Parameters
        ----------
        dataframe:
            Source DataFrame.

        Returns
        -------
        pandas.DataFrame
        """
        return dataframe.iloc[0:0].copy()

    @staticmethod
    def _valid_dataframe(
        dataframe: pd.DataFrame,
        date_column: str,
    ) -> bool:
        """
        Validate that the DataFrame contains the requested date column.

        Parameters
        ----------
        dataframe:
            Input DataFrame.

        date_column:
            Name of the date column.

        Returns
        -------
        bool
        """
        return (
            not dataframe.empty
            and date_column in dataframe.columns
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ensure_datetime(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
    ) -> pd.DataFrame:
        """
        Return a copy with the specified column converted to datetime.

        Invalid values become NaT.

        Parameters
        ----------
        dataframe:
            Input DataFrame.

        date_column:
            Date column name.

        Returns
        -------
        pandas.DataFrame
        """
        if not self._valid_dataframe(dataframe, date_column):
            return self._empty_like(dataframe)

        result = dataframe.copy()

        result[date_column] = pd.to_datetime(
            result[date_column],
            errors="coerce",
        )

        return result

    def filter_latest(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Return the latest record.

        The latest record is the final row of the DataFrame.

        Parameters
        ----------
        dataframe:
            Input DataFrame.

        Returns
        -------
        pandas.DataFrame
        """
        if dataframe.empty:
            return self._empty_like(dataframe)

        return dataframe.iloc[[-1]].copy()

    def filter_day(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
        selected_date: date,
    ) -> pd.DataFrame:
        """
        Filter rows matching a calendar day.

        Parameters
        ----------
        dataframe:
            Input DataFrame.

        date_column:
            Date column.

        selected_date:
            Target date.

        Returns
        -------
        pandas.DataFrame
        """
        df = self.ensure_datetime(
            dataframe,
            date_column,
        )

        if df.empty:
            return df

        return df.loc[
            df[date_column].dt.date == selected_date
        ].copy()

    def filter_month(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
        month: int,
        year: int,
    ) -> pd.DataFrame:
        """
        Filter rows by month and year.

        Parameters
        ----------
        dataframe:
            Input DataFrame.

        date_column:
            Date column.

        month:
            Month number.

        year:
            Calendar year.

        Returns
        -------
        pandas.DataFrame
        """
        df = self.ensure_datetime(
            dataframe,
            date_column,
        )

        if df.empty:
            return df

        mask = (
            (df[date_column].dt.month == month)
            & (df[date_column].dt.year == year)
        )

        return df.loc[mask].copy()

    def filter_range(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """
        Filter rows between two dates (inclusive).

        Parameters
        ----------
        dataframe:
            Input DataFrame.

        date_column:
            Date column.

        start_date:
            Inclusive start date.

        end_date:
            Inclusive end date.

        Returns
        -------
        pandas.DataFrame
        """
        df = self.ensure_datetime(
            dataframe,
            date_column,
        )

        if df.empty:
            return df

        mask = (
            (df[date_column].dt.date >= start_date)
            & (df[date_column].dt.date <= end_date)
        )

        return df.loc[mask].copy()

    def available_years(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
    ) -> List[int]:
        """
        Return sorted available years.

        Parameters
        ----------
        dataframe:
            Input DataFrame.

        date_column:
            Date column.

        Returns
        -------
        list[int]
        """
        df = self.ensure_datetime(
            dataframe,
            date_column,
        )

        if df.empty:
            return []

        years = (
            df[date_column]
            .dropna()
            .dt.year
            .drop_duplicates()
            .sort_values()
        )

        return years.astype(int).tolist()

    def available_months(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
    ) -> List[int]:
        """
        Return sorted available month numbers.

        Parameters
        ----------
        dataframe:
            Input DataFrame.

        date_column:
            Date column.

        Returns
        -------
        list[int]
        """
        df = self.ensure_datetime(
            dataframe,
            date_column,
        )

        if df.empty:
            return []

        months = (
            df[date_column]
            .dropna()
            .dt.month
            .drop_duplicates()
            .sort_values()
        )

        return months.astype(int).tolist()
