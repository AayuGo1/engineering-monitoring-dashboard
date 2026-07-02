"""
models/department.py

Reusable data models representing engineering departments.

This module defines immutable domain models that are independent of any
data source or presentation framework. The models are intended to be
populated by future services regardless of whether the underlying data
originates from Excel, a database, or an API.

This module intentionally contains:
- No Streamlit code
- No pandas
- No Excel logic
- No business logic
- No calculations
- No rendering
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


# =============================================================================
# SubCategory Model
# =============================================================================


@dataclass(frozen=True)
class SubCategory:
    """
    Represents a measurable engineering subcategory.

    Attributes
    ----------
    name:
        Internal unique identifier.

    display_name:
        Human-readable display name.

    value:
        Measured value.

    unit:
        Measurement unit.

    metadata:
        Optional extensible metadata.
    """

    name: str
    display_name: str
    value: float | int | None = None
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Department Model
# =============================================================================


@dataclass(frozen=True)
class Department:
    """
    Represents an engineering department.

    Attributes
    ----------
    name:
        Internal unique identifier.

    display_name:
        Human-readable department name.

    total_consumption:
        Aggregated consumption value.

    unit:
        Measurement unit.

    subcategories:
        Collection of department subcategories.

    metadata:
        Optional extensible metadata.
    """

    name: str
    display_name: str
    total_consumption: float | int | None = None
    unit: str = ""
    subcategories: Tuple[SubCategory, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Department Summary Model
# =============================================================================


@dataclass(frozen=True)
class DepartmentSummary:
    """
    Represents a high-level summary of engineering departments.

    Attributes
    ----------
    department_count:
        Number of departments represented.

    total_consumption:
        Combined consumption across all departments.

    highest_department:
        Department with the highest consumption.

    lowest_department:
        Department with the lowest consumption.
    """

    department_count: int
    total_consumption: float | int | None = None
    highest_department: Department | None = None
    lowest_department: Department | None = None
