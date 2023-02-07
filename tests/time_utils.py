import pytest

from tourney.time_utils import as_datetime, TimeWindow


def test_as_datetime():
    t1s = "2023-01-01 12:34:56"
    t2s = "2023-01-01 12:34:56-05:00"
    t1 = as_datetime(t1s)
    t2 = as_datetime(t2s)
    assert t2 > t1


def test_TimeWindow():
    t1 = as_datetime("2023-01-01 08:34:56")
    t2 = as_datetime("2023-01-01 12:34:56")
    w1 = TimeWindow(t1, t2)
    w1b = TimeWindow((t1, t2))
    w1c = TimeWindow(t2 - t1)
    assert w1b == w1
    assert w1c == w1
    assert TimeWindow(t1, t1) != w1
    with pytest.raises(ValueError):
        TimeWindow(t2, t1)
    with pytest.raises(ValueError):
        TimeWindow(t1, t2, t1)

    t3 = t1 + (t2 - t1) / 2
    assert t3 in w1
    t4 = t2.add(hours=1)
    assert w1.overlaps((t3, t4))

    assert TimeWindow(t1, t1).as_timedelta().total_seconds() == 0


def test_get_available_times():
    # TODO
    pass
