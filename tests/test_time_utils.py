from datetime import timedelta

import pytest

from tourney.time_utils import as_time, get_available_times, TimeWindow


def test_as_time():
    # times (no dates)
    t1s = "12:34:56"
    t1 = as_time(t1s)
    t2 = t1 + timedelta(hours=2)
    t3 = t1 + timedelta(hours=23)
    assert t2 > t1
    assert t3 < t1

    # datetimes
    dt1s = "2023-01-01 12:34"
    dt2s = "2023-01-01 12:34:56-05:00"
    dt1 = as_time(dt1s)
    dt2 = as_time(dt2s)
    assert dt2 > dt1

    dt2s = "2023-01-01 12:34-05:00"
    dt1s = "2023-01-01 12:34:56"
    dt1 = as_time(dt1s)
    dt2 = as_time(dt2s)
    assert dt2 > dt1

    # AM/PM
    assert (as_time("12:34pm") - as_time("12:34:00am")).total_minutes() == 12 * 60


def test_TimeWindow():
    t1 = as_time("08:34:56")
    t2 = as_time("12:34:56")
    w1 = TimeWindow(t1, t2)
    w1b = TimeWindow((t1, t2))
    assert w1b == w1
    assert TimeWindow(t1, t1) != w1
    with pytest.raises(ValueError):
        TimeWindow(t2, t1)
    with pytest.raises(ValueError):
        TimeWindow(t1, t2, t1)
    with pytest.raises(TypeError):
        TimeWindow(t2 - t1)

    assert (t1 + timedelta(hours=1)) in w1

    t3 = t1 + (t2 - t1) / 2
    assert t3 in w1
    t4 = t2 + timedelta(hours=1)
    assert w1.overlaps((t3, t4))

    assert TimeWindow(t1, t1).as_timedelta().total_seconds() == 0

    # Using datetimes
    dt1 = as_time("2023-01-01 08:34:56")
    dt2 = as_time("2023-01-01 12:34:56")
    dt12 = dt2 - dt1
    w2 = TimeWindow(dt12)
    w3 = TimeWindow(dt1 + dt12 / 2, dt2 + dt12 / 2)
    assert w2.overlaps(w3) is True


def test_get_available_times():
    game_minutes = 25
    game_duration = timedelta(minutes=game_minutes)
    start_1 = as_time("15:40")
    end_1 = start_1 + 4 * game_duration
    start_2 = as_time("9:30")
    end_2 = start_2 + 4.2 * game_duration
    times = get_available_times([(start_1, end_1), (start_2, end_2)], minutes_per_game=game_minutes)
    assert len(times) == 8

    w1 = TimeWindow(start_1, end_1)
    w2 = TimeWindow(start_2, end_2)
    assert all([t in w1 or t in w2 for t in times])
