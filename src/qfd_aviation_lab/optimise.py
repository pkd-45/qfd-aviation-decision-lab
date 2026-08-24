from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .domain import BASE_TYPE_BY_CODE, BASE_TYPES, MISSION_WEIGHTS, BaseType
from .geo import haversine_matrix


@dataclass(frozen=True)
class OptimisationResult:
    selected: pd.DataFrame
    assignments: pd.DataFrame
    objective: float
    total_cost: float
    success: bool
    message: str


def _option_table(sites: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for site_idx, site in sites.reset_index(drop=True).iterrows():
        for base in BASE_TYPES:
            rows.append(
                {
                    "option_id": len(rows),
                    "site_idx": site_idx,
                    "site": site["site"],
                    "lat": site["lat"],
                    "lon": site["lon"],
                    "type_code": base.code,
                    "type_label": base.label,
                    "cost_units": base.cost_units,
                    "supports_suppression": base.supports_suppression,
                    "supports_isr": base.supports_isr,
                }
            )
    return pd.DataFrame(rows)


def _mission_parameters(base: BaseType, mission: str) -> tuple[float, float, float] | None:
    if mission == "suppression" and base.supports_suppression:
        assert base.suppression_speed_kmh is not None
        assert base.suppression_readiness_min is not None
        assert base.suppression_range_km is not None
        return (
            base.suppression_speed_kmh,
            base.suppression_readiness_min,
            base.suppression_range_km,
        )
    if mission == "isr" and base.supports_isr:
        assert base.isr_speed_kmh is not None
        assert base.isr_readiness_min is not None
        assert base.isr_range_km is not None
        return base.isr_speed_kmh, base.isr_readiness_min, base.isr_range_km
    return None


def _response_matrix(
    cells: pd.DataFrame,
    options: pd.DataFrame,
    mission: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    distances = haversine_matrix(
        cells["lat"].to_numpy(),
        cells["lon"].to_numpy(),
        options["lat"].to_numpy(),
        options["lon"].to_numpy(),
    )
    response = np.full_like(distances, 1e6, dtype=float)
    feasible = np.zeros_like(distances, dtype=bool)

    for option_idx, option in options.iterrows():
        base = BASE_TYPE_BY_CODE[str(option["type_code"])]
        parameters = _mission_parameters(base, mission)
        if parameters is None:
            continue
        speed_kmh, readiness_min, max_range_km = parameters
        water_delay = 0.0
        if mission == "suppression":
            water_delay = 18.0 * base.water_sensitivity * cells["water_scarcity"].to_numpy()
        response[:, option_idx] = (
            readiness_min + 60.0 * distances[:, option_idx] / speed_kmh + water_delay
        )
        feasible[:, option_idx] = distances[:, option_idx] <= max_range_km
    return response, feasible, distances


def optimise_network(
    cells: pd.DataFrame,
    sites: pd.DataFrame,
    budget_units: float = 24.0,
    max_open_sites: int = 6,
    fixed_cost_weight: float = 0.05,
) -> OptimisationResult:
    """Solve a multi-mission risk-weighted facility-location MILP.

    Each synthetic risk cell receives both suppression and ISR coverage. A selected
    facility may support one or both missions. At most one facility class may be opened
    at a candidate location, subject to the fiscal and site-count constraints.
    """
    options = _option_table(sites)
    missions = tuple(MISSION_WEIGHTS)
    mission_data = {mission: _response_matrix(cells, options, mission) for mission in missions}

    n_cells = len(cells)
    n_options = len(options)
    n_y = n_options
    block_size = n_cells * n_options
    n_x = len(missions) * block_size
    n_vars = n_y + n_x

    risk = cells["scenario_risk"].to_numpy(dtype=float)
    c = np.zeros(n_vars, dtype=float)
    c[:n_y] = fixed_cost_weight * options["cost_units"].to_numpy(dtype=float)

    lower = np.zeros(n_vars, dtype=float)
    upper = np.ones(n_vars, dtype=float)

    mission_offset: dict[str, int] = {}
    for mission_idx, mission in enumerate(missions):
        offset = n_y + mission_idx * block_size
        mission_offset[mission] = offset
        response, feasible, _ = mission_data[mission]
        c[offset : offset + block_size] = (
            MISSION_WEIGHTS[mission] * risk[:, None] * response
        ).ravel()
        upper[offset : offset + block_size] = feasible.astype(float).ravel()

    rows: list[dict[int, float]] = []
    lb: list[float] = []
    ub: list[float] = []

    # Each cell receives one assignment for each mission.
    for mission in missions:
        offset = mission_offset[mission]
        for i in range(n_cells):
            coeff = {offset + i * n_options + o: 1.0 for o in range(n_options)}
            rows.append(coeff)
            lb.append(1.0)
            ub.append(1.0)

    # Mission assignments may only use selected, feasible facility options.
    for mission in missions:
        offset = mission_offset[mission]
        _, feasible, _ = mission_data[mission]
        for i in range(n_cells):
            for o in range(n_options):
                if not feasible[i, o]:
                    continue
                rows.append({offset + i * n_options + o: 1.0, o: -1.0})
                lb.append(-np.inf)
                ub.append(0.0)

    # At most one facility class per candidate site.
    for site_idx in range(len(sites)):
        option_ids = options.loc[options["site_idx"] == site_idx, "option_id"].tolist()
        rows.append({int(o): 1.0 for o in option_ids})
        lb.append(-np.inf)
        ub.append(1.0)

    rows.append({int(o): float(options.loc[o, "cost_units"]) for o in range(n_options)})
    lb.append(-np.inf)
    ub.append(float(budget_units))

    rows.append({o: 1.0 for o in range(n_options)})
    lb.append(-np.inf)
    ub.append(float(max_open_sites))

    matrix = lil_matrix((len(rows), n_vars), dtype=float)
    for r, coeffs in enumerate(rows):
        for col, value in coeffs.items():
            matrix[r, col] = value

    result = milp(
        c=c,
        integrality=np.ones(n_vars, dtype=int),
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(matrix.tocsr(), np.asarray(lb), np.asarray(ub)),
        options={"time_limit": 30.0},
    )

    if result.x is None:
        return OptimisationResult(
            selected=pd.DataFrame(),
            assignments=pd.DataFrame(),
            objective=float("inf"),
            total_cost=float("nan"),
            success=False,
            message=str(result.message),
        )

    y = result.x[:n_y]
    selected_ids = np.flatnonzero(y > 0.5)
    selected = options.iloc[selected_ids].copy().reset_index(drop=True)
    selected["selected"] = True

    assignment_frames: list[pd.DataFrame] = []
    for mission in missions:
        offset = mission_offset[mission]
        x = result.x[offset : offset + block_size].reshape(n_cells, n_options)
        response, _, distances = mission_data[mission]
        assigned_option = x.argmax(axis=1)
        assigned = cells[
            [
                "cell_id",
                "lat",
                "lon",
                "scenario_risk",
                "scenario_pressure_index",
                "water_scarcity",
            ]
        ].copy()
        assigned["mission"] = mission
        assigned["option_id"] = assigned_option
        assigned = assigned.merge(
            options[["option_id", "site", "type_code", "type_label"]],
            on="option_id",
            how="left",
        )
        assigned["response_min"] = response[np.arange(n_cells), assigned_option]
        assigned["distance_km"] = distances[np.arange(n_cells), assigned_option]
        assignment_frames.append(assigned)

    assignments = pd.concat(assignment_frames, ignore_index=True)
    total_cost = float(selected["cost_units"].sum())
    return OptimisationResult(
        selected=selected,
        assignments=assignments,
        objective=float(result.fun),
        total_cost=total_cost,
        success=bool(result.success),
        message=str(result.message),
    )
