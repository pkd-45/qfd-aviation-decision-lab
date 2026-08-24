from __future__ import annotations

import numpy as np
import pandas as pd

CANDIDATE_SITES = (
    ("Brisbane", -27.47, 153.03),
    ("Toowoomba", -27.56, 151.95),
    ("Bundaberg", -24.87, 152.35),
    ("Rockhampton", -23.38, 150.51),
    ("Mackay", -21.14, 149.19),
    ("Townsville", -19.26, 146.82),
    ("Cairns", -16.92, 145.78),
    ("Roma", -26.57, 148.79),
    ("Longreach", -23.44, 144.25),
    ("Mount Isa", -20.73, 139.49),
    ("Charleville", -26.40, 146.24),
    ("Emerald", -23.53, 148.16),
)


DEMAND_CENTRES = (
    ("SE", -27.2, 152.7, 1.7),
    ("WideBay", -25.1, 152.2, 1.0),
    ("Central", -23.6, 150.3, 1.0),
    ("Whitsunday", -21.1, 149.0, 0.8),
    ("North", -19.5, 146.6, 1.0),
    ("FarNorth", -16.9, 145.6, 0.9),
    ("DarlingDowns", -27.1, 150.6, 0.9),
    ("CentralWest", -23.5, 145.0, 0.65),
    ("NorthWest", -20.7, 140.2, 0.55),
)


def make_candidate_sites() -> pd.DataFrame:
    """Return illustrative regional-centre candidate locations.

    These are demonstration locations only. They are not asserted to be current QFD
    aviation facilities or recommended sites.
    """
    return pd.DataFrame(CANDIDATE_SITES, columns=["site", "lat", "lon"])


def make_synthetic_risk_cells(seed: int = 3040, n_cells: int = 54) -> pd.DataFrame:
    """Create deterministic Queensland-inspired synthetic demand/risk cells."""
    rng = np.random.default_rng(seed)
    weights = np.array([c[3] for c in DEMAND_CENTRES], dtype=float)
    weights /= weights.sum()
    centre_idx = rng.choice(len(DEMAND_CENTRES), size=n_cells, p=weights)

    rows: list[dict[str, float | int | str]] = []
    for cell_id, idx in enumerate(centre_idx):
        name, centre_lat, centre_lon, _ = DEMAND_CENTRES[idx]
        lat = float(np.clip(rng.normal(centre_lat, 1.15), -28.9, -10.7))
        lon = float(np.clip(rng.normal(centre_lon, 1.25), 138.2, 153.4))

        inland = np.clip((151.8 - lon) / 12.5, 0.0, 1.0)
        north = np.clip((-lat - 14.0) / 15.0, 0.0, 1.0)
        south_east = np.exp(-(((lat + 27.4) / 2.4) ** 2 + ((lon - 152.5) / 2.4) ** 2))
        regional = np.exp(-(((lat + 23.5) / 4.2) ** 2 + ((lon - 148.0) / 4.5) ** 2))

        bushfire_hazard = float(
            np.clip(0.30 + 0.35 * inland + 0.20 * regional + rng.normal(0, 0.08), 0.05, 1.0)
        )
        climate_exposure = float(
            np.clip(0.25 + 0.28 * north + 0.32 * inland + rng.normal(0, 0.07), 0.05, 1.0)
        )
        vulnerability = float(
            np.clip(0.20 + 0.52 * south_east + 0.22 * regional + rng.normal(0, 0.08), 0.05, 1.0)
        )
        water_scarcity = float(np.clip(0.12 + 0.70 * inland + rng.normal(0, 0.07), 0.02, 1.0))

        rows.append(
            {
                "cell_id": cell_id,
                "region_cluster": name,
                "lat": lat,
                "lon": lon,
                "bushfire_hazard": bushfire_hazard,
                "climate_exposure": climate_exposure,
                "vulnerability": vulnerability,
                "water_scarcity": water_scarcity,
            }
        )

    df = pd.DataFrame(rows)
    # Multiplicative structure prevents a single high component from dominating by itself.
    df["baseline_risk"] = (
        0.42 * df["bushfire_hazard"]
        + 0.20 * df["climate_exposure"]
        + 0.28 * df["vulnerability"]
        + 0.10 * df["water_scarcity"]
    )
    df["baseline_risk"] /= df["baseline_risk"].sum()
    return df
