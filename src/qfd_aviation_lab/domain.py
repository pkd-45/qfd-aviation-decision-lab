from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaseType:
    """Illustrative facility/capability class used by the synthetic prototype."""

    code: str
    label: str
    cost_units: float
    water_sensitivity: float
    suppression_speed_kmh: float | None
    suppression_readiness_min: float | None
    suppression_range_km: float | None
    isr_speed_kmh: float | None
    isr_readiness_min: float | None
    isr_range_km: float | None

    @property
    def supports_suppression(self) -> bool:
        return self.suppression_speed_kmh is not None

    @property
    def supports_isr(self) -> bool:
        return self.isr_speed_kmh is not None


# All performance and cost values below are synthetic planning parameters. They are
# deliberately not presented as QFD aircraft specifications, budgets or service standards.
BASE_TYPES: tuple[BaseType, ...] = (
    BaseType(
        code="HUB",
        label="Strategic aviation hub",
        cost_units=9.0,
        water_sensitivity=0.25,
        suppression_speed_kmh=255.0,
        suppression_readiness_min=8.0,
        suppression_range_km=650.0,
        isr_speed_kmh=220.0,
        isr_readiness_min=7.0,
        isr_range_km=520.0,
    ),
    BaseType(
        code="REG",
        label="Regional airbase",
        cost_units=4.5,
        water_sensitivity=0.45,
        suppression_speed_kmh=235.0,
        suppression_readiness_min=12.0,
        suppression_range_km=480.0,
        isr_speed_kmh=160.0,
        isr_readiness_min=18.0,
        isr_range_km=390.0,
    ),
    BaseType(
        code="MOB",
        label="Mobile staging base",
        cost_units=3.0,
        water_sensitivity=0.75,
        suppression_speed_kmh=215.0,
        suppression_readiness_min=22.0,
        suppression_range_km=330.0,
        isr_speed_kmh=None,
        isr_readiness_min=None,
        isr_range_km=None,
    ),
    BaseType(
        code="RPAS",
        label="RPAS / local ISR node",
        cost_units=1.5,
        water_sensitivity=0.0,
        suppression_speed_kmh=None,
        suppression_readiness_min=None,
        suppression_range_km=None,
        isr_speed_kmh=120.0,
        isr_readiness_min=3.0,
        isr_range_km=180.0,
    ),
)


BASE_TYPE_BY_CODE = {base.code: base for base in BASE_TYPES}
MISSION_WEIGHTS = {"suppression": 0.60, "isr": 0.40}
