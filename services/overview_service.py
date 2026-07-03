"""
services/overview_service.py

Backend service for the Overview Dashboard.

This module provides a lightweight backend façade for the Overview page.
Workbook loading and parsing are delegated to EngineeringRepository.

Responsibilities
----------------
- Expose workbook metadata.
- Expose engineering departments.
- Expose engineering data.
- Expose dashboard summary metadata.
- Expose latest / previous engineering readings.

This module intentionally contains:
- No Streamlit
- No UI
- No Plotly
- No HTML
- No workbook loading
- No workbook parsing
- No department or meter lookup logic

Numerical reading calculations are delegated to ``ConsumptionCalculator``,
mirroring the pattern already used by ``DepartmentAnalysisService``,
``AirCompressorService``, and ``FreonService``: this class never slices
DataFrames by position and never assumes which column holds the Date
values — that is always resolved via
``EngineeringRepository.get_date_column()``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from services.consumption_calculator import ConsumptionCalculator
from services.engineering_parser import (
    EngineeringDepartment,
    EngineeringWorkbook,
)
from services.engineering_repository import EngineeringRepository


# =============================================================================
# Data Models
# =============================================================================


@dataclass(frozen=True)
class DashboardSummary:
    """
    Summary metadata required by dashboard pages.
    """

    workbook_loaded: bool
    department_count: int
    meter_count: int
    latest_record_count: int


# =============================================================================
# Service
# =============================================================================


class OverviewService:
    """
    Backend service powering the Overview Dashboard.

    This service is a thin façade over ``EngineeringRepository``. All
    workbook access — department lookups, meter lookups, and
    DataFrame/Series retrieval — is delegated to the repository. This
    class contains no DataFrame slicing, column index calculations,
    or department/meter discovery logic of its own. Numerical reading
    calculations are delegated to ``ConsumptionCalculator``.
    """

    def __init__(self) -> None:
        """
        Initialize the Overview service.
        """
        self._repository = EngineeringRepository()
        self._calculator = ConsumptionCalculator()

    # ------------------------------------------------------------------
    # Existing Public API (Backward Compatible)
    # ------------------------------------------------------------------

    def get_workbook(self) -> EngineeringWorkbook:
        """
        Return parsed engineering workbook metadata.

        Returns
        -------
        EngineeringWorkbook
        """
        return self._repository.get_workbook()

    def get_departments(self) -> List[EngineeringDepartment]:
        """
        Return all engineering departments.

        Returns
        -------
        list[EngineeringDepartment]
        """
        return self._repository.get_departments()

    def get_department(
        self,
        name: str,
    ) -> Optional[EngineeringDepartment]:
        """
        Return department metadata.

        Parameters
        ----------
        name:
            Department name.

        Returns
        -------
        EngineeringDepartment | None
        """
        return self._repository.get_department(name)

    def get_department_dataframe(
        self,
        name: str,
    ) -> pd.DataFrame:
        """
        Return engineering readings belonging to a department.

        Parameters
        ----------
        name:
            Department name.

        Returns
        -------
        pandas.DataFrame

        Raises
        ------
        ValueError
            If the department cannot be found.
        """
        return self._repository.get_department_dataframe(name)

    def get_meter_dataframe(
        self,
        department_name: str,
        meter_name: str,
    ) -> pd.Series:
        """
        Return engineering readings for a single meter.

        Parameters
        ----------
        department_name:
            Department name.

        meter_name:
            Meter name.

        Returns
        -------
        pandas.Series

        Raises
        ------
        ValueError
            If the department or meter cannot be found.
        """
        return self._repository.get_meter_dataframe(
            department_name,
            meter_name,
        )

    def get_latest_record(self) -> pd.Series:
        """
        Return the latest engineering record.

        Returns
        -------
        pandas.Series

        Raises
        ------
        ValueError
            If no engineering records are available.
        """
        return self._repository.get_latest_record()

    # ------------------------------------------------------------------
    # Dashboard Metadata
    # ------------------------------------------------------------------

    def is_workbook_loaded(self) -> bool:
        """
        Return workbook loading status.

        Returns
        -------
        bool
        """
        return self._repository.is_loaded()

    def get_department_count(self) -> int:
        """
        Return the number of engineering departments.

        Returns
        -------
        int
        """
        return self._repository.get_department_count()

    def get_meter_count(self) -> int:
        """
        Return the number of engineering meters.

        Returns
        -------
        int
        """
        return self._repository.get_meter_count()

    def get_dashboard_summary(self) -> DashboardSummary:
        """
        Return dashboard summary metadata.

        Returns
        -------
        DashboardSummary
        """
        dataframe = self._repository.get_engineering_dataframe()

        return DashboardSummary(
            workbook_loaded=self._repository.is_loaded(),
            department_count=self._repository.get_department_count(),
            meter_count=self._repository.get_meter_count(),
            latest_record_count=len(dataframe),
        )

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _resolve_date_column(self, dataframe: pd.DataFrame) -> Optional[str]:
        """
        Resolve the workbook Date column's identifier, if present.

        The Date column is always resolved through
        ``EngineeringRepository.get_date_column()`` — never assumed,
        never guessed from DataFrame structure (e.g. never
        ``dataframe.columns[0]``). If the repository cannot identify a
        Date column, or the resolved column is not present in
        ``dataframe``, ``None`` is returned so callers can iterate all
        columns instead.

        Parameters
        ----------
        dataframe:
            The DataFrame the resolved column should belong to.

        Returns
        -------
        str | None
            The Date column's identifier, or ``None`` if it cannot be
            resolved for this DataFrame.
        """
        try:
            date_column = self._repository.get_date_column()
        except (ValueError, AttributeError):
            return None

        label = getattr(date_column, "data_column", None)

        if label is not None and label in dataframe.columns:
            return label

        return None

    def _calculate_readings_from_dataframe(
        self,
        dataframe: pd.DataFrame,
    ) -> tuple[float | None, float | None]:
        """
        Calculate the latest and previous readings for a workbook-wide
        DataFrame.

        Mirrors ``DepartmentAnalysisService._calculate_summary_from_dataframe``
        and ``AirCompressorService._calculate_summary_from_dataframe``:
        iterates the DataFrame's columns using ``ConsumptionCalculator``
        and returns the values from the first column that yields a
        valid latest reading, skipping the Date column (when it can be
        resolved) so it is never treated as a numeric reading.

        Parameters
        ----------
        dataframe:
            The engineering records to inspect.

        Returns
        -------
        tuple[float | None, float | None]
            A ``(latest, previous)`` tuple. Returns ``(None, None)``
            if the DataFrame is empty or contains no valid numeric
            readings.
        """
        if dataframe.empty:
            return None, None

        date_column = self._resolve_date_column(dataframe)

        latest: float | None = None
        previous: float | None = None

        for column in dataframe.columns:
            if column == date_column:
                continue

            series = dataframe[column]
            latest = self._calculator.latest_reading(series)

            if latest is not None:
                previous = self._calculator.previous_reading(series)
                break

        return latest, previous

    # ------------------------------------------------------------------
    # Reading APIs
    # ------------------------------------------------------------------

    def get_latest_reading(self) -> Optional[float]:
        """
        Return the latest valid engineering reading across the
        workbook.

        The value is calculated using ``ConsumptionCalculator`` over
        the workbook-wide engineering DataFrame returned by
        ``EngineeringRepository.get_engineering_dataframe()``, using
        the first column (excluding the Date column) that yields a
        valid reading — the same column-resolution strategy used by
        ``DepartmentAnalysisService.get_department_summary()``.

        Returns
        -------
        float | None
            The latest reading, or ``None`` if no engineering data is
            available.
        """
        dataframe = self._repository.get_engineering_dataframe()
        latest, _ = self._calculate_readings_from_dataframe(dataframe)
        return latest

    def get_previous_reading(self) -> Optional[float]:
        """
        Return the previous valid engineering reading across the
        workbook.

        The value is calculated using ``ConsumptionCalculator`` over
        the workbook-wide engineering DataFrame returned by
        ``EngineeringRepository.get_engineering_dataframe()``, using
        the same column resolved by ``get_latest_reading()`` for
        consistency between the two values.

        Returns
        -------
        float | None
            The previous reading, or ``None`` if fewer than two valid
            readings are available.
        """
        dataframe = self._repository.get_engineering_dataframe()
        _, previous = self._calculate_readings_from_dataframe(dataframe)
        return previous
