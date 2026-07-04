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
- Discover workbook metadata columns (e.g. the Date column)
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

#: Header value used to identify the workbook's Date column.
DATE_COLUMN_HEADER = "date"


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


@dataclass(frozen=True)
class WorkbookColumn:
    """
    Represents a workbook metadata column.

    Unlike ``EngineeringMeter``, which models an engineering measurement
    (e.g. an Air Compressor or PNG meter belonging to a department),
    ``WorkbookColumn`` models non-measurement workbook metadata such as
    ID, Start time, Completion time, Email, Name, Last modified time,
    Date, and Name2 columns.

    Attributes
    ----------
    column_name:
        The canonical (normalized) header value identifying this
        column, e.g. ``"Date"``.
    display_name:
        The header value as it should be displayed to users.
    column_index:
        The zero-based positional index of this column within the raw
        worksheet DataFrame.
    data_column:
        The DataFrame column identifier for this column, suitable for
        indexing into DataFrames returned by the repository.
    """

    column_name: str
    display_name: str
    column_index: int
    data_column: str


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
        self._date_column: WorkbookColumn | None = None

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

        Each department contains exactly one physical meter. Its
        identity is read once, from the meter-row cell at the column
        where the department itself begins (e.g.
        ``"2F3 Air Compressor"``), and exactly one ``EngineeringMeter``
        is constructed for it at that boundary column. Later columns
        that continue the same department -- signalled by a
        blank/merged department cell -- are per-meter data fields
        (e.g. ``"Pressure"``, ``"Air Flow"``, ``"Comp 1 Running
        Hours"``), not additional equipment, and are therefore never
        used to construct another ``EngineeringMeter``. This keeps the
        parser's meter count aligned with the physical meter count in
        the workbook (one ``EngineeringMeter`` per meter) instead of
        one per column. Per-column reading data continues to live in
        the department's own DataFrame and is discovered directly from
        there by the service layer, not from ``EngineeringMeter``
        objects.
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

            # Only a department cell marks a new department boundary.
            # Columns that continue an already-open department (blank
            # department cell, part of the same merged Excel range)
            # are intentionally skipped below: they are data fields of
            # the meter already constructed at the boundary, never a
            # trigger for constructing another one.
            if not department:
                continue

            current_department = department

            # Ignore a department boundary column with no meter-row
            # value; without a meter name there is nothing to
            # construct for this department.
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

    def _find_header_column(
        self,
        header_value: str,
    ) -> Optional[WorkbookColumn]:
        """
        Locate a workbook metadata column by header value.

        Searches only the workbook's header metadata rows (the
        department header row and the meter header row) for a cell
        whose normalized value matches ``header_value``. Engineering
        data rows are never inspected.

        Parameters
        ----------
        header_value:
            The header value to search for. Matching is
            whitespace-stripped and case-insensitive.

        Returns
        -------
        WorkbookColumn | None
            The matching workbook column, or ``None`` if no header
            metadata cell matches ``header_value``.
        """
        target = header_value.strip().casefold()

        department_headers = self._dataframe.iloc[HEADER_ROW]
        meter_headers = self._dataframe.iloc[METER_ROW]

        for column_index in range(self._dataframe.shape[1]):

            department_value = self._normalize(
                department_headers.iloc[column_index]
            )

            meter_value = self._normalize(
                meter_headers.iloc[column_index]
            )

            for candidate in (department_value, meter_value):

                if not candidate:
                    continue

                if candidate.casefold() != target:
                    continue

                return WorkbookColumn(
                    column_name=candidate,
                    display_name=candidate,
                    column_index=column_index,
                    data_column=str(
                        self._dataframe.columns[column_index]
                    ),
                )

        return None

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

    def get_date_column(self) -> WorkbookColumn:
        """
        Discover and return the workbook's Date column.

        The Date column is workbook metadata, not an engineering
        measurement, and is therefore modeled as a ``WorkbookColumn``
        rather than an ``EngineeringMeter``.

        Discovery is performed dynamically by searching the workbook's
        header metadata rows (the department header row and the meter
        header row) for a cell whose normalized value equals ``"date"``
        (whitespace-stripped, case-insensitive). Excel column letters,
        column indices, and header positions are never hardcoded, and
        engineering data rows are never inspected.

        Returns
        -------
        WorkbookColumn
            Metadata describing the workbook's Date column.

        Raises
        ------
        ValueError
            If the workbook does not contain a column whose header
            matches ``"date"``.
        """
        if self._date_column is None:

            date_column = self._find_header_column(DATE_COLUMN_HEADER)

            if date_column is None:
                raise ValueError(
                    "Engineering workbook does not contain a Date "
                    "column."
                )

            self._date_column = date_column

        return self._date_column
