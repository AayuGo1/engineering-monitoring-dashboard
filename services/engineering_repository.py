"""
services/engineering_repository.py

Centralized engineering workbook repository.

This module provides the single source of truth for accessing the
engineering worksheet and its parsed metadata. It encapsulates workbook
loading and parser construction so that higher-level services can depend
on a stable, reusable backend interface.

Responsibilities
----------------
- Load the engineering worksheet.
- Construct the EngineeringParser.
- Parse workbook metadata.
- Expose engineering data rows.
- Expose engineering departments.
- Expose engineering meters.
- Expose department- and meter-scoped DataFrames/Series, so that
  higher-level services never slice DataFrames, use column indices,
  or locate departments/meters themselves.

This module intentionally contains:
- No Streamlit
- No Plotly
- No HTML
- No business logic
- No engineering calculations
- No date filtering
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
    WorkbookColumn,
)


class EngineeringRepository:
    """
    Central repository for engineering workbook access.

    The repository eagerly loads and parses the engineering worksheet
    during construction. All parsed objects are cached and reused by
    downstream services. This is the single source of truth for
    engineering workbook data access: higher-level services must
    obtain department metadata, meter metadata, and engineering
    DataFrames/Series exclusively through this class, rather than
    slicing DataFrames, using column indices, or locating departments
    and meters themselves.
    """

    def __init__(self) -> None:
        """
        Initialize the repository.

        The constructor performs the following operations exactly once:

        1. Load the raw engineering worksheet.
        2. Construct the EngineeringParser.
        3. Parse workbook metadata.
        4. Slice engineering data rows.
        5. Cache all parsed objects.
        """
        self._loaded = False

        self._raw_sheet: pd.DataFrame = load_raw_sheet1()

        self._parser = EngineeringParser(self._raw_sheet)

        self._workbook: EngineeringWorkbook = self._parser.parse()

        self._engineering_dataframe: pd.DataFrame = (
            self._raw_sheet.iloc[DATA_START_ROW:]
            .reset_index(drop=True)
        )

        self._departments: List[
            EngineeringDepartment
        ] = self._parser.discover_departments()

        self._meters: List[
            EngineeringMeter
        ] = self._parser.discover_meters()

        self._loaded = True

    # ------------------------------------------------------------------
    # Workbook
    # ------------------------------------------------------------------

    def get_raw_sheet(self) -> pd.DataFrame:
        """
        Return the complete raw engineering worksheet.

        Returns
        -------
        pandas.DataFrame
            Raw worksheet loaded using ``header=None``.
        """
        return self._raw_sheet.copy()

    def get_engineering_dataframe(self) -> pd.DataFrame:
        """
        Return engineering data rows only.

        The returned DataFrame excludes workbook header rows using
        ``DATA_START_ROW``.

        Returns
        -------
        pandas.DataFrame
        """
        return self._engineering_dataframe.copy()

    def get_workbook(self) -> EngineeringWorkbook:
        """
        Return parsed engineering workbook metadata.

        Returns
        -------
        EngineeringWorkbook
        """
        return self._workbook

    # ------------------------------------------------------------------
    # Departments
    # ------------------------------------------------------------------

    def get_departments(
        self,
    ) -> List[EngineeringDepartment]:
        """
        Return all engineering departments.

        Returns
        -------
        list[EngineeringDepartment]
        """
        return list(self._departments)

    def get_department(
        self,
        name: str,
    ) -> Optional[EngineeringDepartment]:
        """
        Return metadata for a single department.

        Parameters
        ----------
        name:
            Department name.

        Returns
        -------
        EngineeringDepartment | None
        """
        return self._parser.get_department(name)

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _require_department(
        self,
        department_name: str,
    ) -> EngineeringDepartment:
        """
        Return a department or raise an exception if it does not exist.

        Centralizes department validation so that every public method
        needing a guaranteed-valid department raises the same
        descriptive error instead of duplicating this check.

        Parameters
        ----------
        department_name:
            Engineering department name.

        Returns
        -------
        EngineeringDepartment

        Raises
        ------
        ValueError
            If the requested department cannot be found.
        """
        department = self.get_department(
            department_name
        )

        if department is None:
            raise ValueError(
                f"Unknown department: '{department_name}'."
            )

        return department

    def _require_meter(
        self,
        department_name: str,
        meter_name: str,
    ) -> EngineeringMeter:
        """
        Return a meter or raise an exception if it does not exist.

        Centralizes meter validation so that every public method
        needing a guaranteed-valid meter raises the same descriptive
        error instead of duplicating this check.

        Parameters
        ----------
        department_name:
            Engineering department name.

        meter_name:
            Engineering meter name.

        Returns
        -------
        EngineeringMeter

        Raises
        ------
        ValueError
            If the requested meter cannot be found.
        """
        meter = self.get_meter(
            department_name,
            meter_name,
        )

        if meter is None:
            raise ValueError(
                f"Unknown meter '{meter_name}' "
                f"in department '{department_name}'."
            )

        return meter

    # ------------------------------------------------------------------
    # Meters
    # ------------------------------------------------------------------

    def get_meters(
        self,
    ) -> List[EngineeringMeter]:
        """
        Return all engineering meters.

        Returns
        -------
        list[EngineeringMeter]
        """
        return list(self._meters)

    def get_meter(
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
        department = self.get_department(
            department_name
        )

        if department is None:
            return None

        normalized = meter_name.strip().casefold()

        for meter in department.meters:
            if meter.meter_name.casefold() == normalized:
                return meter

        return None

    # ------------------------------------------------------------------
    # Engineering Data Access
    # ------------------------------------------------------------------

    def get_department_dataframe(
        self,
        department_name: str,
    ) -> pd.DataFrame:
        """
        Return engineering readings for a department.

        The returned DataFrame always includes the engineering Date
        column in addition to the department's meter columns, so that
        callers can perform date-based filtering (via ``DateFilter``)
        directly against this DataFrame without merging, appending, or
        reconstructing anything themselves.

        The Date column is always resolved through ``get_date_column()``
        (which delegates to the parser) rather than being hardcoded or
        guessed. It is appended after the department's meter columns so
        that column-order-dependent consumers (e.g. code that scans
        ``DataFrame.columns`` looking for the first meaningful reading)
        continue to encounter meter columns before the Date column.

        Parameters
        ----------
        department_name:
            Department name.

        Returns
        -------
        pandas.DataFrame
            A copy of the department's meter columns followed by the
            Date column.

        Raises
        ------
        ValueError
            If the department cannot be found, or if the parser cannot
            identify a date column.
        """
        department = self._require_department(
            department_name
        )

        date_meter = self.get_date_column()

        dataframe = self.get_engineering_dataframe()

        meter_column_indices = [
            meter.column_index
            for meter in department.meters
        ]

        column_indices = list(meter_column_indices)

        if date_meter.column_index not in column_indices:
            column_indices.append(date_meter.column_index)

        return dataframe.iloc[:, column_indices].copy()

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
            A copy of the meter's engineering readings.

        Raises
        ------
        ValueError
            If the department or meter cannot be found.
        """
        meter = self._require_meter(
            department_name,
            meter_name,
        )

        dataframe = self.get_engineering_dataframe()

        return dataframe.iloc[
            :,
            meter.column_index,
        ].copy()

    def get_latest_record(self) -> pd.Series:
        """
        Return the latest engineering record.

        Returns
        -------
        pandas.Series
            A copy of the most recent row of engineering data.

        Raises
        ------
        ValueError
            If no engineering records are available.
        """
        dataframe = self.get_engineering_dataframe()

        if dataframe.empty:
            raise ValueError(
                "No engineering records available."
            )

        return dataframe.iloc[-1].copy()

    # ------------------------------------------------------------------
    # Display Metadata
    # ------------------------------------------------------------------

    def get_department_names(
        self,
    ) -> tuple[str, ...]:
        """
        Return department display names in workbook order.

        Returns
        -------
        tuple[str, ...]
        """
        return tuple(
            department.display_name
            for department in self.get_departments()
        )

    def get_meter_names(
        self,
        department_name: str,
    ) -> tuple[str, ...]:
        """
        Return meter display names for a department.

        Parameters
        ----------
        department_name:
            Department name.

        Returns
        -------
        tuple[str, ...]

        Raises
        ------
        ValueError
            If the department cannot be found.
        """
        department = self._require_department(
            department_name
        )

        return tuple(
            meter.display_name
            for meter in department.meters
        )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_department_count(self) -> int:
        """
        Return the number of parsed departments.

        Returns
        -------
        int
        """
        return len(self._departments)

    def get_meter_count(self) -> int:
        """
        Return the number of parsed engineering meters.

        Returns
        -------
        int
        """
        return len(self._meters)

    def is_loaded(self) -> bool:
        """
        Return whether repository construction completed successfully.

        Returns
        -------
        bool
        """
        return self._loaded

    # ------------------------------------------------------------------
    # Date Metadata
    # ------------------------------------------------------------------

    def get_date_column(self) -> WorkbookColumn:
        """
        Return engineering date column metadata.

        This method delegates directly to
        ``EngineeringParser.get_date_column()`` and never duplicates
        the parser's date-column discovery logic.

        Returns
        -------
        WorkbookColumn
            Parser-defined date column metadata.

        Raises
        ------
        ValueError
            If the parser cannot identify a date column.
        """
        return self._parser.get_date_column()
