from collections import defaultdict
from datetime import datetime
from itertools import cycle
from random import seed as set_seed, shuffle
from statistics import variance
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

from .match import Team
from .match_utils import Matches, MatchSeries


def get_team_priorities(played: Matches) -> Dict[Team, int]:
    priorities = {}
    for distance, match in enumerate(played[::-1]):
        for team in match:
            if team not in priorities:
                priorities[team] = distance
    return priorities


def get_match_priorities(teams: Sequence[Team], scheduled: Matches, remaining: Matches):
    priorities = []
    unscheduled_priority = len(teams)
    team_priorities = get_team_priorities(scheduled)
    for team_1, team_2 in remaining:
        team_1_priority = team_priorities.get(team_1, unscheduled_priority)
        team_2_priority = team_priorities.get(team_2, unscheduled_priority)
        priorities.append(team_1_priority * team_2_priority)
    return priorities


def get_priority_schedule(teams: Sequence[Team], num_candidates=5, seed=None):
    all_matches = MatchSeries.all_pairs(teams)
    if seed is not None:
        set_seed(seed)

    def get_candidate_schedule() -> MatchSeries:
        scheduled = []
        remaining = all_matches[:]
        while len(scheduled) < len(all_matches):
            priorities = get_match_priorities(teams, scheduled, remaining)
            max_priority = max(priorities)
            highest = [idx for idx, priority in enumerate(priorities) if priority == max_priority]
            shuffle(highest)
            scheduled.append(remaining.pop(highest[0]))
        return MatchSeries(scheduled)

    def score_schedule(matches: MatchSeries) -> float:
        game_intervals = matches.game_intervals_by_team()
        return variance([i for intervals in game_intervals.values() for i in intervals])

    candidate_schedules = [get_candidate_schedule() for _ in range(num_candidates)]
    candidate_scores = [score_schedule(candidate) for candidate in candidate_schedules]
    best_idx = np.argmin(candidate_scores)
    return candidate_schedules[best_idx]


def get_ref_schedule(teams: Sequence[Team], matches: Matches, seed=None) -> Tuple[List[Team], Dict[Team, int]]:
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
        if candidate in matches[current_idx]:
            continue
        else:
            schedule.append(candidate)
            counts[candidate] += 1
            sorted_candidates = get_sorted_cycler()
    return schedule, counts


def value_counts(sequence: Sequence[Any]) -> Dict[Any, int]:
    counts = defaultdict(int)
    for value in sequence:
        counts[value] += 1
    return dict(counts)


def get_scoreboard_schedule(teams, matches, refs, seed=None) -> Tuple[List[Team], Dict[Team, int]]:
    if len(teams) < 4:
        raise ValueError("Too few teams to have separate scoreboard operators")
    if seed is not None:
        set_seed(seed)

    teams = list(teams)
    shuffle(teams)
    counts = {team: 0 for team in teams}
    ref_counts = value_counts(refs)

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


def get_game_times(windows, minutes_per_game) -> List[datetime]:
    pass
