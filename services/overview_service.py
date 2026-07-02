"""
services/overview_service.py

Backend service for the Overview Dashboard.

This module provides a thin service layer over the engineering parser.
Its responsibility is to expose parsed engineering data in a form that
dashboard pages can consume without knowing anything about the workbook
structure.

Responsibilities
----------------
- Load the raw engineering worksheet.
- Parse the engineering workbook.
- Expose department metadata.
- Expose department data.
- Expose individual meter data.
- Expose the latest engineering record.

This module intentionally contains:
- No Streamlit
- No UI
- No Plotly
- No HTML
- No KPI calculations
- No engineering calculations
- No aggregations
"""

from __future__ import annotations

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


class OverviewService:
    """
    Backend service for the Overview Dashboard.

    The workbook is parsed once during construction and reused for all
    subsequent queries.
    """

    def __init__(self) -> None:
        """Initialize the Overview service."""
        self._raw_sheet = load_raw_sheet1()

        self._parser = EngineeringParser(self._raw_sheet)

        self._workbook = self._parser.parse()

        self._data = self._raw_sheet.iloc[DATA_START_ROW:].reset_index(
            drop=True
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
    # Public API
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
        Return engineering readings for a department.

        The returned DataFrame excludes the workbook header rows and
        contains only the columns belonging to the requested department.

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
            If the meter cannot be found.
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
            Last engineering row.

        Raises
        ------
        ValueError
            If no engineering records exist.
        """
        if self._data.empty:
            raise ValueError(
                "No engineering records available."
            )

        return self._data.iloc[-1].copy()
