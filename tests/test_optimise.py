from qfd_aviation_lab.data import make_candidate_sites, make_synthetic_risk_cells
from qfd_aviation_lab.domain import BASE_TYPE_BY_CODE
from qfd_aviation_lab.metrics import network_metrics
from qfd_aviation_lab.optimise import optimise_network
from qfd_aviation_lab.scenarios import SCENARIOS, apply_scenario


def _baseline_cells(n_cells: int = 30):
    return apply_scenario(make_synthetic_risk_cells(n_cells=n_cells), SCENARIOS[0])


def test_network_respects_budget_site_uniqueness_and_mission_coverage() -> None:
    cells = _baseline_cells()
    result = optimise_network(cells, make_candidate_sites(), budget_units=24.0)
    assert result.success
    assert result.total_cost <= 24.0 + 1e-9
    assert result.selected["site"].is_unique
    assert len(result.selected) <= 6
    assert len(result.assignments) == 2 * len(cells)
    assert set(result.assignments["mission"]) == {"suppression", "isr"}
    assert result.assignments["response_min"].gt(0).all()


def test_assignments_use_opened_compatible_facilities() -> None:
    result = optimise_network(_baseline_cells(), make_candidate_sites(), budget_units=24.0)
    selected_ids = set(result.selected["option_id"])
    assert set(result.assignments["option_id"]).issubset(selected_ids)
    for row in result.assignments.itertuples():
        base = BASE_TYPE_BY_CODE[row.type_code]
        if row.mission == "suppression":
            assert base.supports_suppression
            assert base.suppression_range_km is not None
            assert row.distance_km <= base.suppression_range_km + 1e-6
        else:
            assert base.supports_isr
            assert base.isr_range_km is not None
            assert row.distance_km <= base.isr_range_km + 1e-6


def test_reference_network_exposes_rpas_and_crewed_capability() -> None:
    result = optimise_network(
        apply_scenario(make_synthetic_risk_cells(), SCENARIOS[0]),
        make_candidate_sites(),
        budget_units=24.0,
    )
    assert result.success
    assert (result.selected["type_code"] == "RPAS").any()
    assert result.selected["supports_suppression"].any()


def test_relaxing_budget_does_not_worsen_optimal_objective() -> None:
    cells = _baseline_cells()
    sites = make_candidate_sites()
    lower = optimise_network(cells, sites, budget_units=18.0)
    higher = optimise_network(cells, sites, budget_units=24.0)
    assert lower.success and higher.success
    assert higher.objective <= lower.objective + 1e-8
    lower_metrics = network_metrics(lower.assignments)
    higher_metrics = network_metrics(higher.assignments)
    assert higher_metrics["suppression_risk_weighted_mean_response_min"] > 0
    assert lower_metrics["isr_risk_weighted_mean_response_min"] > 0
