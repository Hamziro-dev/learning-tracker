# tests/test_logic.py
from logic.tracker import Tracker

def test_add_entry():
    tracker = Tracker()
    tracker.add_entry("Python", 3)
    tracker.add_entry("Kivy", 2)
    assert tracker.total_hours("Python") == 3
    assert tracker.total_hours("Kivy") == 2