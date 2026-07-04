"""
services/air_compressor_service.py

Backend service for Air Compressor engineering data.

This module provides a thin orchestration layer between the UI and
the lower-level engineering services. It owns no data access of its
own: ``EngineeringRepository`` is the single source of truth for
workbook data, department discovery, meter discovery, and column
metadata. This service only coordinates repository lookups with
``DateFilter`` for date-based filtering and ``ConsumptionCalculator``
for numerical summaries, following the same pattern used by
``DepartmentAnalysisService``.

Column Label Convention
------------------------
``EngineeringRepository`` returns DataFrames whose columns are the
*original* underlying DataFrame labels (integers, since the workbook
is loaded with ``header=None``). ``EngineeringParser`` exposes two
different identifiers for a column:

- ``column_index`` (``int``): the positional index, which also equals
  the actual DataFrame column label for these frames.
- ``data_column`` (``str``): a *stringified* version of that same
  label, intended for display/reference purposes.

Because the underlying DataFrame columns are integers, ``data_column``
must never be used to index into a DataFrame returned by
``EngineeringRepository`` (``frame[date_column.data_column]`` fails to
match, since ``"3" != 3``). This service always indexes DataFrames —
for both data columns and the Date column — using ``column_index``
(or the equivalent raw DataFrame column labels discovered from the
department's DataFrame), so the two identifiers are never mixed.

Section Structure — Dynamic Field Discovery
--------------------------------------------
Earlier versions of this service assumed the Air Compressor section
was modeled as one meter *per logical reading* ("Pressure", "Air
Flow", "Air Consumption", "Running Hours", "Running Load"), each
resolved via ``EngineeringRepository.get_meter()`` by that hardcoded
name.

The workbook does not model the section that way. It contains a
single Air Compressor meter (e.g. "2F3 Air Compressor"); pressure,
flow, consumption, running hours, and running load are separate
*columns* within that meter's data, not separate named meters. Since
``EngineeringMeter`` carries only ``meter_name``, ``display_name``,
``column_index``, and ``data_column`` — no per-column role metadata —
there is no name to search for beyond the meter itself.

This service therefore:

1. Resolves the section's meter dynamically — it looks up whichever
   meter(s) the "Air Compressor" department actually contains via
   ``EngineeringRepository.get_meter_names()`` / ``get_meter()``,
   rather than assuming a specific meter name.
2. Discovers the section's data columns dynamically from the
   department's DataFrame (every column except the Date column, in
   workbook order), rather than assuming fixed column identities.
3. Addresses the five logical readings by *position* within that
   discovered column list (``AirCompressorFieldPositions``), since
   position in workbook order is the only distinguishing signal
   available. Positions are configuration, overridable at
   construction time — the same philosophy the previous hardcoded
   meter names followed, just applied to the structure the workbook
   actually has.

Bugfix note — graceful handling of missing positions
-----------------------------------------------------
A given workbook is not guaranteed to actually contain data columns
for all five logical readings that ``AirCompressorFieldPositions``
assumes -- the section's discovered data-column count can be fewer
(or more) than the five configured positions. ``_resolve_field_column``
previously treated a configured position beyond what the workbook
actually contains as an error and raised
``ValueError("Field position X is out of range ...")``, which
propagated out of whichever ``get_*_trend()`` method was called and
crashed page rendering.

This mirrors, and is fixed the same way as, the equivalent method in
``FreonService``: resolving a position the workbook doesn't provide is
not an error condition — it simply means that particular reading is
absent from this workbook. ``_resolve_field_column`` now returns
``None`` in that case, and ``_get_filtered_field_trend`` reports the
reading as unavailable by returning an empty ``pandas.Series`` (which
callers already render as an empty/"no data" chart), instead of
raising.

This module intentionally contains:
- No Streamlit
- No HTML
- No Plotly
- No UI logic
- No workbook loading
- No EngineeringParser interaction
- No DataFrame slicing by position outside of the dynamic column
  discovery described above
- No hardcoded meter-name search logic
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

import pandas as pd

from services.consumption_calculator import ConsumptionCalculator
from services.date_filter import DateFilter
from services.engineering_parser import EngineeringDepartment, EngineeringMeter
from services.engineering_repository import EngineeringRepository


DEFAULT_SECTION_DEPARTMENT_NAME = "Air Compressor"


@dataclass(frozen=True)
class AirCompressorFieldPositions:
    """
    Positional indices, within the Air Compressor section's
    dynamically discovered data columns (Date column excluded, in
    workbook order), of each logical reading.

    The workbook models the Air Compressor section as a single meter
    whose pressure, flow, consumption, running hours, and running
    load readings live in separate columns rather than as separate
    named meters. Since ``EngineeringMeter`` exposes no per-column
    role metadata, "the pressure column" can only be identified by
    its position among the section's data columns. These positions
    are configuration, overridable at ``AirCompressorService``
    construction time, rather than hardcoded meter-name literals
    scattered through the class.

    Not every workbook is guaranteed to provide data columns for all
    five positions below. A workbook with fewer discovered data
    columns than a given position requires simply does not have that
    reading; see ``AirCompressorService._resolve_field_column``.
    """

    pressure: int = 0
    air_flow: int = 1
    air_consumption: int = 2
    running_hours: int = 3
    running_load: int = 4


@dataclass(frozen=True)
class AirCompressorSummary:
    """
    Summary information for the Air Compressor engineering section.

    Attributes
    ----------
    latest_reading:
        Latest valid engineering reading.

    previous_reading:
        Previous valid engineering reading.

    consumption:
        Difference between latest and previous readings.

    meter_count:
        Number of engineering meters belonging to the Air Compressor
        section, as discovered from the workbook. With the section
        modeled as a single meter, this is ordinarily ``1``.
    """

    latest_reading: float | None
    previous_reading: float | None
    consumption: float | None
    meter_count: int


class AirCompressorService:
    """
    Backend service powering Air Compressor engineering views.

    This service is a thin orchestration layer. All data access is
    delegated to ``EngineeringRepository``; this class only combines
    repository results with ``DateFilter`` and ``ConsumptionCalculator``
    to answer UI-facing questions about the Air Compressor engineering
    section. The section's meter and data columns are discovered
    dynamically from the workbook rather than assumed from hardcoded
    meter names.
    """

    def __init__(
        self,
        department_name: str = DEFAULT_SECTION_DEPARTMENT_NAME,
        field_positions: AirCompressorFieldPositions = AirCompressorFieldPositions(),
    ) -> None:
        """
        Initialize the service and its collaborators.

        Parameters
        ----------
        department_name:
            The workbook department name representing the Air
            Compressor section. Defaults to
            ``DEFAULT_SECTION_DEPARTMENT_NAME``.

        field_positions:
            The positions, among the section's dynamically discovered
            data columns, of each logical reading. Defaults to
            ``AirCompressorFieldPositions()``.
        """
        self._repository = EngineeringRepository()
        self._calculator = ConsumptionCalculator()
        self._date_filter = DateFilter()

        self._department_name = department_name
        self._field_positions = field_positions

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _resolve_department(self) -> EngineeringDepartment:
        """
        Resolve the Air Compressor department via repository metadata.

        Returns
        -------
        EngineeringDepartment
            The department matching ``self._department_name``.

        Raises
        ------
        ValueError
            If no department with that name exists in the workbook.
            The error lists the department names that do exist, so a
            naming mismatch is immediately diagnosable.
        """
        department = self._repository.get_department(
            self._department_name
        )

        if department is not None:
            return department

        available = ", ".join(
            self._repository.get_department_names()
        ) or "(none discovered)"

        raise ValueError(
            f"Unable to resolve the '{self._department_name}' "
            f"department. Departments found instead: {available}."
        )

    def _resolve_section_meter(self) -> EngineeringMeter:
        """
        Resolve the Air Compressor section's meter dynamically.

        Rather than searching for a specific hardcoded meter name
        (e.g. "2F3 Air Compressor"), this takes whichever meter(s) the
        repository actually discovered within the Air Compressor
        department and resolves the first one, since the section is
        modeled as a single meter. This keeps the service correct
        regardless of what that meter happens to be named in the
        workbook.

        Returns
        -------
        EngineeringMeter
            The section's meter.

        Raises
        ------
        ValueError
            If the department cannot be resolved, or if it has no
            meters registered.
        """
        self._resolve_department()

        meter_names = list(
            self._repository.get_meter_names(self._department_name)
        )

        if not meter_names:
            raise ValueError(
                f"The '{self._department_name}' department has no "
                "meters registered in the workbook."
            )

        meter = self._repository.get_meter(
            self._department_name,
            meter_names[0],
        )

        if meter is not None:
            return meter

        raise ValueError(
            f"Unable to resolve meter '{meter_names[0]}' in the "
            f"'{self._department_name}' department."
        )

    def _get_field_columns(self) -> List[int]:
        """
        Return the Air Compressor section's data columns, discovered
        dynamically from the department's DataFrame.

        Every column of the department DataFrame except the Date
        column is treated as a data column (pressure, flow,
        consumption, running hours, running load, or any other
        reading the workbook happens to contain), in workbook order.
        This replaces hardcoded per-reading meter-name lookups with
        structure read directly from the data.

        Returns
        -------
        List[int]
            The section's non-Date column labels, in workbook order.
            Empty if the department has no data.

        Raises
        ------
        ValueError
            If the department or its meter cannot be resolved.
        """
        self._resolve_section_meter()

        dataframe = self._repository.get_department_dataframe(
            self._department_name
        )

        if dataframe.empty:
            return []

        date_label = self._repository.get_date_column().column_index

        return [
            column for column in dataframe.columns if column != date_label
        ]

    def _resolve_field_column(self, position: int) -> Optional[int]:
        """
        Resolve the DataFrame column label for a field at a given
        position among the section's dynamically discovered data
        columns.

        The number of data columns a workbook actually provides for
        this section is not guaranteed to match the five logical
        readings (pressure, air flow, air consumption, running hours,
        running load) that ``AirCompressorFieldPositions`` defaults
        assume -- a workbook may expose fewer (or more) data columns
        than that. Rather than treating a configured position beyond
        what the workbook actually contains as an error, this method
        reports the reading as unavailable so callers can degrade
        gracefully (see ``_get_filtered_field_trend``), instead of
        raising and crashing page rendering.

        Parameters
        ----------
        position:
            The zero-based position, within the section's discovered
            data columns, of the desired reading.

        Returns
        -------
        int | None
            The corresponding DataFrame column label, or ``None`` if
            ``position`` falls outside the section's dynamically
            discovered data columns (i.e. the workbook does not
            provide that many readings for this section).

        Raises
        ------
        ValueError
            If the department or its meter cannot be resolved.
        """
        columns = self._get_field_columns()

        if position < 0 or position >= len(columns):
            return None

        return columns[position]

    def _calculate_summary_from_dataframe(
        self,
        dataframe: pd.DataFrame,
        date_column: int,
    ) -> tuple[
        float | None,
        float | None,
        float | None,
    ]:
        """
        Calculate latest, previous, and consumption values for a
        department DataFrame.

        Mirrors
        ``DepartmentAnalysisService._calculate_summary_from_dataframe``:
        iterates the DataFrame's columns using ``ConsumptionCalculator``
        and returns the values from the first column that yields a
        valid latest reading, skipping the Date column so it is never
        treated as a numeric reading.

        Parameters
        ----------
        dataframe:
            The Air Compressor section's engineering records.

        date_column:
            The Date column's ``column_index`` (the actual DataFrame
            column label), excluded from iteration.

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
            if column == date_column:
                continue

            series = dataframe[column]

            latest = self._calculator.latest_reading(series)
            previous = self._calculator.previous_reading(series)
            consumption = self._calculator.calculate_consumption(series)

            if latest is not None:
                break

        return latest, previous, consumption

    def _get_filtered_field_trend(
        self,
        position: int,
        mode: str,
        *,
        selected_date: Optional[date] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.Series:
        """
        Return a field's readings, optionally filtered using ``DateFilter``.

        Single reusable helper backing every trend method
        (``get_pressure_trend``, ``get_flow_trend``,
        ``get_energy_consumption_trend``, ``get_running_hours_trend``,
        ``get_running_load_trend``), so the filtering-orchestration
        logic exists in exactly one place. Mirrors
        ``DepartmentAnalysisService.get_filtered_department_data``: the
        Date column is always resolved through
        ``EngineeringRepository.get_date_column()``, never assumed or
        duplicated here, and the field column is always resolved
        through ``_resolve_field_column()`` (dynamic discovery from
        the department DataFrame), never a hardcoded meter-name
        lookup. Both are indexed into the department DataFrame using
        their actual DataFrame column labels, never a stringified
        ``data_column``, so the two identifiers are never mixed.

        If ``position`` does not correspond to a data column the
        workbook actually provides for this section, this is not
        treated as an error: the reading is simply absent from this
        workbook, and an empty series is returned, exactly as when the
        department itself has no data.

        Parameters
        ----------
        position:
            The zero-based position, within the section's discovered
            data columns, of the desired reading.

        mode:
            The filter mode: ``"latest"``, ``"day"``, ``"month"``, or
            ``"range"``. Any other value returns the field's
            unfiltered readings.

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
        pandas.Series
            The field's (optionally filtered) readings, indexed by
            the corresponding engineering Date values so charts built
            from this Series plot against real dates instead of row
            numbers. Empty if the department has no data or if
            ``position`` addresses a reading the workbook does not
            provide for this section.

        Raises
        ------
        ValueError
            If the department or meter cannot be resolved, or if the
            repository cannot identify a Date column.
        """
        department_frame = self._repository.get_department_dataframe(
            self._department_name
        )

        if department_frame.empty:
            return pd.Series(dtype=float)

        field_label = self._resolve_field_column(position)

        if field_label is None:
            return pd.Series(dtype=float)

        date_column = self._repository.get_date_column()
        date_label = date_column.column_index

        subset = department_frame[[field_label, date_label]].copy()

        normalized_mode = mode.lower()

        if normalized_mode == "latest":
            filtered = self._date_filter.filter_latest(subset)
        elif normalized_mode == "day":
            filtered = self._date_filter.filter_day(
                subset, date_label, selected_date
            )
        elif normalized_mode == "month":
            filtered = self._date_filter.filter_month(
                subset, date_label, month, year
            )
        elif normalized_mode == "range":
            filtered = self._date_filter.filter_range(
                subset, date_label, start_date, end_date
            )
        else:
            filtered = subset

        if filtered.empty:
            return pd.Series(dtype=float)

        return filtered.set_index(date_label)[field_label]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_available_meters(self) -> List[str]:
        """
        Return labels for the Air Compressor section's dynamically
        discovered data columns.

        With the section modeled as a single meter, these are not
        separate meter names but the section's individual reading
        columns (pressure, flow, consumption, running hours, running
        load, or whatever else the workbook happens to contain),
        labeled by their raw DataFrame column values and returned in
        workbook order.

        Returns
        -------
        List[str]
            String labels of the Air Compressor section's data
            columns, in workbook order.

        Raises
        ------
        ValueError
            If the Air Compressor department or its meter cannot be
            resolved.
        """
        columns = self._get_field_columns()
        return [str(column) for column in columns]

    def get_compressor_dataframe(self) -> pd.DataFrame:
        """
        Return engineering data for the Air Compressor section.

        Returns
        -------
        pandas.DataFrame
            The Air Compressor section's data columns plus the
            workbook's Date column, exactly as provided by
            ``EngineeringRepository.get_department_dataframe()``.

        Raises
        ------
        ValueError
            If the Air Compressor department cannot be resolved.
        """
        self._resolve_department()

        return self._repository.get_department_dataframe(
            self._department_name
        )

    def get_latest_compressor_readings(self) -> pd.DataFrame:
        """
        Return the latest engineering record for the Air Compressor
        section.

        Returns
        -------
        pandas.DataFrame
            A single-row DataFrame containing the latest record for
            the Air Compressor section.

        Raises
        ------
        ValueError
            If the Air Compressor department cannot be resolved.
        """
        dataframe = self.get_compressor_dataframe()

        return self._date_filter.filter_latest(dataframe)

    def get_summary(self) -> AirCompressorSummary:
        """
        Return summary information for the Air Compressor section.

        Numerical values are calculated using ``ConsumptionCalculator``,
        following the same pattern used by
        ``DepartmentAnalysisService.get_department_summary()``. The
        meter count reflects however many meters the repository
        actually discovered for the section (ordinarily ``1``, since
        the section is modeled as a single meter).

        Returns
        -------
        AirCompressorSummary
            The section's latest reading, previous reading,
            consumption, and meter count.

        Raises
        ------
        ValueError
            If the Air Compressor department cannot be resolved.
        """
        department = self._resolve_department()
        dataframe = self.get_compressor_dataframe()

        if dataframe.empty:
            return AirCompressorSummary(
                latest_reading=None,
                previous_reading=None,
                consumption=None,
                meter_count=len(department.meters),
            )

        date_label = self._repository.get_date_column().column_index

        latest, previous, consumption = (
            self._calculate_summary_from_dataframe(
                dataframe,
                date_column=date_label,
            )
        )

        return AirCompressorSummary(
            latest_reading=latest,
            previous_reading=previous,
            consumption=consumption,
            meter_count=len(department.meters),
        )

    def get_pressure_trend(
        self,
        mode: str = "latest",
        *,
        selected_date: Optional[date] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.Series:
        """
        Return the pressure reading's values, optionally filtered by
        date using ``DateFilter``.

        Returns an empty series if the workbook does not provide a
        data column at the configured pressure position (see
        ``AirCompressorFieldPositions``).

        Parameters
        ----------
        mode:
            The filter mode: ``"latest"``, ``"day"``, ``"month"``, or
            ``"range"``.

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
        pandas.Series
            The pressure reading's engineering values.

        Raises
        ------
        ValueError
            If the department or meter cannot be resolved.
        """
        return self._get_filtered_field_trend(
            self._field_positions.pressure,
            mode,
            selected_date=selected_date,
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
        )

    def get_flow_trend(
        self,
        mode: str = "latest",
        *,
        selected_date: Optional[date] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.Series:
        """
        Return the air flow reading's values, optionally filtered by
        date using ``DateFilter``.

        Returns an empty series if the workbook does not provide a
        data column at the configured air flow position (see
        ``AirCompressorFieldPositions``).

        Parameters
        ----------
        mode:
            The filter mode: ``"latest"``, ``"day"``, ``"month"``, or
            ``"range"``.

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
        pandas.Series
            The air flow reading's engineering values.

        Raises
        ------
        ValueError
            If the department or meter cannot be resolved.
        """
        return self._get_filtered_field_trend(
            self._field_positions.air_flow,
            mode,
            selected_date=selected_date,
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
        )

    def get_energy_consumption_trend(
        self,
        mode: str = "latest",
        *,
        selected_date: Optional[date] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.Series:
        """
        Return the air consumption reading's values, optionally
        filtered by date using ``DateFilter``.

        Returns an empty series if the workbook does not provide a
        data column at the configured air consumption position (see
        ``AirCompressorFieldPositions``).

        Parameters
        ----------
        mode:
            The filter mode: ``"latest"``, ``"day"``, ``"month"``, or
            ``"range"``.

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
        pandas.Series
            The air consumption reading's engineering values.

        Raises
        ------
        ValueError
            If the department or meter cannot be resolved.
        """
        return self._get_filtered_field_trend(
            self._field_positions.air_consumption,
            mode,
            selected_date=selected_date,
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
        )

    def get_running_hours_trend(
        self,
        mode: str = "latest",
        *,
        selected_date: Optional[date] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.Series:
        """
        Return the running hours reading's values, optionally
        filtered by date using ``DateFilter``.

        Returns an empty series if the workbook does not provide a
        data column at the configured running hours position (see
        ``AirCompressorFieldPositions``).

        Parameters
        ----------
        mode:
            The filter mode: ``"latest"``, ``"day"``, ``"month"``, or
            ``"range"``.

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
        pandas.Series
            The running hours reading's engineering values.

        Raises
        ------
        ValueError
            If the department or meter cannot be resolved.
        """
        return self._get_filtered_field_trend(
            self._field_positions.running_hours,
            mode,
            selected_date=selected_date,
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
        )

    def get_running_load_trend(
        self,
        mode: str = "latest",
        *,
        selected_date: Optional[date] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.Series:
        """
        Return the running load reading's values, optionally filtered
        by date using ``DateFilter``.

        Returns an empty series if the workbook does not provide a
        data column at the configured running load position (see
        ``AirCompressorFieldPositions``).

        Parameters
        ----------
        mode:
            The filter mode: ``"latest"``, ``"day"``, ``"month"``, or
            ``"range"``.

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
        pandas.Series
            The running load reading's engineering values.

        Raises
        ------
        ValueError
            If the department or meter cannot be resolved.
        """
        return self._get_filtered_field_trend(
            self._field_positions.running_load,
            mode,
            selected_date=selected_date,
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
        )
