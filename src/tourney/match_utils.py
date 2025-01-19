from more_itertools import pairwise
from typing import List, Sequence, Union

from .match import Match, MatchSeries, Team

Matches = Union[MatchSeries, Sequence[Match]]
TeamsOrNumber = Union[int, Sequence[Team]]


def get_teams(teams: TeamsOrNumber) -> List[Team]:
    try:
        return [f"Team {i + 1}" for i in range(int(teams))]
    except TypeError:
        return list(teams)


def shares_team(match_1: Match, match_2: Match) -> bool:
    return len(set(match_1).intersection(set(match_2))) > 0


def any_back_to_back(matches: Matches) -> bool:
    return any([shares_team(*match) for match in pairwise(matches)])
