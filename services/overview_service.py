"""
services/overview_service.py

Backend service for the Overview Dashboard.

This module provides a single backend interface for the Overview page.
It encapsulates workbook loading, engineering parsing, and exposes
metadata and engineering data through a stable, strongly-typed API.

Responsibilities
----------------
- Load the raw engineering worksheet.
- Parse the engineering workbook.
- Expose workbook metadata.
- Expose engineering departments.
- Expose engineering data.
- Expose dashboard summary metadata.

This module intentionally contains:
- No Streamlit
- No UI
- No Plotly
- No HTML
- No engineering calculations
- No KPI calculations
- No aggregation logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from data.loader import load_raw_sheet1
from services.engineering_parser import (
    DATA_START_ROW,
    EngineeringDepartment,
    EngineeringMeter,
    EngineeringParser,
    EngineeringWorkbook,
)


# =============================================================================
# Data Models
# =============================================================================


@dataclass(frozen=True)
class DashboardSummary:
    """
    Summary metadata required by dashboard pages.

    Attributes
    ----------
    workbook_loaded:
        Indicates whether the workbook was successfully loaded.

    department_count:
        Number of discovered engineering departments.

    meter_count:
        Number of discovered engineering meters.

    latest_record_count:
        Number of engineering records available after the header rows.
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

    The workbook is loaded and parsed once during construction. Parsed
    metadata is cached inside the service instance.
    """

    def __init__(self) -> None:
        """Initialize the Overview service."""

        self._workbook_loaded = False

        self._raw_sheet = load_raw_sheet1()

        self._parser = EngineeringParser(self._raw_sheet)

        self._workbook = self._parser.parse()

        self._data = (
            self._raw_sheet.iloc[DATA_START_ROW:]
            .reset_index(drop=True)
        )

        self._workbook_loaded = True

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

        Parameters
        ----------
        department_name:
            Department name.

        meter_name:
            Meter name.

        Returns
        -------
        EngineeringMeter | None
        """
        department = self.get_department(department_name)

        if department is None:
            return None

        normalized = meter_name.strip().casefold()

        for meter in department.meters:
            if meter.meter_name.casefold() == normalized:
                return meter

        return None

    # ------------------------------------------------------------------
    # Existing Public API (Backward Compatible)
    # ------------------------------------------------------------------

    def get_workbook(self) -> EngineeringWorkbook:
        """
        Return the parsed engineering workbook.

        Returns
        -------
        EngineeringWorkbook
        """
        return self._workbook

    def get_departments(self) -> List[EngineeringDepartment]:
        """
        Return all engineering departments.

        Returns
        -------
        list[EngineeringDepartment]
        """
        return self._parser.discover_departments()

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
        return self._parser.get_department(name)

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
        department = self.get_department(name)

        if department is None:
            raise ValueError(
                f"Unknown department: '{name}'."
            )

        column_indices = [
            meter.column_index
            for meter in department.meters
        ]

        return self._data.iloc[:, column_indices].copy()

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
            If the requested meter cannot be found.
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

        return self._data.iloc[:, meter.column_index].copy()

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
        if self._data.empty:
            raise ValueError(
                "No engineering records available."
            )

        return self._data.iloc[-1].copy()

    # ------------------------------------------------------------------
    # Extended Dashboard API
    # ------------------------------------------------------------------

    def is_workbook_loaded(self) -> bool:
        """
        Return workbook loading status.

        Returns
        -------
        bool
        """
        return self._workbook_loaded

    def get_department_count(self) -> int:
        """
        Return the number of engineering departments.

        Returns
        -------
        int
        """
        return len(self.get_departments())

    def get_meter_count(self) -> int:
        """
        Return the total number of engineering meters.

        Returns
        -------
        int
        """
        return sum(
            len(department.meters)
            for department in self.get_departments()
        )

    def get_dashboard_summary(self) -> DashboardSummary:
        """
        Return summary metadata required by dashboard pages.

        Returns
        -------
        DashboardSummary
        """
        return DashboardSummary(
            workbook_loaded=self.is_workbook_loaded(),
            department_count=self.get_department_count(),
            meter_count=self.get_meter_count(),
            latest_record_count=len(self._data),
        )

    def get_latest_reading(self) -> None:
        """
        Placeholder for future latest reading calculation.

        Returns
        -------
        None
        """
        return None

    def get_previous_reading(self) -> None:
        """
        Placeholder for future previous reading calculation.

        Returns
        -------
        None
        """
        return None
