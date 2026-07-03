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

Section Identification
-----------------------
``EngineeringParser`` (and therefore ``EngineeringRepository``) exposes
no section/category metadata beyond a department's ``department_name``:
``EngineeringDepartment`` carries only ``department_name``,
``display_name``, and ``meters``, and ``EngineeringMeter`` carries only
``meter_name``, ``display_name``, ``column_index``, and
``data_column``. There is no grouping concept layered on top of
ordinary department discovery for this service to resolve "the Air
Compressor section" through instead.

Given that, "Air Compressor" is treated as the name of an ordinary
department, resolved exclusively through
``EngineeringRepository.get_department()`` / ``get_meter()`` — the
same name-based lookup every other service in this project already
uses. To avoid burying that name inside method logic, it is exposed as
a constructor parameter with a default, the same way
``DepartmentAnalysisService`` treats department names as data supplied
by the caller rather than something hardcoded into a method body. The
same applies to the individual meter names (Pressure, Air Flow, Air
Consumption, Running Hours, Running Load): they are configuration,
overridable at construction time, not literals scattered through the
class.

This module intentionally contains:
- No Streamlit
- No HTML
- No Plotly
- No UI logic
- No workbook loading
- No EngineeringParser interaction
- No DataFrame slicing by position
- No department or meter discovery logic of its own
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
class AirCompressorMeterNames:
    """
    Display names of the Air Compressor section's meters.

    These are the one piece of configuration this service cannot avoid
    needing: resolving "the pressure meter" requires knowing what the
    pressure meter is called, since ``EngineeringMeter`` exposes no
    role/category metadata beyond its name. Overridable at
    ``AirCompressorService`` construction time rather than hardcoded
    into method bodies.
    """

    pressure: str = "Pressure"
    air_flow: str = "Air Flow"
    air_consumption: str = "Air Consumption"
    running_hours: str = "Running Hours"
    running_load: str = "Running Load"


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
        section.
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
    section.
    """

    def __init__(
        self,
        department_name: str = DEFAULT_SECTION_DEPARTMENT_NAME,
        meter_names: AirCompressorMeterNames = AirCompressorMeterNames(),
    ) -> None:
        """
        Initialize the service and its collaborators.

        Parameters
        ----------
        department_name:
            The workbook department name representing the Air
            Compressor section. Defaults to
            ``DEFAULT_SECTION_DEPARTMENT_NAME``.

        meter_names:
            The display names of the section's meters. Defaults to
            ``AirCompressorMeterNames()``.
        """
        self._repository = EngineeringRepository()
        self._calculator = ConsumptionCalculator()
        self._date_filter = DateFilter()

        self._department_name = department_name
        self._meter_names = meter_names

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

    def _resolve_meter(self, meter_name: str) -> EngineeringMeter:
        """
        Resolve a meter within the Air Compressor department by name.

        Parameters
        ----------
        meter_name:
            The meter's expected display name.

        Returns
        -------
        EngineeringMeter
            The matching meter.

        Raises
        ------
        ValueError
            If the Air Compressor department cannot be resolved, or if
            no meter with the given name exists within it. The error
            lists the meters that do exist, so a naming mismatch is
            immediately diagnosable.
        """
        self._resolve_department()

        meter = self._repository.get_meter(
            self._department_name,
            meter_name,
        )

        if meter is not None:
            return meter

        available = ", ".join(
            self._repository.get_meter_names(self._department_name)
        ) or "(none discovered)"

        raise ValueError(
            f"Unable to resolve meter '{meter_name}' in the "
            f"'{self._department_name}' department. Meters found "
            f"instead: {available}."
        )

    def _calculate_summary_from_dataframe(
        self,
        dataframe: pd.DataFrame,
        date_column: str,
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
            The Date column's identifier, excluded from iteration.

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

    def _get_filtered_meter_trend(
        self,
        meter_name: str,
        mode: str,
        *,
        selected_date: Optional[date] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.Series:
        """
        Return a meter's readings, optionally filtered using ``DateFilter``.

        Single reusable helper backing every trend method
        (``get_pressure_trend``, ``get_flow_trend``,
        ``get_energy_consumption_trend``, ``get_running_hours_trend``,
        ``get_running_load_trend``), so the filtering-orchestration
        logic exists in exactly one place. Mirrors
        ``DepartmentAnalysisService.get_filtered_department_data``: the
        Date column is always resolved through
        ``EngineeringRepository.get_date_column()``, never assumed or
        duplicated here, and the meter column is always resolved
        through ``EngineeringRepository.get_meter()``, never sliced by
        position.

        Parameters
        ----------
        meter_name:
            The target meter's display name.

        mode:
            The filter mode: ``"latest"``, ``"day"``, ``"month"``, or
            ``"range"``. Any other value returns the meter's
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
            The meter's (optionally filtered) readings.

        Raises
        ------
        ValueError
            If the department or meter cannot be resolved, or if the
            repository cannot identify a Date column.
        """
        meter = self._resolve_meter(meter_name)

        department_frame = self._repository.get_department_dataframe(
            self._department_name
        )

        if department_frame.empty:
            return pd.Series(dtype=float)

        date_column = self._repository.get_date_column()
        date_label = date_column.data_column
        meter_label = meter.column_index

        subset = department_frame[[meter_label, date_label]].copy()

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

        return filtered[meter_label].reset_index(drop=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_available_meters(self) -> List[str]:
        """
        Return the display names of meters belonging to the Air
        Compressor section.

        Returns
        -------
        List[str]
            Display names of the Air Compressor section's meters, in
            workbook order.

        Raises
        ------
        ValueError
            If the Air Compressor department cannot be resolved.
        """
        self._resolve_department()

        return list(
            self._repository.get_meter_names(self._department_name)
        )

    def get_compressor_dataframe(self) -> pd.DataFrame:
        """
        Return engineering data for the Air Compressor section.

        Returns
        -------
        pandas.DataFrame
            The Air Compressor section's meter columns plus the
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
        ``DepartmentAnalysisService.get_department_summary()``. Meter
        counts are sourced from department metadata returned by the
        repository.

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

        date_label = self._repository.get_date_column().data_column

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
        Return the pressure meter's readings, optionally filtered by
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
            The pressure meter's engineering readings.

        Raises
        ------
        ValueError
            If the pressure meter cannot be resolved.
        """
        return self._get_filtered_meter_trend(
            self._meter_names.pressure,
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
        Return the air flow meter's readings, optionally filtered by
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
            The air flow meter's engineering readings.

        Raises
        ------
        ValueError
            If the air flow meter cannot be resolved.
        """
        return self._get_filtered_meter_trend(
            self._meter_names.air_flow,
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
        Return the air consumption meter's readings, optionally
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
            The air consumption meter's engineering readings.

        Raises
        ------
        ValueError
            If the air consumption meter cannot be resolved.
        """
        return self._get_filtered_meter_trend(
            self._meter_names.air_consumption,
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
        Return the running hours meter's readings, optionally filtered
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
            The running hours meter's engineering readings.

        Raises
        ------
        ValueError
            If the running hours meter cannot be resolved.
        """
        return self._get_filtered_meter_trend(
            self._meter_names.running_hours,
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
        Return the running load meter's readings, optionally filtered
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
            The running load meter's engineering readings.

        Raises
        ------
        ValueError
            If the running load meter cannot be resolved.
        """
        return self._get_filtered_meter_trend(
            self._meter_names.running_load,
            mode,
            selected_date=selected_date,
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
        )
