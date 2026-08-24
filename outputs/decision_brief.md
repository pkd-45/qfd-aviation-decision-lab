# Aviation network decision-support demo

## Purpose

This is a synthetic, portfolio-scale demonstration of a risk-based framework for comparing aviation hub and airbase configurations. It demonstrates methodology, not operational recommendations to QFD.

## Decision model

The optimiser jointly considers two illustrative service missions: crewed suppression response and intelligence/surveillance (ISR), including RPAS nodes.
Synthetic mission-priority weights are suppression 60% and ISR 40%. These are demonstration assumptions, not QFD policy weights.
Scenario risk is separated into (1) an aggregate pressure index and (2) normalised spatial risk weights. This avoids conflating changing statewide pressure with changing geographic allocation of risk.

## Baseline illustrative configuration

Budget constraint: **24.0 synthetic cost units**.

- **Brisbane** — RPAS / local ISR node (RPAS); cost 1.5
- **Toowoomba** — Regional airbase (REG); cost 4.5
- **Rockhampton** — Regional airbase (REG); cost 4.5
- **Townsville** — Strategic aviation hub (HUB); cost 9.0
- **Charleville** — Regional airbase (REG); cost 4.5

## Baseline service metrics

- Suppression risk-weighted mean response: **59.3 min**
- Suppression risk-weighted 60-minute coverage: **57.5%**
- ISR risk-weighted mean response: **73.7 min**
- ISR risk-weighted 60-minute coverage: **41.9%**

## Scenario stress test

| Scenario | Pressure index | Suppression mean (min) | Suppression 60-min coverage | ISR mean (min) | Configuration changed? |
|---|---:|---:|---:|---:|---|
| baseline | 1.00 | 59.3 | 57.5% | 73.7 | no |
| severe_drought | 1.13 | 60.4 | 55.3% | 73.9 | no |
| extreme_fire_weather | 1.30 | 59.9 | 55.0% | 74.1 | no |
| future_stress_test | 1.21 | 59.9 | 55.2% | 74.0 | no |

### Configuration stability

The reference-budget site/type configuration remains unchanged across all four illustrative scenarios. In this synthetic example, the stress tests therefore degrade service metrics without causing a network substitution.

## Fiscal sensitivity

| Budget | Feasible | Sites | RPAS nodes | Suppression mean (min) | ISR mean (min) |
|---:|---|---:|---:|---:|---:|
| 15.0 | no | — | — | — | — |
| 18.0 | yes | 4 | 0 | 62.8 | 89.3 |
| 21.0 | yes | 6 | 2 | 62.8 | 80.7 |
| 24.0 | yes | 5 | 1 | 59.3 | 73.7 |
| 27.0 | yes | 4 | 0 | 56.6 | 67.4 |
| 30.0 | yes | 6 | 2 | 56.6 | 63.0 |

An infeasible low-budget point means the model cannot satisfy both mission coverage requirements with the available synthetic facility options and budget; it is not treated as a numerical failure.

## GIS-ready outputs

The demo writes GeoJSON layers for candidate sites, scenario risk cells, selected networks and mission assignment lines. These can be opened directly in GIS software such as QGIS for inspection or further styling.

## What this prototype demonstrates

- A transparent spatial risk layer combining hazard, climate exposure, vulnerability and water scarcity.
- A standardised data model for strategic hubs, regional airbases, mobile staging bases and RPAS/ISR nodes.
- Multi-mission mixed-integer optimisation under a fiscal constraint.
- Separate suppression and ISR response/coverage metrics for decision-makers.
- Scenario pressure, spatial reweighting and network-stability diagnostics.
- A budget-versus-service frontier, including explicit infeasibility.
- GIS-ready GeoJSON products alongside CSV, JSON and maps.

## What is not claimed

- No QFD operational, incident, aviation, water or infrastructure data are used.
- Candidate locations are illustrative regional centres, not asserted QFD facilities or recommendations.
- The four-level facility typology is a prototype software schema, not a claimed national standard.
- Synthetic cost, range, readiness, speed and mission-weight parameters are placeholders.
- Aircraft availability, duty limits, simultaneous incidents, refuelling logistics, terrain and detailed weather routing remain outside this prototype.
