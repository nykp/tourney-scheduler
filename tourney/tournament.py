from dataclasses import dataclass
from itertools import repeat
from math import floor, log2
from typing import List, NamedTuple, Optional, Sequence, Union

import pandas as pd
import pendulum

from .elimination.scheduler import get_seeded_schedule
from .match import Match, MatchSeries, Team
from .match_utils import get_teams, Matches, TeamsOrNumber
from .referees import get_ref_schedule, get_scoreboard_schedule
from .round_robin.scheduler import get_priority_schedule
from .time_utils import TimeDateTime, TimeLike


class Game(NamedTuple):
    game: int
    time: TimeDateTime
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
            game_id = row.get("game", idx + 1)
            games.append(
                Game(
                    game_id,
                    dt,
                    Match(row["home"], row["away"], id=game_id),
                    row.get("referee"),
                    row.get("scoreboard"),
                )
            )
        return cls(games)

    @classmethod
    def create(
        cls,
        matches: Matches,
        times: Sequence[TimeLike],
        referees: Optional[Sequence[Team]] = None,
        scoreboard: Optional[Sequence[Team]] = None,
    ) -> "Tournament":
        if len(matches) > len(times):
            raise ValueError(
                f"Too few available times ({len(times)}) for the number of matches ({len(matches)})"
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
            game_id = match.id if match.id is not None else i + 1
            games.append(Game(game_id, time, match, ref, score))
        return cls(games)

    @classmethod
    def schedule_round_robin(
        cls,
        teams: TeamsOrNumber,
        times: Sequence[TimeLike],
        with_referees=True,
        with_scoreboard=True,
        num_candidates=5,
        rng_seed=None,
    ) -> "Tournament":
        teams = get_teams(teams)
        matches = get_priority_schedule(teams, num_candidates=num_candidates, rng_seed=rng_seed)
        referees = None
        scoreboards = None
        if with_referees:
            referees, _ = get_ref_schedule(teams, matches)
            if with_scoreboard:
                scoreboards, _ = get_scoreboard_schedule(teams, matches, referees)
        return cls.create(matches=matches, times=times, referees=referees, scoreboard=scoreboards)

    @classmethod
    def schedule_elimination(
        cls,
        teams: TeamsOrNumber,
        times: Sequence[TimeLike],
        with_referees=True,
        with_scoreboard=True,
        ranks: Optional[Union[Sequence[int], str]] = None,
        game_number_start=1,
        rng_seed=None,
    ) -> "Tournament":
        teams = get_teams(teams)
        matches = get_seeded_schedule(teams, ranks=ranks, game_number_start=game_number_start, rng_seed=rng_seed)
        referees = None
        scoreboards = None
        if with_referees:
            referees, _ = get_ref_schedule(teams, matches)
            if with_scoreboard:
                scoreboards, _ = get_scoreboard_schedule(teams, matches, referees)
        return cls.create(matches=matches, times=times, referees=referees, scoreboard=scoreboards)

    @classmethod
    def schedule_round_robin_with_playoffs(
        cls,
        teams: TeamsOrNumber,
        times: Sequence[TimeLike],
        playoff_teams: Optional[int] = None,
        playoff_times: Optional[Sequence[TimeLike]] = None,
        with_referees=True,
        with_scoreboard=True,
        num_candidates=5,
        rng_seed=None,
    ) -> "Tournament":
        teams = get_teams(teams)
        round_robin = cls.schedule_round_robin(
            teams,
            times,
            with_referees=with_referees,
            with_scoreboard=with_scoreboard,
            num_candidates=num_candidates,
            rng_seed=rng_seed,
        )
        if playoff_teams is None:
            playoff_teams = _highest_pow2(len(teams))
        round_robin_winners = [f"Ranked {i + 1}" for i in range(playoff_teams)]
        if playoff_times is None:
            playoff_times = times[len(round_robin):]
        elimination = cls.schedule_elimination(
            round_robin_winners,
            playoff_times,
            with_referees=with_referees,
            with_scoreboard=with_scoreboard,
            game_number_start=(len(round_robin) + 1),
            rng_seed=rng_seed,
        )
        return cls(round_robin.games + elimination.games)

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame([game._asdict() for game in self.games])
        return df.dropna(axis=1, how="all")

    def summary(self) -> pd.DataFrame:
        summary = {team: {"games": 0, "referees": 0, "scoreboards": 0} for team in self.teams}
        for game in self:
            summary[game.match.home]["games"] += 1
            summary[game.match.away]["games"] += 1
            if game.referee:
                summary[game.referee]["referees"] += 1
            if game.scoreboard:
                summary[game.referee]["scoreboards"] += 1
        return pd.DataFrame.from_dict(summary, orient="index")

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


def _highest_pow2(x) -> int:
    return 2 ** int(floor(log2(x)))
