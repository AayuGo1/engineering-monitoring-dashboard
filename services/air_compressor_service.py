"""
services/air_compressor_service.py

Backend service for Air Compressor engineering data.

This module provides a thin orchestration layer between the UI and
the lower-level engineering services. Like the other engineering
services in this project, it owns no data access of its own:
``EngineeringRepository`` is the single source of truth for workbook
data, department discovery, meter discovery, and column metadata.
This service only coordinates repository lookups with ``DateFilter``
for date-based filtering and ``ConsumptionCalculator`` for numerical
summaries.

Current Limitations
--------------------
``EngineeringRepository`` does not yet expose *section* discovery —
i.e. a way to identify which departments and meters make up the
"Air Compressor" engineering section (as distinct from ordinary
department discovery, which returns whatever departments happen to
exist in the workbook without any notion of grouping them into
sections). Because that capability does not exist yet, this service
must not hardcode department names, meter names, or Excel column
identifiers (e.g. "Air Compressor", "Air Flow", "Pressure", "Running
Hours", "Energy") to work around the gap. Doing so would silently
reintroduce the exact kind of workbook-structure guessing that the
repository layer exists to eliminate.

Until ``EngineeringRepository`` is extended with section discovery,
every method in this service that would need to resolve "the Air
Compressor meters" raises a descriptive ``ValueError`` explaining
the missing capability, rather than guessing or hardcoding a mapping.

This module intentionally contains:
- No Streamlit
- No HTML
- No Plotly
- No UI logic
- No workbook loading
- No EngineeringParser interaction
- No DataFrame slicing by column index
- No department, meter, or section discovery logic
- No hardcoded department, meter, or column names
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, NoReturn, Optional

import pandas as pd

from services.consumption_calculator import ConsumptionCalculator
from services.date_filter import DateFilter
from services.engineering_repository import EngineeringRepository


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

    latest_reading: Optional[float]
    previous_reading: Optional[float]
    consumption: Optional[float]
    meter_count: int


class AirCompressorService:
    """
    Backend service powering Air Compressor engineering views.

    This service is a thin orchestration layer. All data access is
    delegated to ``EngineeringRepository``; this class only combines
    repository results with ``DateFilter`` and
    ``ConsumptionCalculator`` to answer UI-facing questions about the
    Air Compressor engineering section.

    Notes
    -----
    ``EngineeringRepository`` does not yet expose Air Compressor
    section discovery. Every method below that would require
    resolving "the Air Compressor meters" therefore raises
    ``ValueError`` via ``_require_section_support`` instead of
    hardcoding a department or meter mapping.
    """

    def __init__(
        self,
        repository: Optional[EngineeringRepository] = None,
        calculator: Optional[ConsumptionCalculator] = None,
        date_filter: Optional[DateFilter] = None,
    ) -> None:
        """
        Initialize the service and its collaborators.

        Parameters
        ----------
        repository:
            The ``EngineeringRepository`` instance to delegate all
            workbook access to. Defaults to a new instance.
        calculator:
            The ``ConsumptionCalculator`` instance used to derive
            consumption figures from readings. Defaults to a new
            instance.
        date_filter:
            The ``DateFilter`` instance used to filter engineering
            records by date. Defaults to a new instance.
        """
        self._repository = repository or EngineeringRepository()
        self._calculator = calculator or ConsumptionCalculator()
        self._date_filter = date_filter or DateFilter()

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require_section_support(operation: str) -> NoReturn:
        """
        Raise a descriptive error for operations that require Air
        Compressor section discovery.

        Parameters
        ----------
        operation:
            A short, human-readable description of the operation that
            could not be performed (e.g. ``"resolve the Air Compressor
            meters"``).

        Raises
        ------
        ValueError
            Always. Explains that ``EngineeringRepository`` does not
            yet expose the section-discovery capability needed to
            perform ``operation``, and that this service intentionally
            does not hardcode a workaround.
        """
        raise ValueError(
            f"Unable to {operation}: EngineeringRepository does not "
            "yet expose Air Compressor section discovery (metadata "
            "identifying which departments and meters belong to the "
            "Air Compressor engineering section). AirCompressorService "
            "intentionally does not hardcode department, meter, or "
            "column names to work around this gap. Extend "
            "EngineeringRepository with section discovery before this "
            "operation can be supported."
        )

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
            Display names of the Air Compressor section's meters.

        Raises
        ------
        ValueError
            Always, until ``EngineeringRepository`` exposes Air
            Compressor section discovery.
        """
        self._require_section_support(
            "resolve the Air Compressor meters"
        )

    def get_compressor_dataframe(self) -> pd.DataFrame:
        """
        Return engineering data for the Air Compressor section.

        Returns
        -------
        pandas.DataFrame
            The Air Compressor section's engineering records.

        Raises
        ------
        ValueError
            Always, until ``EngineeringRepository`` exposes Air
            Compressor section discovery.
        """
        self._require_section_support(
            "retrieve the Air Compressor engineering data"
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
            Always, until ``EngineeringRepository`` exposes Air
            Compressor section discovery.
        """
        self._require_section_support(
            "retrieve the latest Air Compressor readings"
        )

    def get_summary(self) -> AirCompressorSummary:
        """
        Return summary information for the Air Compressor section.

        Numerical values would be calculated using
        ``ConsumptionCalculator``, following the same pattern used by
        ``DepartmentAnalysisService.get_department_summary()``.

        Returns
        -------
        AirCompressorSummary
            The section's latest reading, previous reading,
            consumption, and meter count.

        Raises
        ------
        ValueError
            Always, until ``EngineeringRepository`` exposes Air
            Compressor section discovery.
        """
        self._require_section_support(
            "calculate the Air Compressor summary"
        )

    def get_pressure_trend(
        self,
        mode: str = "latest",
        *,
        selected_date: Optional[Any] = None,
        month: Optional[Any] = None,
        year: Optional[Any] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
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
            Always, until ``EngineeringRepository`` exposes Air
            Compressor section discovery capable of identifying the
            pressure meter without hardcoding its name.
        """
        self._require_section_support(
            "resolve the Air Compressor pressure meter"
        )

    def get_flow_trend(
        self,
        mode: str = "latest",
        *,
        selected_date: Optional[Any] = None,
        month: Optional[Any] = None,
        year: Optional[Any] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
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
            Always, until ``EngineeringRepository`` exposes Air
            Compressor section discovery capable of identifying the
            air flow meter without hardcoding its name.
        """
        self._require_section_support(
            "resolve the Air Compressor air flow meter"
        )

    def get_energy_consumption_trend(
        self,
        mode: str = "latest",
        *,
        selected_date: Optional[Any] = None,
        month: Optional[Any] = None,
        year: Optional[Any] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
    ) -> pd.Series:
        """
        Return the energy meter's consumption trend, optionally
        filtered by date using ``DateFilter`` and calculated using
        ``ConsumptionCalculator``.

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
            The energy meter's engineering readings.

        Raises
        ------
        ValueError
            Always, until ``EngineeringRepository`` exposes Air
            Compressor section discovery capable of identifying the
            energy meter without hardcoding its name.
        """
        self._require_section_support(
            "resolve the Air Compressor energy meter"
        )
