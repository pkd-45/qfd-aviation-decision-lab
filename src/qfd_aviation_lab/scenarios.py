from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Scenario:
    name: str
    hazard_mult: float = 1.0
    climate_mult: float = 1.0
    vulnerability_mult: float = 1.0
    scarcity_mult: float = 1.0


SCENARIOS: tuple[Scenario, ...] = (
    Scenario("baseline"),
    Scenario(
        "severe_drought",
        hazard_mult=1.18,
        climate_mult=1.08,
        scarcity_mult=1.55,
    ),
    Scenario(
        "extreme_fire_weather",
        hazard_mult=1.48,
        climate_mult=1.35,
        scarcity_mult=1.18,
    ),
    Scenario(
        "future_stress_test",
        hazard_mult=1.28,
        climate_mult=1.30,
        scarcity_mult=1.25,
    ),
)


def _raw_risk(
    hazard: pd.Series,
    climate: pd.Series,
    vulnerability: pd.Series,
    scarcity: pd.Series,
) -> pd.Series:
    return 0.42 * hazard + 0.20 * climate + 0.28 * vulnerability + 0.10 * scarcity


def apply_scenario(cells: pd.DataFrame, scenario: Scenario) -> pd.DataFrame:
    """Return scenario-adjusted cells with separated pressure and spatial weights.

    ``scenario_pressure_index`` captures the aggregate change in synthetic risk pressure
    relative to the unmodified inputs. ``scenario_risk`` is normalised to sum to one and
    therefore represents the spatial allocation of that pressure for optimisation.
    """
    result = cells.copy()
    baseline_raw = _raw_risk(
        result["bushfire_hazard"],
        result["climate_exposure"],
        result["vulnerability"],
        result["water_scarcity"],
    )

    hazard = (result["bushfire_hazard"] * scenario.hazard_mult).clip(upper=1.5)
    climate = (result["climate_exposure"] * scenario.climate_mult).clip(upper=1.5)
    vulnerability = (result["vulnerability"] * scenario.vulnerability_mult).clip(upper=1.5)
    scarcity = (result["water_scarcity"] * scenario.scarcity_mult).clip(upper=1.5)

    raw = _raw_risk(hazard, climate, vulnerability, scarcity)
    pressure_index = float(raw.sum() / baseline_raw.sum())

    result["scenario_risk_raw"] = raw
    result["scenario_risk"] = raw / raw.sum()
    result["scenario_pressure_index"] = pressure_index
    # Scarcity is also an operational input: drought can increase turnaround friction.
    result["water_scarcity"] = scarcity
    return result
