import numpy as np


def image_data() -> np.ndarray:
    return np.arange(100).reshape(10, 10)


def labels_data() -> np.ndarray:
    return np.arange(100).reshape(10, 10) % 5


def points_data() -> np.ndarray:
    return np.arange(30).reshape(10, 3)


def shapes_data() -> list[np.ndarray]:
    return [np.arange(4).reshape(2, 2), np.arange(4).reshape(2, 2) + 1]


def surface_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    vertices = np.array([[0, 0], [0, 20], [10, 0], [10, 10]])
    faces = np.array([[0, 1, 2], [1, 2, 3]])
    values = np.linspace(0, 1, len(vertices))
    return (vertices, faces, values)


def tracks_data() -> np.ndarray:
    zyx = np.arange(30).reshape(10, 3)
    t = np.concatenate([np.arange(5), np.arange(5)])
    return np.concatenate([t[:, None], zyx], axis=1)


def vectors_data() -> np.ndarray:
    return np.arange(60).reshape(10, 2, 3)
