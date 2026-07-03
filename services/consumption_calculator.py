"""
services/consumption_calculator.py

Reusable engineering consumption calculation engine.

This module contains generic numerical calculations that operate on
already-prepared pandas Series objects. It is intentionally independent
of workbook structure, engineering parsing, UI frameworks, and business
logic.

Responsibilities
----------------
- Calculate consumption
- Retrieve latest and previous readings
- Calculate descriptive statistics
- Perform safe arithmetic operations

This module intentionally contains:
- No Streamlit
- No Excel loading
- No workbook parsing
- No UI rendering
- No engineering-specific assumptions
"""

from __future__ import annotations

from typing import Optional

import pandas as pd


class ConsumptionCalculator:
    """
    Generic calculation engine for engineering readings.

    All calculations operate on pandas Series and ignore missing values.
    Input data is never modified.
    """

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _numeric_series(series: pd.Series) -> pd.Series:
        """
        Return a cleaned numeric copy of a series.

        Parameters
        ----------
        series:
            Input pandas Series.

        Returns
        -------
        pandas.Series
            Numeric series with invalid values removed.
        """
        return (
            pd.to_numeric(series.copy(), errors="coerce")
            .dropna()
            .reset_index(drop=True)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_numeric(self, series: pd.Series) -> bool:
        """
        Determine whether a series contains numeric values.

        Parameters
        ----------
        series:
            Input pandas Series.

        Returns
        -------
        bool
            True if at least one valid numeric value exists.
        """
        return not self._numeric_series(series).empty

    def latest_reading(
        self,
        series: pd.Series,
    ) -> Optional[float]:
        """
        Return the latest valid numeric reading.

        Parameters
        ----------
        series:
            Input pandas Series.

        Returns
        -------
        float | None
        """
        values = self._numeric_series(series)

        if values.empty:
            return None

        return float(values.iloc[-1])

    def previous_reading(
        self,
        series: pd.Series,
    ) -> Optional[float]:
        """
        Return the previous valid numeric reading.

        Parameters
        ----------
        series:
            Input pandas Series.

        Returns
        -------
        float | None
        """
        values = self._numeric_series(series)

        if len(values) < 2:
            return None

        return float(values.iloc[-2])

    def calculate_consumption(
        self,
        series: pd.Series,
    ) -> Optional[float]:
        """
        Calculate consumption.

        Consumption is defined as:

            latest reading - previous reading

        Parameters
        ----------
        series:
            Input pandas Series.

        Returns
        -------
        float | None
        """
        latest = self.latest_reading(series)
        previous = self.previous_reading(series)

        return self.difference(latest, previous)

    def maximum(
        self,
        series: pd.Series,
    ) -> Optional[float]:
        """
        Return the maximum valid reading.

        Parameters
        ----------
        series:
            Input pandas Series.

        Returns
        -------
        float | None
        """
        values = self._numeric_series(series)

        if values.empty:
            return None

        return float(values.max())

    def minimum(
        self,
        series: pd.Series,
    ) -> Optional[float]:
        """
        Return the minimum valid reading.

        Parameters
        ----------
        series:
            Input pandas Series.

        Returns
        -------
        float | None
        """
        values = self._numeric_series(series)

        if values.empty:
            return None

        return float(values.min())

    def average(
        self,
        series: pd.Series,
    ) -> Optional[float]:
        """
        Return the average valid reading.

        Parameters
        ----------
        series:
            Input pandas Series.

        Returns
        -------
        float | None
        """
        values = self._numeric_series(series)

        if values.empty:
            return None

        return float(values.mean())

    @staticmethod
    def difference(
        first: Optional[float],
        second: Optional[float],
    ) -> Optional[float]:
        """
        Return the arithmetic difference.

        Parameters
        ----------
        first:
            First numeric value.

        second:
            Second numeric value.

        Returns
        -------
        float | None
            first - second, or None if either value is unavailable.
        """
        if first is None or second is None:
            return None

        return float(first - second)
