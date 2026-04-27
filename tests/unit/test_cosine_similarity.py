import numpy as np
import pytest

from perfume_bot.services.recommendation import cosine_similarity, build_note_vector


def test_identical_vectors_similarity_is_one():
    a = np.array([1, 0, 1, 1, 0], dtype=float)
    assert cosine_similarity(a, a) == pytest.approx(1.0)


def test_zero_intersection_similarity_is_zero():
    a = np.array([1, 0, 0], dtype=float)
    b = np.array([0, 1, 0], dtype=float)
    assert cosine_similarity(a, b) == pytest.approx(0.0)


def test_partial_overlap():
    a = np.array([1, 1, 0], dtype=float)
    b = np.array([1, 0, 1], dtype=float)
    result = cosine_similarity(a, b)
    assert 0.0 < result < 1.0


def test_zero_vector_returns_zero():
    zero = np.array([0, 0, 0], dtype=float)
    other = np.array([1, 1, 0], dtype=float)
    assert cosine_similarity(zero, other) == pytest.approx(0.0)


def test_build_note_vector_basic():
    all_note_ids = [1, 2, 3, 4, 5]
    selected_ids = {1, 3}
    vec = build_note_vector(all_note_ids, selected_ids)
    assert vec.tolist() == [1.0, 0.0, 1.0, 0.0, 0.0]
