"""
services/engineering_parser.py

Engineering parser for Sheet 1 of the Engineering Monitoring Dashboard.

This module interprets the raw Sheet 1 DataFrame (loaded with header=None)
and converts the workbook structure into strongly typed engineering models.

Responsibilities
----------------
- Interpret the fixed workbook schema
- Discover departments
- Discover meters
- Build a structured engineering workbook model

This module intentionally contains:
- No Streamlit
- No plotting
- No UI
- No calculations
- No aggregation
- No business logic
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd


# =============================================================================
# Workbook Structure Constants
# =============================================================================

#: Zero-based department header row.
HEADER_ROW = 0

#: Zero-based meter header row.
METER_ROW = 1

#: First engineering data row.
DATA_START_ROW = 2


# =============================================================================
# Data Models
# =============================================================================


@dataclass(frozen=True)
class EngineeringMeter:
    """
    Represents an engineering meter.
    """

    meter_name: str
    display_name: str
    column_index: int
    data_column: str


@dataclass(frozen=True)
class EngineeringDepartment:
    """
    Represents an engineering department and its meters.
    """

    department_name: str
    display_name: str
    meters: tuple[EngineeringMeter, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EngineeringWorkbook:
    """
    Parsed representation of the engineering workbook.
    """

    departments: tuple[EngineeringDepartment, ...]
    header_row: int
    data_start_row: int


# =============================================================================
# Parser
# =============================================================================


class EngineeringParser:
    """
    Parser for the engineering section of Sheet 1.

    Parameters
    ----------
    dataframe:
        Raw Sheet 1 DataFrame loaded using ``header=None``.
    """

    def __init__(self, dataframe: pd.DataFrame) -> None:
        self._dataframe = dataframe

        self._departments: List[EngineeringDepartment] | None = None
        self._meters: List[EngineeringMeter] | None = None
        self._workbook: EngineeringWorkbook | None = None

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _normalize(value: object) -> str:
        """
        Normalize header values.

        Parameters
        ----------
        value:
            Raw workbook value.

        Returns
        -------
        str
            Normalized string.
        """
        if pd.isna(value):
            return ""

        return str(value).strip()

    def _build_metadata(self) -> None:
        """
        Parse department and meter metadata from the fixed workbook schema.
        """
        if self._departments is not None:
            return

        department_headers = self._dataframe.iloc[HEADER_ROW]
        meter_headers = self._dataframe.iloc[METER_ROW]

        department_map: Dict[str, List[EngineeringMeter]] = {}

        current_department = ""

        for column_index in range(self._dataframe.shape[1]):

            department = self._normalize(
                department_headers.iloc[column_index]
            )

            meter = self._normalize(
                meter_headers.iloc[column_index]
            )

            # Ignore completely blank columns.
            if not department and not meter:
                continue

            # Propagate merged department headers.
            if department:
                current_department = department

            # Ignore columns before the first department.
            if not current_department:
                continue

            # Skip department columns that do not contain a meter.
            if not meter:
                continue

            engineering_meter = EngineeringMeter(
                meter_name=meter,
                display_name=meter,
                column_index=column_index,
                data_column=str(self._dataframe.columns[column_index]),
            )

            department_map.setdefault(
                current_department,
                [],
            ).append(engineering_meter)

        departments: List[EngineeringDepartment] = []
        meters: List[EngineeringMeter] = []

        for department_name, department_meters in department_map.items():

            departments.append(
                EngineeringDepartment(
                    department_name=department_name,
                    display_name=department_name,
                    meters=tuple(department_meters),
                )
            )

            meters.extend(department_meters)

        self._departments = departments
        self._meters = meters

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def parse(self) -> EngineeringWorkbook:
        """
        Parse the engineering workbook structure.

        Returns
        -------
        EngineeringWorkbook
            Parsed workbook metadata.
        """
        if self._workbook is None:

            self._build_metadata()

            self._workbook = EngineeringWorkbook(
                departments=tuple(self._departments),
                header_row=HEADER_ROW,
                data_start_row=DATA_START_ROW,
            )

        return self._workbook

    def discover_departments(self) -> List[EngineeringDepartment]:
        """
        Return discovered engineering departments.

        Returns
        -------
        list[EngineeringDepartment]
        """
        self._build_metadata()
        return list(self._departments)

    def discover_meters(self) -> List[EngineeringMeter]:
        """
        Return discovered engineering meters.

        Returns
        -------
        list[EngineeringMeter]
        """
        self._build_metadata()
        return list(self._meters)

    def get_department(
        self,
        name: str,
    ) -> Optional[EngineeringDepartment]:
        """
        Retrieve department metadata by name.

        Parameters
        ----------
        name:
            Department name.

        Returns
        -------
        EngineeringDepartment | None
            Matching department, otherwise None.
        """
        normalized = name.strip().casefold()

        for department in self.discover_departments():
            if department.department_name.casefold() == normalized:
                return department

        return None
