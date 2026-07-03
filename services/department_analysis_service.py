"""
services/department_analysis_service.py

Backend service for the Department Analysis page.

This module provides a thin orchestration layer between the UI and
the lower-level engineering services. It no longer owns any data
access: ``EngineeringRepository`` is the single source of truth for
workbook data, department discovery, meter discovery, and column
metadata. This service only coordinates repository lookups with
``DateFilter`` for date-based filtering and ``ConsumptionCalculator``
for numerical summaries.

Responsibilities
----------------
- Delegate department and meter lookups to ``EngineeringRepository``.
- Filter engineering records using ``DateFilter``.
- Calculate department summary values using ``ConsumptionCalculator``.
- Expose department data for the UI.

This module intentionally contains:
- No Streamlit
- No HTML
- No Plotly
- No UI logic
- No workbook loading
- No DataFrame slicing or column index calculations
- No department or meter discovery logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from services.engineering_repository import EngineeringRepository
from services.consumption_calculator import ConsumptionCalculator
from services.date_filter import DateFilter
from services.engineering_parser import EngineeringDepartment


@dataclass(frozen=True)
class DepartmentSummary:
    """
    Summary information for a department.

    Attributes
    ----------
    latest_reading:
        Latest valid engineering reading.

    previous_reading:
        Previous valid engineering reading.

    consumption:
        Difference between latest and previous readings.

    meter_count:
        Number of engineering meters belonging to the department.
    """

    latest_reading: float | None
    previous_reading: float | None
    consumption: float | None
    meter_count: int


class DepartmentAnalysisService:
    """
    Backend service powering the Department Analysis page.

    This service is a thin orchestration layer. All data access is
    delegated to ``EngineeringRepository``; this class only combines
    repository results with ``DateFilter`` and
    ``ConsumptionCalculator`` to answer UI-facing questions.
    """

    def __init__(self) -> None:
        """Initialize the service and its collaborators."""
        self._repository = EngineeringRepository()
        self._calculator = ConsumptionCalculator()
        self._date_filter = DateFilter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_departments(self) -> List[EngineeringDepartment]:
        """
        Return all engineering departments.

        Returns
        -------
        List[EngineeringDepartment]
            All departments known to the repository.
        """
        return self._repository.get_departments()

    def get_department(self, name: str) -> Optional[EngineeringDepartment]:
        """
        Return department metadata.

        Parameters
        ----------
        name:
            The department name to look up.

        Returns
        -------
        Optional[EngineeringDepartment]
            The matching department, or ``None`` if it does not exist.
        """
        return self._repository.get_department(name)

    def get_department_dataframe(self, name: str) -> pd.DataFrame:
        """
        Return engineering data for a department.

        Parameters
        ----------
        name:
            The department name to look up.

        Returns
        -------
        pandas.DataFrame
            The department's engineering records, as provided by the
            repository.
        """
        return self._repository.get_department_dataframe(name)

    def get_meter_dataframe(
        self,
        department_name: str,
        meter_name: str,
    ) -> pd.Series:
        """
        Return engineering readings for a meter.

        Parameters
        ----------
        department_name:
            The owning department's name.
        meter_name:
            The meter name to look up.

        Returns
        -------
        pandas.Series
            The meter's engineering readings, as provided by the
            repository.
        """
        return self._repository.get_meter_dataframe(department_name, meter_name)

    def get_latest_department_data(self, name: str) -> pd.DataFrame:
        """
        Return the latest engineering record for a department.

        Parameters
        ----------
        name:
            The department name to look up.

        Returns
        -------
        pandas.DataFrame
            A single-row DataFrame containing the latest record for
            the department.
        """
        dataframe = self.get_department_dataframe(name)
        return self._date_filter.filter_latest(dataframe)

    def get_filtered_department_data(
        self,
        department_name: str,
        mode: str,
        *,
        selected_date=None,
        month=None,
        year=None,
        start_date=None,
        end_date=None,
    ) -> pd.DataFrame:
        """
        Return filtered department data.

        The department DataFrame is obtained from
        ``EngineeringRepository.get_department_dataframe()``, which
        always includes the workbook Date column alongside the
        department's meter columns. The Date column identifier used
        for filtering is always resolved through
        ``EngineeringRepository.get_date_column()`` — never assumed,
        never guessed from DataFrame structure (e.g. never
        ``dataframe.columns[0]``), and never duplicated here.

        Parameters
        ----------
        department_name:
            The department name to look up.
        mode:
            The filter mode: ``"latest"``, ``"day"``, ``"month"``, or
            ``"range"``. Any other value returns the department's
            unfiltered data.
        selected_date:
            The date to filter by when ``mode`` is ``"day"``.
        month:
            The month to filter by when ``mode`` is ``"month"``.
        year:
            The year to filter by when ``mode`` is ``"month"``.
        start_date:
            The inclusive range start when ``mode`` is ``"range"``.
        end_date:
            The inclusive range end when ``mode`` is ``"range"``.

        Returns
        -------
        pandas.DataFrame
            The filtered engineering records for the department.

        Raises
        ------
        ValueError
            If the department cannot be found, or if the repository
            cannot identify a date column.
        """
        dataframe = self.get_department_dataframe(department_name)

        if dataframe.empty:
            return dataframe

        mode = mode.lower()

        if mode == "latest":
            return self._date_filter.filter_latest(dataframe)

        if mode in ("day", "month", "range"):
            date_column = self._repository.get_date_column()
            data_column = date_column.data_column

            if mode == "day":
                return self._date_filter.filter_day(
                    dataframe,
                    data_column,
                    selected_date,
                )

            if mode == "month":
                return self._date_filter.filter_month(
                    dataframe,
                    data_column,
                    month,
                    year,
                )

            return self._date_filter.filter_range(
                dataframe,
                data_column,
                start_date,
                end_date,
            )

        return dataframe.copy()

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _calculate_summary_from_dataframe(
        self,
        dataframe: pd.DataFrame,
    ) -> tuple[
        float | None,
        float | None,
        float | None,
    ]:
        """
        Calculate latest, previous, and consumption values for a
        department DataFrame.

        Iterates the DataFrame's columns using ``ConsumptionCalculator``
        and returns the values from the first column that yields a
        valid latest reading.

        Parameters
        ----------
        dataframe:
            The department's engineering records.

        Returns
        -------
        tuple[float | None, float | None, float | None]
            A ``(latest, previous, consumption)`` tuple. Returns
            ``(None, None, None)`` if the DataFrame is empty or
            contains no valid numeric readings.
        """
        latest = None
        previous = None
        consumption = None

        for column in dataframe.columns:
            series = dataframe[column]

            latest = self._calculator.latest_reading(series)
            previous = self._calculator.previous_reading(series)
            consumption = self._calculator.calculate_consumption(series)

            if latest is not None:
                break

        return latest, previous, consumption

    def get_department_summary(self, department_name: str) -> DepartmentSummary:
        """
        Return summary information for a department.

        Numerical values are calculated using ``ConsumptionCalculator``.
        Meter counts are sourced from the department metadata returned
        by the repository.

        Parameters
        ----------
        department_name:
            The department name to summarize.

        Returns
        -------
        DepartmentSummary
            The department's latest reading, previous reading,
            consumption, and meter count.
        """
        dataframe = self.get_department_dataframe(department_name)

        if dataframe.empty:
            return DepartmentSummary(
                latest_reading=None,
                previous_reading=None,
                consumption=None,
                meter_count=0,
            )

        latest, previous, consumption = self._calculate_summary_from_dataframe(
            dataframe
        )

        department = self.get_department(department_name)

        meter_count = (
            len(department.meters) if department is not None else 0
        )

        return DepartmentSummary(
            latest_reading=latest,
            previous_reading=previous,
            consumption=consumption,
            meter_count=meter_count,
        )
