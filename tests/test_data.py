from qfd_aviation_lab.data import make_synthetic_risk_cells
from qfd_aviation_lab.scenarios import SCENARIOS, apply_scenario


def test_synthetic_data_is_deterministic() -> None:
    a = make_synthetic_risk_cells()
    b = make_synthetic_risk_cells()
    assert a.equals(b)
    assert abs(a["baseline_risk"].sum() - 1.0) < 1e-12


def test_scenario_pressure_is_separate_from_spatial_weights() -> None:
    cells = make_synthetic_risk_cells()
    baseline = apply_scenario(cells, SCENARIOS[0])
    drought = apply_scenario(cells, SCENARIOS[1])
    assert abs(baseline["scenario_risk"].sum() - 1.0) < 1e-12
    assert abs(drought["scenario_risk"].sum() - 1.0) < 1e-12
    assert abs(baseline["scenario_pressure_index"].iloc[0] - 1.0) < 1e-12
    assert drought["scenario_pressure_index"].iloc[0] > 1.0
