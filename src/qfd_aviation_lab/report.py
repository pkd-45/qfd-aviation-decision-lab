from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd


def save_network_map(
    cells: pd.DataFrame,
    sites: pd.DataFrame,
    selected: pd.DataFrame,
    assignments: pd.DataFrame,
    output_path: Path,
    title: str,
) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 8.5))
    sizes = 45 + 460 * cells["scenario_risk"] / cells["scenario_risk"].max()
    scatter = ax.scatter(
        cells["lon"],
        cells["lat"],
        c=cells["scenario_risk"],
        s=sizes,
        alpha=0.72,
    )
    ax.scatter(
        sites["lon"],
        sites["lat"],
        marker="x",
        s=45,
        label="Candidate site",
    )
    if not selected.empty:
        selected_lookup = selected.set_index(["site", "type_code"])
        suppression = assignments.loc[assignments["mission"] == "suppression"]
        for _, row in suppression.iterrows():
            base = selected_lookup.loc[(row["site"], row["type_code"])]
            ax.plot(
                [row["lon"], base["lon"]],
                [row["lat"], base["lat"]],
                linewidth=0.35,
                alpha=0.13,
            )
        ax.scatter(
            selected["lon"],
            selected["lat"],
            marker="*",
            s=220,
            label="Selected facility",
        )
        label_offsets = {
            "Brisbane": (-82, -18),
            "Toowoomba": (-86, 10),
            "Rockhampton": (8, 8),
            "Townsville": (8, 8),
            "Charleville": (8, 8),
        }
        for _, row in selected.iterrows():
            offset = label_offsets.get(str(row["site"]), (5, 5))
            ax.annotate(
                f"{row['site']} ({row['type_code']})",
                (row["lon"], row["lat"]),
                xytext=offset,
                textcoords="offset points",
                fontsize=8,
            )
    pressure = float(cells["scenario_pressure_index"].iloc[0])
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"{title}\naggregate pressure index = {pressure:.2f}")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.colorbar(scatter, ax=ax, label="Normalised synthetic spatial risk weight")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_budget_frontier(summary: pd.DataFrame, output_path: Path) -> None:
    feasible = summary.loc[summary["feasible"]].copy()
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ax.plot(
        feasible["budget_units"],
        100.0 * feasible["suppression_risk_coverage_within_90min"],
        marker="o",
        label="Suppression: coverage within 90 min",
    )
    ax.plot(
        feasible["budget_units"],
        100.0 * feasible["isr_risk_coverage_within_60min"],
        marker="s",
        label="ISR: coverage within 60 min",
    )
    if (~summary["feasible"]).any():
        infeasible = summary.loc[~summary["feasible"], "budget_units"]
        for budget in infeasible:
            budget_value = float(budget)
            ax.axvline(budget_value, linestyle=":", alpha=0.25)
            ax.text(
                budget_value + 0.12,
                0.98,
                "infeasible",
                rotation=90,
                va="top",
                transform=ax.get_xaxis_transform(),
                fontsize=8,
            )
    ax.set_xlabel("Synthetic budget units")
    ax.set_ylabel("Risk-weighted coverage (%)")
    ax.set_title("Illustrative fiscal trade-off frontier")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _format_configuration(selected: list[dict[str, Any]]) -> list[str]:
    return [
        f"- **{item['site']}** — {item['type_label']} ({item['type_code']}); "
        f"cost {item['cost_units']:.1f}"
        for item in selected
    ]


def save_decision_brief(
    output_path: Path,
    scenario_rows: list[dict[str, object]],
    budget_rows: list[dict[str, object]],
    budget_units: float,
    mission_weights: dict[str, float],
) -> None:
    baseline = next(row for row in scenario_rows if row["scenario"] == "baseline")
    selected = baseline["selected"]
    stable = all(not bool(row["configuration_changed_vs_baseline"]) for row in scenario_rows)
    lines = [
        "# Aviation network decision-support demo",
        "",
        "## Purpose",
        "",
        (
            "This is a synthetic, portfolio-scale demonstration of a risk-based framework "
            "for comparing aviation hub and airbase configurations. It demonstrates "
            "methodology, not operational recommendations to QFD."
        ),
        "",
        "## Decision model",
        "",
        (
            "The optimiser jointly considers two illustrative service missions: crewed "
            "suppression response and intelligence/surveillance (ISR), including RPAS nodes."
        ),
        (
            f"Synthetic mission-priority weights are suppression "
            f"{100 * mission_weights['suppression']:.0f}% and ISR "
            f"{100 * mission_weights['isr']:.0f}%. These are demonstration assumptions, "
            "not QFD policy weights."
        ),
        (
            "Scenario risk is separated into (1) an aggregate pressure index and (2) "
            "normalised spatial risk weights. This avoids conflating changing statewide "
            "pressure with changing geographic allocation of risk."
        ),
        "",
        "## Baseline illustrative configuration",
        "",
        f"Budget constraint: **{budget_units:.1f} synthetic cost units**.",
        "",
        *_format_configuration(selected),
        "",
        "## Baseline service metrics",
        "",
        (
            "- Suppression risk-weighted mean response: "
            f"**{baseline['suppression_risk_weighted_mean_response_min']:.1f} min**"
        ),
        (
            "- Suppression risk-weighted 60-minute coverage: "
            f"**{100 * baseline['suppression_risk_coverage_within_60min']:.1f}%**"
        ),
        (
            "- ISR risk-weighted mean response: "
            f"**{baseline['isr_risk_weighted_mean_response_min']:.1f} min**"
        ),
        (
            "- ISR risk-weighted 60-minute coverage: "
            f"**{100 * baseline['isr_risk_coverage_within_60min']:.1f}%**"
        ),
        "",
        "## Scenario stress test",
        "",
        (
            "| Scenario | Pressure index | Suppression mean (min) | "
            "Suppression 60-min coverage | ISR mean (min) | Configuration changed? |"
        ),
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in scenario_rows:
        changed = "yes" if row["configuration_changed_vs_baseline"] else "no"
        lines.append(
            f"| {row['scenario']} | {row['scenario_pressure_index']:.2f} | "
            f"{row['suppression_risk_weighted_mean_response_min']:.1f} | "
            f"{100 * row['suppression_risk_coverage_within_60min']:.1f}% | "
            f"{row['isr_risk_weighted_mean_response_min']:.1f} | {changed} |"
        )
    lines += [
        "",
        "### Configuration stability",
        "",
    ]
    if stable:
        lines.append(
            "The reference-budget site/type configuration remains unchanged across all four "
            "illustrative scenarios. In this synthetic example, the stress tests therefore "
            "degrade service metrics without causing a network substitution."
        )
    else:
        lines.append(
            "At least one stress scenario changes the selected site/type configuration, "
            "demonstrating scenario-sensitive network adaptation."
        )
    lines += [
        "",
        "## Fiscal sensitivity",
        "",
        ("| Budget | Feasible | Sites | RPAS nodes | Suppression mean (min) | ISR mean (min) |"),
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in budget_rows:
        if not row["feasible"]:
            lines.append(f"| {row['budget_units']:.1f} | no | — | — | — | — |")
            continue
        lines.append(
            f"| {row['budget_units']:.1f} | yes | {int(row['n_selected_sites'])} | "
            f"{int(row['n_rpas_nodes'])} | "
            f"{row['suppression_risk_weighted_mean_response_min']:.1f} | "
            f"{row['isr_risk_weighted_mean_response_min']:.1f} |"
        )
    lines += [
        "",
        (
            "An infeasible low-budget point means the model cannot satisfy both mission "
            "coverage requirements with the available synthetic facility options and budget; "
            "it is not treated as a numerical failure."
        ),
        "",
        "## GIS-ready outputs",
        "",
        (
            "The demo writes GeoJSON layers for candidate sites, scenario risk cells, "
            "selected networks and mission assignment lines. These can be opened directly "
            "in GIS software such as QGIS for inspection or further styling."
        ),
        "",
        "## What this prototype demonstrates",
        "",
        (
            "- A transparent spatial risk layer combining hazard, climate exposure, "
            "vulnerability and water scarcity."
        ),
        (
            "- A standardised data model for strategic hubs, regional airbases, mobile "
            "staging bases and RPAS/ISR nodes."
        ),
        "- Multi-mission mixed-integer optimisation under a fiscal constraint.",
        "- Separate suppression and ISR response/coverage metrics for decision-makers.",
        "- Scenario pressure, spatial reweighting and network-stability diagnostics.",
        "- A budget-versus-service frontier, including explicit infeasibility.",
        "- GIS-ready GeoJSON products alongside CSV, JSON and maps.",
        "",
        "## What is not claimed",
        "",
        "- No QFD operational, incident, aviation, water or infrastructure data are used.",
        (
            "- Candidate locations are illustrative regional centres, not asserted QFD "
            "facilities or recommendations."
        ),
        (
            "- The four-level facility typology is a prototype software schema, not a "
            "claimed national standard."
        ),
        "- Synthetic cost, range, readiness, speed and mission-weight parameters are placeholders.",
        (
            "- Aircraft availability, duty limits, simultaneous incidents, refuelling "
            "logistics, terrain and detailed weather routing remain outside this prototype."
        ),
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _json_default(value: object) -> object:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serialisable")


def save_summary_json(output_path: Path, rows: list[dict[str, object]]) -> None:
    output_path.write_text(
        json.dumps(rows, indent=2, default=_json_default),
        encoding="utf-8",
    )
