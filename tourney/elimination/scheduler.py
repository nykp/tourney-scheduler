from random import seed as set_seed, shuffle
from typing import List, Optional, Sequence, Tuple, Union

from ..match import Match, MatchSeries, Team
from ..match_utils import get_teams, TeamsOrNumber


def _get_idx(idx: int):
    def get(tup):
        return tup[idx]
    return get



def _split_brackets(teams_increasing_rank: Sequence[Team]) -> Tuple[List[Team], List[Team]]:
    if len(teams_increasing_rank) % 2:
        raise ValueError("Odd number of teams, cannot split into two brackets")
    teams_with_idx = list(enumerate(teams_increasing_rank))
    half_idx = len(teams_with_idx) // 2
    bottom_half = teams_with_idx[:half_idx]
    top_half = teams_with_idx[half_idx:]
    paired = list(zip(top_half[::-1], bottom_half))
    unpaired = [t for pair in paired for t in pair]
    left = unpaired[:half_idx]
    right = unpaired[half_idx:]
    left_ranked = list(map(_get_idx(1), sorted(left, key=_get_idx(0))))
    right_ranked = list(map(_get_idx(1), sorted(right, key=_get_idx(0))))
    return left_ranked, right_ranked


def _get_bracket_matches(
    teams_increasing_rank: Sequence[Team],
    game_number_start=1
) -> Tuple[MatchSeries, List[Team], int]:
    match_count = len(teams_increasing_rank) // 2
    match_teams = list(teams_increasing_rank[:(match_count * 2)])
    bye_teams = list(teams_increasing_rank[(match_count * 2):])
    matches = []
    for i in range(match_count):
        home = match_teams.pop(-1)
        away = match_teams.pop(0)
        matches.append(Match(home, away, id=(game_number_start + i)))
    return MatchSeries(matches), bye_teams, game_number_start + len(matches)


def get_seeded_schedule(
    teams: TeamsOrNumber,
    ranks: Optional[Union[Sequence[int], str]] = None,
    game_number_start=1,
    rng_seed=None,
) -> MatchSeries:

    teams = get_teams(teams)
    if len(teams) % 2:
        raise NotImplementedError("Seeded schedule currently only implemented for even numbers of teams")

    if ranks is None:
        ranks = list(range(1, len(teams) + 1))
    elif isinstance(ranks, str):
        if ranks in ("random", "shuffle"):
            if rng_seed is not None:
                set_seed(rng_seed)
            ranks = list(range(1, len(teams) + 1))
            shuffle(ranks)
        else:
            raise ValueError(f"Unrecognized rank specification: {ranks}")
        
    elif len(ranks) != len(teams):
        raise ValueError("Number of ranks does not match the number of teams")

    teams_increasing_rank = list(map(_get_idx(0), sorted(zip(teams, ranks), key=_get_idx(1), reverse=True)))
    left_teams, right_teams = _split_brackets(teams_increasing_rank)
    game_number = game_number_start
    all_matches = MatchSeries([])

    while len(left_teams) > 1:
        assert len(left_teams) == len(right_teams)

        # Get bracket matches
        left_matches, left_byes, game_number = _get_bracket_matches(left_teams, game_number)
        right_matches, right_byes, game_number = _get_bracket_matches(right_teams, game_number)
        all_matches += (left_matches + right_matches)

        # Get bracket winners
        left_winners = [f"Game {m.id} winner" for m in left_matches]
        left_teams = left_winners + left_byes

        right_winners = [f"Game {m.id} winner" for m in right_matches]
        right_teams = right_winners + right_byes

    # Final match
    final_match = Match(left_teams[0], right_teams[0], game_number)
    return all_matches + final_match
