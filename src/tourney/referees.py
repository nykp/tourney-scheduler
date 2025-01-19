from collections import defaultdict
from datetime import datetime
from itertools import cycle
from random import seed as set_seed, shuffle
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .match import Team
from .match_utils import Matches


def get_ref_schedule(
        teams: Sequence[Team],
        matches: Matches,
        times: Optional[Sequence[datetime]] = None,
        seed=None
) -> Tuple[List[Team], Dict[Team, int]]:
    if len(teams) < 3:
        raise ValueError("Too few teams to have referees")
    if seed is not None:
        set_seed(seed)

    teams = list(teams)
    shuffle(teams)
    counts = {team: 0 for team in teams}

    def get_sorted_cycler():
        return cycle([t[0] for t in sorted(counts.items(), key=lambda t: t[1])])

    sorted_candidates = get_sorted_cycler()
    schedule = []
    while len(schedule) < len(matches):
        candidate = next(sorted_candidates)
        current_idx = len(schedule)
        current_match = matches[current_idx]
        current_time = times[current_idx] if times else None
        next_match = matches[current_idx + 1] if current_idx < len(matches) - 1 else None
        next_time = times[current_idx + 1] if times and (current_idx < len(matches) - 1) else None
        if candidate in current_match:
            continue
        elif next_match and len(teams) > 4 and candidate in next_match:
            if next_time and (next_time.date() == current_time.date()):
                continue
        else:
            schedule.append(candidate)
            counts[candidate] += 1
            sorted_candidates = get_sorted_cycler()
    return schedule, counts


def _value_counts(sequence: Sequence[Any]) -> Dict[Any, int]:
    counts = defaultdict(int)
    for value in sequence:
        counts[value] += 1
    return dict(counts)


def get_scoreboard_schedule(
    teams: Sequence[Team],
    matches: Matches,
    refs: Sequence[Team],
    seed=None
) -> Tuple[List[Team], Dict[Team, int]]:

    if len(teams) < 4:
        raise ValueError("Too few teams to have separate scoreboard operators")
    if seed is not None:
        set_seed(seed)

    teams = list(teams)
    shuffle(teams)
    counts = {team: 0 for team in teams}
    ref_counts = _value_counts(refs)

    def get_sorted_cycler():
        return cycle([t[0] for t in sorted(counts.items(), key=lambda t: t[1] + ref_counts.get(t[0], 0))])

    sorted_candidates = get_sorted_cycler()
    schedule = []
    while len(schedule) < len(matches):
        candidate = next(sorted_candidates)
        current_idx = len(schedule)
        if candidate in matches[current_idx] or candidate == refs[current_idx]:
            continue
        else:
            schedule.append(candidate)
            counts[candidate] += 1
            sorted_candidates = get_sorted_cycler()
    return schedule, counts
