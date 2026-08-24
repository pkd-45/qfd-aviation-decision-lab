import numpy as np

from qfd_aviation_lab.geo import haversine_matrix


def test_haversine_zero_distance() -> None:
    matrix = haversine_matrix(
        np.array([-27.47]), np.array([153.03]), np.array([-27.47]), np.array([153.03])
    )
    assert matrix.shape == (1, 1)
    assert matrix[0, 0] < 1e-9
