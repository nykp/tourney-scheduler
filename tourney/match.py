from itertools import combinations, count, repeat
from typing import Dict, Hashable, Iterable, List, NamedTuple, Optional, Sequence, TypeVar, Union

Team = TypeVar("Team")


class Match:
    def __init__(self, home: Team, away: Team, id: Optional[Hashable] = None):
        self.home = home
        self.away = away
        self.id = id

    def with_id(self, id: Optional[Hashable]) -> "Match":
        return Match(self.home, self.away, id)

    def swap(self, id=None) -> "Match":
        return type(self)(self.away, self.home, id=id)

    def __iter__(self):
        return iter((self.home, self.away))

    def __contains__(self, team: Team) -> bool:
        return team in tuple(self)

    def __str__(self) -> str:
        s = f"{self.home} vs. {self.away}"
        if self.id is not None:
            s += f" (id: {self.id})"
        return s

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
    def all_pairs(cls, teams: Sequence[Team], ids: Union[bool, Iterable[Hashable]] = None):
        if ids:
            if isinstance(ids, bool):
                ids = count(1)
        else:
            ids = repeat(None)

        return cls([Match(a, b, id=id) for (a, b), id in zip(combinations(teams, 2), ids)])

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
