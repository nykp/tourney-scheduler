from itertools import combinations
from typing import Dict, Iterable, List, NamedTuple, Sequence, TypeVar, Union

Team = TypeVar("Team")


class Match(NamedTuple):
    home: Team
    away: Team

    def swap(self) -> "Match":
        return Match(self[1], self[0])

    def __str__(self) -> str:
        return f"{self[0]} vs. {self[1]}"

    def __repr__(self) -> str:
        return str(self)


class MatchSeries:
    def __init__(self, matches: Iterable[Match]):
        self.matches: List[Match] = list(matches)

    @property
    def teams(self) -> List[Team]:
        return sorted(set([team for match in self for team in match]))

    def __len__(self) -> int:
        return len(self.matches)

    def __iter__(self):
        return iter(self.matches)

    def __getitem__(self, idx: int) -> Match:
        return self.matches[idx]

    def __add__(self, other: Union[Match, Sequence[Match], "MatchSeries"]) -> "MatchSeries":
        if isinstance(other, Match):
            other = [other]
        other = MatchSeries(other)
        return MatchSeries(self.matches + other.matches)

    def pop(self, match: Union[int, Match]) -> Match:
        if isinstance(match, Match):
            match = self.matches.index(match)
        return self.matches.pop(match)

    @classmethod
    def all_pairs(cls, teams: Sequence[Team]):
        return cls([Match(a, b) for a, b in combinations(teams, 2)])

    def game_intervals_by_team(self) -> Dict[Team, List[int]]:
        intervals = {}
        for team in self.teams:
            team_intervals = []
            last_idx = -1
            for idx, match in enumerate(self.matches):
                if team in match:
                    team_intervals.append(idx - last_idx - 1)
                    last_idx = idx
            team_intervals.append(idx - last_idx)
            intervals[team] = team_intervals
        return intervals

    def __str__(self) -> str:
        return "\n".join(map(str, self))

    def __repr__(self) -> str:
        return str(self)