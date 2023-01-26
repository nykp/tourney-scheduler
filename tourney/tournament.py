from dataclasses import dataclass
from datetime import datetime
from itertools import repeat
from typing import List, NamedTuple, Optional, Sequence, Union

import pandas as pd
import pendulum

from .match import Match, MatchSeries, Team
from .match_utils import Matches


class Game(NamedTuple):
    game: int
    time: datetime
    match: Match
    referee: Optional[Team] = None
    scoreboard: Optional[Team] = None


@dataclass
class Tournament:
    games: Sequence[Game]

    @staticmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "Tournament":
        required_cols = ["time", "home", "away"]
        optional_cols = ["game", "referee", "scoreboard"]

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Tournament table is missing columns: {', '.join(missing_cols)}")
        columns = required_cols
        for col in optional_cols:
            if col in df.columns:
                columns.append(col)
        games = []
        for idx, row in enumerate(df.to_dict(orient='records')):
            dt = row["time"]
            if isinstance(dt, str):
                dt = pendulum.parse(dt)
            games.append(
                Game(
                    row.get("game", idx + 1),
                    dt,
                    Match(row["home"], row["away"]),
                    row.get("referee"),
                    row.get("scoreboard"),
                )
            )
        return cls(games)

    @classmethod
    def create(
        cls,
        matches: Matches,
        times: Sequence[Union[str, datetime]],
        referees: Optional[Sequence[Team]] = None,
        scoreboard: Optional[Sequence[Team]] = None,
    ) -> "Tournament":
        if len(matches) != len(times):
            raise ValueError(
                f"The number of times ({len(times)}) does not equal the number of matches ({len(matches)})"
            )
        if referees:
            if len(referees) != len(matches):
                raise ValueError(
                    f"The number of referees ({len(referees)}) does not equal the number of matches ({len(matches)})"
                )
        else:
            referees = repeat(None)
        if scoreboard:
            if len(scoreboard) != len(matches):
                raise ValueError(
                    f"The number of scoreboard teams ({len(scoreboard)}) does not equal the number of matches"
                    f" ({len(matches)})"
                )
        else:
            scoreboard = repeat(None)

        games = []
        for i, (match, time, ref, score) in enumerate(zip(matches, times, referees, scoreboard)):
            if isinstance(time, str):
                time = pendulum.parse(time)
            games.append(Game(i + 1, time, match, ref, score))
        return cls(games)

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame([game._asdict() for game in self.games])
        return df.dropna(axis=1, how="all")

    @property
    def teams(self) -> List[Team]:
        return sorted(set([t for g in self for t in g.match]))

    @property
    def matches(self) -> MatchSeries:
        return MatchSeries(g.match for g in self)

    def __len__(self) -> int:
        return len(self.games)

    def __iter__(self):
        return iter(self.games)

    def __getitem__(self, idx: int) -> Game:
        return self.games[idx]

    def __str__(self) -> str:
        dates = sorted(set([g.time.strftime("%Y-%m-%d") for g in self]))
        teams = self.teams
        return f"{type(self).__name__}({len(self)} games, {len(teams)} teams: {teams}, dates: {dates})"

    def __repr__(self):
        return str(self)
