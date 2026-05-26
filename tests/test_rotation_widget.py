import pytest
from ui.rotation_widget import RotationWidget


def test_initial_rotation_is_zero(qapp):
    w = RotationWidget()
    assert w.rotation() == 0


def test_rotate_left_adds_90(qapp):
    w = RotationWidget()
    w.rotate_left()
    assert w.rotation() == 90


def test_rotate_right_subtracts_90(qapp):
    w = RotationWidget()
    w.rotate_right()
    assert w.rotation() == 270


def test_accumulates_left(qapp):
    w = RotationWidget()
    w.rotate_left()
    w.rotate_left()
    assert w.rotation() == 180


def test_accumulates_right(qapp):
    w = RotationWidget()
    w.rotate_right()
    w.rotate_right()
    assert w.rotation() == 180


def test_wraps_at_360(qapp):
    w = RotationWidget()
    for _ in range(4):
        w.rotate_left()
    assert w.rotation() == 0


def test_label_shows_angle(qapp):
    w = RotationWidget()
    w.rotate_left()
    assert w._label.text() == "90°"


def test_reset_sets_to_zero(qapp):
    w = RotationWidget()
    w.rotate_left()
    w.rotate_left()
    w.reset()
    assert w.rotation() == 0
    assert w._label.text() == "0°"
