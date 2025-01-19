from random import seed as set_seed, shuffle
from statistics import variance
from typing import Dict

import numpy as np

from ..match import Team
from ..match_utils import get_teams, Matches, MatchSeries, TeamsOrNumber


def _get_team_priorities(played: Matches) -> Dict[Team, int]:
    priorities = {}
    for distance, match in enumerate(played[::-1]):
        for team in match:
            if team not in priorities:
                priorities[team] = distance
    return priorities


def _get_match_priorities(teams: TeamsOrNumber, scheduled: Matches, remaining: Matches):
    teams = get_teams(teams)
    priorities = []
    unscheduled_priority = len(teams)
    team_priorities = _get_team_priorities(scheduled)
    for team_1, team_2 in remaining:
        team_1_priority = team_priorities.get(team_1, unscheduled_priority)
        team_2_priority = team_priorities.get(team_2, unscheduled_priority)
        priorities.append(team_1_priority * team_2_priority)
    return priorities


def get_priority_schedule(teams: TeamsOrNumber, num_candidates=5, rng_seed=None) -> MatchSeries:
    teams = get_teams(teams)
    all_matches = MatchSeries.all_pairs(teams, ids=False)
    if rng_seed is not None:
        set_seed(rng_seed)

    def get_candidate_schedule() -> MatchSeries:
        scheduled = []
        remaining = all_matches[:]
        while len(scheduled) < len(all_matches):
            priorities = _get_match_priorities(teams, scheduled, remaining)
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
    best_schedule = candidate_schedules[best_idx]
    return MatchSeries([m.with_id(i + 1) for i, m in enumerate(best_schedule)])
