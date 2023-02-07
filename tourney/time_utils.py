from datetime import datetime, timedelta
from pytz import UTC
from typing import List, Sequence, Union

import pendulum
from pendulum.period import Period


TimeLike = Union[str, datetime]


def as_datetime(t: TimeLike) -> datetime:
    if isinstance(t, str):
        return pendulum.parse(t)
    elif not isinstance(t, datetime):
        raise TypeError("Argument must be pendulum-parsable string or a datetime instance")
    else:
        if not t.tzinfo:
            return t.replace(tzinfo=UTC)
        else:
            return t


class TimeWindow:
    def __init__(self, *args: Union[TimeLike, Sequence[TimeLike], "TimeWindowLike"]):
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, Period):
                self.start = arg.start
                self.end = arg.end
            else:
                start, end = arg
                self.start = as_datetime(start)
                self.end = as_datetime(end)
        elif len(args) == 2:
            start, end = args
            if start > end:
                raise ValueError("start is after end")
            self.start = as_datetime(start)
            self.end = as_datetime(end)
        else:
            raise ValueError("Unexpected number of arguments; should be single period arg or two datetime args")

    def __iter__(self):
        return iter([self.start, self.end])

    def as_timedelta(self) -> timedelta:
        return self.end - self.start

    def __contains__(self, other: Union[TimeLike, "TimeWindowLike"]) -> bool:
        if isinstance(other, TimeLike):
            return self.start <= other < self.end
        else:
            other = TimeWindow(other)
            return other.start in self and other.end in self

    def overlaps(self, other: "TimeWindowLike") -> bool:
        other = TimeWindow(other)
        if self.start <= other.start:
            first = self
            second = other
        else:
            first = other
            second = self
        return first.end > second.start

    def __eq__(self, other: "TimeWindow") -> bool:
        return self.start == other.start and self.end == other.end


TimeWindowLike = Union[TimeWindow, Period, Sequence[TimeLike]]


def get_available_times(
    time_windows: Union[TimeWindowLike, Sequence[TimeWindowLike]],
    minutes_per_game: int = 30,
) -> List[datetime]:
    try:
        time_windows = [TimeWindow(time_windows)]
    except TypeError:
        time_windows = [TimeWindow(w) for w in time_windows]
    times = []
    delta = timedelta(minutes=minutes_per_game)
    for window in time_windows:
        current_time = window.start
        next_time = current_time + delta
        while next_time <= window.end:
            times.append(current_time)
            current_time = next_time
            next_time += delta
    return times
