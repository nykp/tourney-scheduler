from datetime import datetime, time, timedelta
from pytz import UTC
from typing import List, Sequence, Union

import pendulum
from pendulum.period import Period


TimeLike = Union[datetime, str, time]
TimeDateTime = Union[datetime, time]


def as_time(t: TimeLike) -> TimeDateTime:
    if isinstance(t, str):
        if t.lower().endswith("am"):
            tmp = pendulum.parse(t[:-2].strip(), exact=True)
            if tmp.hour == 12:
                tmp -= timedelta(hours=12)
            return tmp
        elif t.lower().endswith("pm"):
            tmp = pendulum.parse(t[:-2].strip(), exact=True)
            if tmp.hour == 12:
                tmp -= timedelta(hours=12)
            return tmp + timedelta(hours=12)
        else:
            return pendulum.parse(t, exact=True)
    elif isinstance(t, datetime):
        if not t.tzinfo:
            return t.replace(tzinfo=UTC)
        else:
            return t
    elif isinstance(t, time):
        return t
    else:
        raise TypeError("Argument must be pendulum-parsable string or a datetime instance")


class TimeWindow:
    def __init__(self, *args: Union[TimeLike, Sequence[TimeLike], "TimeWindowLike"]):
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, Period):
                self.start = arg.start
                self.end = arg.end
            else:
                try:
                    start, end = arg
                except (TypeError, ValueError):
                    raise TypeError("If single argument is used, it must be a period or (start, end) pair.")
                self.start = as_time(start)
                self.end = as_time(end)
        elif len(args) == 2:
            start, end = args
            start = as_time(start)
            end = as_time(end)
            if start > end:
                raise ValueError("start is after end. If times are correct, you may need to include the dates.")
            self.start = start
            self.end = end
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

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.start} --> {self.end})"

    def __repr__(self) -> str:
        return str(self)


TimeWindowLike = Union[TimeWindow, Period, Sequence[TimeLike]]


def get_available_times(
    time_windows: Union[TimeWindowLike, Sequence[TimeWindowLike]],
    minutes_per_game: int = 30,
) -> List[TimeDateTime]:
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
