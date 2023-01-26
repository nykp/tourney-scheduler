from more_itertools import pairwise
from typing import Sequence, Union

from .match import Match, MatchSeries

Matches = Union[MatchSeries, Sequence[Match]]


def shares_team(match_1: Match, match_2: Match) -> bool:
    return len(set(match_1).intersection(set(match_2))) > 0


def any_back_to_back(matches: Matches) -> bool:
    return any([shares_team(*match) for match in pairwise(matches)])
