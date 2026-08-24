from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .data import make_candidate_sites, make_synthetic_risk_cells
from .domain import BASE_TYPES, MISSION_WEIGHTS
from .geojson import save_assignment_lines_geojson, save_points_geojson
from .metrics import network_metrics
from .optimise import optimise_network
from .report import (
    save_budget_frontier,
    save_decision_brief,
    save_network_map,
    save_summary_json,
)
from .scenarios import SCENARIOS, apply_scenario

BUDGET_SWEEP = (15.0, 18.0, 21.0, 24.0, 27.0, 30.0)


def _save_facility_catalog(output_dir: Path) -> None:
    rows = []
    for base in BASE_TYPES:
        row = dict(base.__dict__)
        row["supports_suppression"] = base.supports_suppression
        row["supports_isr"] = base.supports_isr
        rows.append(row)
    pd.DataFrame(rows).to_csv(output_dir / "facility_type_catalog.csv", index=False)


def _selection_signature(selected: pd.DataFrame) -> tuple[str, ...]:
    return tuple(sorted(f"{row.site}:{row.type_code}" for row in selected.itertuples()))


def _jaccard(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    left = set(a)
    right = set(b)
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def run_demo(output_dir: Path, budget_units: float = 24.0) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    cells = make_synthetic_risk_cells()
    sites = make_candidate_sites()
    cells.to_csv(output_dir / "synthetic_risk_cells.csv", index=False)
    sites.to_csv(output_dir / "illustrative_candidate_sites.csv", index=False)
    _save_facility_catalog(output_dir)
    save_points_geojson(sites, output_dir / "candidate_sites.geojson", ["site"])

    scenario_rows: list[dict[str, object]] = []
    assignments_all: list[pd.DataFrame] = []
    selected_all: list[pd.DataFrame] = []

    for scenario in SCENARIOS:
        scenario_cells = apply_scenario(cells, scenario)
        result = optimise_network(scenario_cells, sites, budget_units=budget_units)
        if not result.success:
            raise RuntimeError(f"Optimisation failed for {scenario.name}: {result.message}")

        metrics = network_metrics(result.assignments)
        selected_records = result.selected[
            [
                "site",
                "type_code",
                "type_label",
                "cost_units",
                "lat",
                "lon",
                "supports_suppression",
                "supports_isr",
            ]
        ].to_dict(orient="records")
        signature = _selection_signature(result.selected)
        row: dict[str, object] = {
            "scenario": scenario.name,
            "scenario_pressure_index": float(scenario_cells["scenario_pressure_index"].iloc[0]),
            "total_cost": result.total_cost,
            "objective": result.objective,
            "n_selected_sites": len(result.selected),
            "n_rpas_nodes": int((result.selected["type_code"] == "RPAS").sum()),
            "n_suppression_capable_sites": int(result.selected["supports_suppression"].sum()),
            "n_isr_capable_sites": int(result.selected["supports_isr"].sum()),
            "selected_configuration": " | ".join(signature),
            "selected": selected_records,
            "signature": signature,
            **metrics,
        }
        scenario_rows.append(row)

        assignments = result.assignments.copy()
        assignments["scenario"] = scenario.name
        assignments_all.append(assignments)
        selected = result.selected.copy()
        selected["scenario"] = scenario.name
        selected_all.append(selected)

        save_points_geojson(
            scenario_cells,
            output_dir / f"risk_cells_{scenario.name}.geojson",
            [
                "cell_id",
                "region_cluster",
                "bushfire_hazard",
                "climate_exposure",
                "vulnerability",
                "water_scarcity",
                "scenario_risk_raw",
                "scenario_risk",
                "scenario_pressure_index",
            ],
        )
        save_points_geojson(
            result.selected,
            output_dir / f"selected_network_{scenario.name}.geojson",
            [
                "site",
                "type_code",
                "type_label",
                "cost_units",
                "supports_suppression",
                "supports_isr",
            ],
        )
        save_assignment_lines_geojson(
            result.assignments,
            result.selected,
            output_dir / f"assignment_lines_{scenario.name}.geojson",
        )
        save_network_map(
            scenario_cells,
            sites,
            result.selected,
            result.assignments,
            output_dir / f"network_{scenario.name}.png",
            f"Synthetic aviation planning demo — {scenario.name.replace('_', ' ')}",
        )

    baseline_signature = tuple(scenario_rows[0]["signature"])
    for row in scenario_rows:
        signature = tuple(row["signature"])
        row["configuration_changed_vs_baseline"] = signature != baseline_signature
        row["selection_jaccard_vs_baseline"] = _jaccard(signature, baseline_signature)

    baseline_cells = apply_scenario(cells, SCENARIOS[0])
    budget_rows: list[dict[str, object]] = []
    for budget in BUDGET_SWEEP:
        result = optimise_network(baseline_cells, sites, budget_units=budget)
        if not result.success:
            budget_rows.append(
                {
                    "budget_units": budget,
                    "feasible": False,
                    "n_selected_sites": 0,
                    "n_rpas_nodes": 0,
                    "total_cost": np.nan,
                    "suppression_risk_weighted_mean_response_min": np.nan,
                    "suppression_risk_coverage_within_90min": np.nan,
                    "isr_risk_weighted_mean_response_min": np.nan,
                    "isr_risk_coverage_within_60min": np.nan,
                }
            )
            continue
        metrics = network_metrics(result.assignments)
        budget_rows.append(
            {
                "budget_units": budget,
                "feasible": True,
                "n_selected_sites": len(result.selected),
                "n_rpas_nodes": int((result.selected["type_code"] == "RPAS").sum()),
                "total_cost": result.total_cost,
                **metrics,
            }
        )

    summary = pd.DataFrame(
        [
            {k: v for k, v in row.items() if k not in {"selected", "signature"}}
            for row in scenario_rows
        ]
    )
    budget_summary = pd.DataFrame(budget_rows)
    summary.to_csv(output_dir / "scenario_summary.csv", index=False)
    budget_summary.to_csv(output_dir / "budget_sensitivity.csv", index=False)
    pd.concat(assignments_all, ignore_index=True).to_csv(
        output_dir / "assignments.csv",
        index=False,
    )
    pd.concat(selected_all, ignore_index=True).to_csv(
        output_dir / "selected_networks.csv",
        index=False,
    )
    save_summary_json(output_dir / "scenario_summary.json", scenario_rows)
    save_decision_brief(
        output_dir / "decision_brief.md",
        scenario_rows,
        budget_rows,
        budget_units,
        MISSION_WEIGHTS,
    )
    save_budget_frontier(budget_summary, output_dir / "budget_frontier.png")
    return summary
