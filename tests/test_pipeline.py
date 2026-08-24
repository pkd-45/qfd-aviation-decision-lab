import json
from pathlib import Path

from qfd_aviation_lab.pipeline import run_demo


def test_demo_writes_expected_outputs(tmp_path: Path) -> None:
    summary = run_demo(tmp_path)
    assert len(summary) == 4
    assert summary["total_cost"].le(24.0 + 1e-9).all()
    baseline_pressure = summary.loc[
        summary["scenario"] == "baseline", "scenario_pressure_index"
    ].iloc[0]
    assert abs(baseline_pressure - 1.0) < 1e-12
    for name in (
        "scenario_summary.csv",
        "scenario_summary.json",
        "budget_sensitivity.csv",
        "budget_frontier.png",
        "facility_type_catalog.csv",
        "selected_networks.csv",
        "assignments.csv",
        "decision_brief.md",
        "network_baseline.png",
        "candidate_sites.geojson",
        "risk_cells_baseline.geojson",
        "selected_network_baseline.geojson",
        "assignment_lines_baseline.geojson",
    ):
        assert (tmp_path / name).exists()

    geojson = json.loads((tmp_path / "selected_network_baseline.geojson").read_text())
    assert geojson["type"] == "FeatureCollection"
    assert geojson["features"]

    budget_text = (tmp_path / "budget_sensitivity.csv").read_text()
    assert "15.0,False" in budget_text
