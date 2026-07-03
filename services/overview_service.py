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

This module intentionally contains:
- No Streamlit
- No UI
- No Plotly
- No HTML
- No workbook loading
- No workbook parsing
- No engineering calculations
- No DataFrame slicing or column index calculations
- No department or meter lookup logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

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
    or department/meter discovery logic of its own.
    """

    def __init__(self) -> None:
        """
        Initialize the Overview service.
        """
        self._repository = EngineeringRepository()

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
    # Placeholder APIs
    # ------------------------------------------------------------------

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
