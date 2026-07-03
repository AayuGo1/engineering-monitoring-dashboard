"""
services/department_analysis_service.py

Backend service for the Department Analysis page.

This module provides a high-level service layer between the UI and the
lower-level engineering services. It encapsulates workbook loading,
engineering metadata parsing, date filtering, and engineering
calculations behind a clean public API.

Responsibilities
----------------
- Load the engineering workbook.
- Parse engineering metadata.
- Filter engineering records.
- Calculate department summary values.
- Expose department data for the UI.

This module intentionally contains:
- No Streamlit
- No HTML
- No Plotly
- No UI logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from data.loader import load_raw_sheet1
from services.consumption_calculator import ConsumptionCalculator
from services.date_filter import DateFilter
from services.engineering_parser import (
    DATA_START_ROW,
    EngineeringDepartment,
    EngineeringMeter,
    EngineeringParser,
)


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
    """

    def __init__(self) -> None:
        """Initialize the service."""
        self._raw_sheet = load_raw_sheet1()

        self._parser = EngineeringParser(self._raw_sheet)

        self._parser.parse()

        self._calculator = ConsumptionCalculator()

        self._date_filter = DateFilter()

        self._engineering_data = (
            self._raw_sheet.iloc[DATA_START_ROW:]
            .reset_index(drop=True)
        )

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _find_meter(
        self,
        department_name: str,
        meter_name: str,
    ) -> Optional[EngineeringMeter]:
        """
        Locate a meter within a department.
        """
        department = self.get_department(department_name)

        if department is None:
            return None

        normalized = meter_name.strip().casefold()

        for meter in department.meters:
            if meter.meter_name.casefold() == normalized:
                return meter

        return None

    def _department_columns(
        self,
        department: EngineeringDepartment,
    ) -> List[int]:
        """
        Return engineering column indices belonging to a department.
        """
        return [
            meter.column_index
            for meter in department.meters
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_departments(self) -> List[EngineeringDepartment]:
        """
        Return all engineering departments.
        """
        return self._parser.discover_departments()

    def get_department(
        self,
        name: str,
    ) -> Optional[EngineeringDepartment]:
        """
        Return department metadata.
        """
        return self._parser.get_department(name)

    def get_department_dataframe(
        self,
        name: str,
    ) -> pd.DataFrame:
        """
        Return engineering data for a department.
        """
        department = self.get_department(name)

        if department is None:
            raise ValueError(
                f"Unknown department: '{name}'."
            )

        columns = self._department_columns(department)

        return self._engineering_data.iloc[:, columns].copy()

    def get_meter_dataframe(
        self,
        department_name: str,
        meter_name: str,
    ) -> pd.Series:
        """
        Return engineering readings for a meter.
        """
        meter = self._find_meter(
            department_name,
            meter_name,
        )

        if meter is None:
            raise ValueError(
                f"Unknown meter '{meter_name}' "
                f"in department '{department_name}'."
            )

        return self._engineering_data.iloc[
            :,
            meter.column_index,
        ].copy()

    def get_latest_department_data(
        self,
        name: str,
    ) -> pd.DataFrame:
        """
        Return the latest engineering record for a department.
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

        The caller is responsible for providing the appropriate date
        column name for the supplied DataFrame. Since workbook structure
        is parser-driven and this service intentionally avoids workbook
        assumptions beyond parser metadata, the first column of the
        department DataFrame is treated as the date column only if the
        caller's requested filter can operate on it.
        """
        dataframe = self.get_department_dataframe(
            department_name
        )

        if dataframe.empty:
            return dataframe

        date_column = dataframe.columns[0]

        mode = mode.lower()

        if mode == "latest":
            return self._date_filter.filter_latest(dataframe)

        if mode == "day":
            return self._date_filter.filter_day(
                dataframe,
                date_column,
                selected_date,
            )

        if mode == "month":
            return self._date_filter.filter_month(
                dataframe,
                date_column,
                month,
                year,
            )

        if mode == "range":
            return self._date_filter.filter_range(
                dataframe,
                date_column,
                start_date,
                end_date,
            )

        return dataframe.copy()

    def get_department_summary(
        self,
        department_name: str,
    ) -> DepartmentSummary:
        """
        Return summary information for a department.

        Numerical values are calculated using ConsumptionCalculator.
        """
        dataframe = self.get_department_dataframe(
            department_name
        )

        if dataframe.empty:
            return DepartmentSummary(
                latest_reading=None,
                previous_reading=None,
                consumption=None,
                meter_count=0,
            )

        latest = None
        previous = None
        consumption = None

        for column in dataframe.columns:
            series = dataframe[column]

            latest = self._calculator.latest_reading(series)

            previous = self._calculator.previous_reading(series)

            consumption = (
                self._calculator.calculate_consumption(
                    series
                )
            )

            if latest is not None:
                break

        department = self.get_department(
            department_name
        )

        meter_count = (
            len(department.meters)
            if department is not None
            else 0
        )

        return DepartmentSummary(
            latest_reading=latest,
            previous_reading=previous,
            consumption=consumption,
            meter_count=meter_count,
        )
