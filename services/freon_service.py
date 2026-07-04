"""
services/freon_service.py

Backend service for Freon Refrigeration engineering data.

This module provides a thin orchestration layer between the UI and
the lower-level engineering services, following exactly the same
architecture used by ``AirCompressorService``. It owns no data access
of its own: ``EngineeringRepository`` is the single source of truth
for workbook data, department discovery, meter discovery, and column
metadata. This service only coordinates repository lookups with
``DateFilter`` for date-based filtering and ``ConsumptionCalculator``
for numerical summaries.

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
Earlier versions of this service assumed the Freon Refrigeration
section was modeled as one meter *per logical reading* (Temperature,
Pressure, Freon Level, Running Hours), each resolved via
``EngineeringRepository.get_meter()`` by that hardcoded name.

Mirroring ``AirCompressorService``, this service instead treats the
section as a single meter whose individual readings live in separate
*columns* within that meter's data, not separate named meters. Since
``EngineeringMeter`` carries only ``meter_name``, ``display_name``,
``column_index``, and ``data_column`` — no per-column role metadata —
there is no name to search for beyond the meter itself.

This service therefore:

1. Resolves the section's meter dynamically — it looks up whichever
   meter(s) the "Freon Refrigeration" department actually contains via
   ``EngineeringRepository.get_meter_names()`` / ``get_meter()``,
   rather than assuming a specific meter name.
2. Discovers the section's data columns dynamically from the
   department's DataFrame (every column except the Date column, in
   workbook order), rather than assuming fixed column identities.
3. Addresses the four logical readings by *position* within that
   discovered column list (``FreonFieldPositions``), since position in
   workbook order is the only distinguishing signal available.
   Positions are configuration, overridable at construction time —
   the same philosophy the previous hardcoded meter names followed,
   just applied to the structure the workbook actually has.

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


DEFAULT_SECTION_DEPARTMENT_NAME = "Freon Refrigeration"


@dataclass(frozen=True)
class FreonFieldPositions:
    """
    Positional indices, within the Freon Refrigeration section's
    dynamically discovered data columns (Date column excluded, in
    workbook order), of each logical reading.

    The workbook models the Freon Refrigeration section as a single
    meter whose temperature, pressure, Freon level, and running hours
    readings live in separate columns rather than as separate named
    meters. Since ``EngineeringMeter`` exposes no per-column role
    metadata, "the temperature column" etc. can only be identified by
    its position among the section's data columns. These positions
    are configuration, overridable at ``FreonService`` construction
    time, rather than hardcoded meter-name literals scattered through
    the class.
    """

    temperature: int = 0
    pressure: int = 1
    freon_level: int = 2
    running_hours: int = 3


@dataclass(frozen=True)
class FreonSummary:
    """
    Summary information for the Freon Refrigeration engineering
    section.

    Attributes
    ----------
    latest_reading:
        Latest valid engineering reading.

    previous_reading:
        Previous valid engineering reading.

    consumption:
        Difference between latest and previous readings.

    meter_count:
        Number of engineering meters belonging to the Freon
        Refrigeration section, as discovered from the workbook. With
        the section modeled as a single meter, this is ordinarily
        ``1``.
    """

    latest_reading: float | None
    previous_reading: float | None
    consumption: float | None
    meter_count: int


class FreonService:
    """
    Backend service powering Freon Refrigeration engineering views.

    This service is a thin orchestration layer. All data access is
    delegated to ``EngineeringRepository``; this class only combines
    repository results with ``DateFilter`` and ``ConsumptionCalculator``
    to answer UI-facing questions about the Freon Refrigeration
    engineering section. The section's meter and data columns are
    discovered dynamically from the workbook rather than assumed from
    hardcoded meter names.
    """

    def __init__(
        self,
        department_name: str = DEFAULT_SECTION_DEPARTMENT_NAME,
        field_positions: FreonFieldPositions = FreonFieldPositions(),
    ) -> None:
        """
        Initialize the service and its collaborators.

        Parameters
        ----------
        department_name:
            The workbook department name representing the Freon
            Refrigeration section. Defaults to
            ``DEFAULT_SECTION_DEPARTMENT_NAME``.

        field_positions:
            The positions, among the section's dynamically discovered
            data columns, of each logical reading. Defaults to
            ``FreonFieldPositions()``.
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
        Resolve the Freon Refrigeration department via repository
        metadata.

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
        Resolve the Freon Refrigeration section's meter dynamically.

        Rather than searching for a specific hardcoded meter name,
        this takes whichever meter(s) the repository actually
        discovered within the Freon Refrigeration department and
        resolves the first one, since the section is modeled as a
        single meter. This keeps the service correct regardless of
        what that meter happens to be named in the workbook.

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
        Return the Freon Refrigeration section's data columns,
        discovered dynamically from the department's DataFrame.

        Every column of the department DataFrame except the Date
        column is treated as a data column (temperature, pressure,
        Freon level, running hours, or any other reading the workbook
        happens to contain), in workbook order. This replaces
        hardcoded per-reading meter-name lookups with structure read
        directly from the data.

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

    def _resolve_field_column(self, position: int) -> int:
        """
        Resolve the DataFrame column label for a field at a given
        position among the section's dynamically discovered data
        columns.

        Parameters
        ----------
        position:
            The zero-based position, within the section's discovered
            data columns, of the desired reading.

        Returns
        -------
        int
            The corresponding DataFrame column label.

        Raises
        ------
        ValueError
            If the department/meter cannot be resolved, or if
            ``position`` falls outside the discovered data columns.
        """
        columns = self._get_field_columns()

        if position < 0 or position >= len(columns):
            raise ValueError(
                f"Field position {position} is out of range for the "
                f"'{self._department_name}' section, which has "
                f"{len(columns)} discovered data column(s): {columns}."
            )

        return columns[position]

    def _resolve_field_position_by_label(self, field_label: str) -> int:
        """
        Resolve the position of a field among the section's
        dynamically discovered data columns, by its display label.

        This backs ``get_meter_trend()``, the generic counterpart to
        the named trend methods, for callers that already hold a
        label obtained from ``get_available_meters()``. The lookup is
        performed against the labels discovered dynamically from the
        workbook (``str(column)`` for each discovered data column),
        never against a hardcoded meter name.

        Parameters
        ----------
        field_label:
            The field's display label, as returned by
            ``get_available_meters()``.

        Returns
        -------
        int
            The zero-based position of the matching field among the
            section's discovered data columns.

        Raises
        ------
        ValueError
            If the department/meter cannot be resolved, or if no
            discovered field matches ``field_label``. The error lists
            the labels that were actually discovered, so a naming
            mismatch is immediately diagnosable.
        """
        labels = [str(column) for column in self._get_field_columns()]

        if field_label in labels:
            return labels.index(field_label)

        available = ", ".join(labels) or "(none discovered)"

        raise ValueError(
            f"Unable to resolve field '{field_label}' in the "
            f"'{self._department_name}' section. Fields found "
            f"instead: {available}."
        )

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
        ``AirCompressorService._calculate_summary_from_dataframe``:
        iterates the DataFrame's columns using ``ConsumptionCalculator``
        and returns the values from the first column that yields a
        valid latest reading, skipping the Date column so it is never
        treated as a numeric reading.

        Parameters
        ----------
        dataframe:
            The Freon Refrigeration section's engineering records.

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
        (``get_temperature_trend``, ``get_pressure_trend``,
        ``get_freon_level_trend``, ``get_running_hours_trend``, and
        the generic ``get_meter_trend``), so the filtering-orchestration
        logic exists in exactly one place. Mirrors
        ``AirCompressorService._get_filtered_field_trend``: the Date
        column is always resolved through
        ``EngineeringRepository.get_date_column()``, never assumed or
        duplicated here, and the field column is always resolved
        through ``_resolve_field_column()`` (dynamic discovery from
        the department DataFrame), never a hardcoded meter-name
        lookup. Both are indexed into the department DataFrame using
        their actual DataFrame column labels, never a stringified
        ``data_column``, so the two identifiers are never mixed.

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
            numbers.

        Raises
        ------
        ValueError
            If the department or meter cannot be resolved, if the
            repository cannot identify a Date column, or if
            ``position`` falls outside the discovered data columns.
        """
        department_frame = self._repository.get_department_dataframe(
            self._department_name
        )

        if department_frame.empty:
            return pd.Series(dtype=float)

        field_label = self._resolve_field_column(position)

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
        Return labels for the Freon Refrigeration section's
        dynamically discovered data columns.

        With the section modeled as a single meter, these are not
        separate meter names but the section's individual reading
        columns (temperature, pressure, Freon level, running hours, or
        whatever else the workbook happens to contain), labeled by
        their raw DataFrame column values and returned in workbook
        order.

        Returns
        -------
        List[str]
            String labels of the Freon Refrigeration section's data
            columns, in workbook order.

        Raises
        ------
        ValueError
            If the Freon Refrigeration department or its meter cannot
            be resolved.
        """
        columns = self._get_field_columns()
        return [str(column) for column in columns]

    def get_freon_dataframe(self) -> pd.DataFrame:
        """
        Return engineering data for the Freon Refrigeration section.

        Returns
        -------
        pandas.DataFrame
            The Freon Refrigeration section's data columns plus the
            workbook's Date column, exactly as provided by
            ``EngineeringRepository.get_department_dataframe()``.

        Raises
        ------
        ValueError
            If the Freon Refrigeration department cannot be resolved.
        """
        self._resolve_department()

        return self._repository.get_department_dataframe(
            self._department_name
        )

    def get_latest_freon_readings(self) -> pd.DataFrame:
        """
        Return the latest engineering record for the Freon
        Refrigeration section.

        Returns
        -------
        pandas.DataFrame
            A single-row DataFrame containing the latest record for
            the Freon Refrigeration section.

        Raises
        ------
        ValueError
            If the Freon Refrigeration department cannot be resolved.
        """
        dataframe = self.get_freon_dataframe()

        return self._date_filter.filter_latest(dataframe)

    def get_previous_freon_readings(self) -> pd.DataFrame:
        """
        Return the previous engineering record for the Freon
        Refrigeration section.

        Uses the full section DataFrame and drops the most recent
        record (as identified by ``DateFilter.filter_latest``) before
        re-applying ``DateFilter.filter_latest`` to the remainder,
        which mirrors how ``ConsumptionCalculator.previous_reading``
        identifies the second-most-recent valid value for a single
        series, without duplicating that logic here.

        Returns
        -------
        pandas.DataFrame
            A single-row DataFrame containing the previous record for
            the Freon Refrigeration section, or an empty DataFrame if
            fewer than two records exist.

        Raises
        ------
        ValueError
            If the Freon Refrigeration department cannot be resolved.
        """
        dataframe = self.get_freon_dataframe()

        if dataframe.empty or len(dataframe) < 2:
            return dataframe.iloc[0:0]

        latest = self._date_filter.filter_latest(dataframe)
        remainder = dataframe.drop(index=latest.index)

        if remainder.empty:
            return remainder

        return self._date_filter.filter_latest(remainder)

    def get_summary(self) -> FreonSummary:
        """
        Return summary information for the Freon Refrigeration
        section.

        Numerical values are calculated using ``ConsumptionCalculator``,
        following the same pattern used by
        ``AirCompressorService.get_summary()``. The meter count
        reflects however many meters the repository actually
        discovered for the section (ordinarily ``1``, since the
        section is modeled as a single meter).

        Returns
        -------
        FreonSummary
            The section's latest reading, previous reading,
            consumption, and meter count.

        Raises
        ------
        ValueError
            If the Freon Refrigeration department cannot be resolved.
        """
        department = self._resolve_department()
        dataframe = self.get_freon_dataframe()

        if dataframe.empty:
            return FreonSummary(
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

        return FreonSummary(
            latest_reading=latest,
            previous_reading=previous,
            consumption=consumption,
            meter_count=len(department.meters),
        )

    def get_meter_trend(
        self,
        meter_name: str,
        mode: str = "latest",
        *,
        selected_date: Optional[date] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.Series:
        """
        Return an arbitrary Freon Refrigeration field's readings,
        optionally filtered by date using ``DateFilter``.

        General-purpose counterpart to the named trend methods (e.g.
        ``get_temperature_trend``), for callers that already know a
        field's display label (for example, one obtained from
        ``get_available_meters()``) and don't need a dedicated method
        for it. The label is resolved against the section's
        dynamically discovered data columns via
        ``_resolve_field_position_by_label()``, never against a
        hardcoded meter name.

        Parameters
        ----------
        meter_name:
            The target field's display label, as returned by
            ``get_available_meters()``.

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
            The field's engineering readings, indexed by their
            corresponding Date values.

        Raises
        ------
        ValueError
            If the field cannot be resolved.
        """
        position = self._resolve_field_position_by_label(meter_name)

        return self._get_filtered_field_trend(
            position,
            mode,
            selected_date=selected_date,
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
        )

    def get_temperature_trend(
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
        Return the temperature reading's values, optionally filtered
        by date using ``DateFilter``.

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
            The temperature reading's engineering values.

        Raises
        ------
        ValueError
            If the temperature column cannot be resolved.
        """
        return self._get_filtered_field_trend(
            self._field_positions.temperature,
            mode,
            selected_date=selected_date,
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
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
            If the pressure column cannot be resolved.
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

    def get_freon_level_trend(
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
        Return the Freon level reading's values, optionally filtered
        by date using ``DateFilter``.

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
            The Freon level reading's engineering values.

        Raises
        ------
        ValueError
            If the Freon level column cannot be resolved.
        """
        return self._get_filtered_field_trend(
            self._field_positions.freon_level,
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
            If the running hours column cannot be resolved.
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
