import os
from typing import List, Optional, Sequence

import click
import pandas as pd
from flask import Flask, request, url_for

from tourney.time_utils import get_available_times, TimeWindow
from tourney.tournament import Tournament

app = Flask(__name__)


@app.route("/")
def root():
    scheduler_url = url_for("schedule")
    return f"Tournament scheduler. To use, please visit {scheduler_url}"


@app.route("/schedule", methods=["POST"])
def schedule() -> str:
    teams = int(request.form["teams"])
    windows = _get_time_windows(request.form["times"])
    minutes = int(request.form["minutes"])
    times = get_available_times(windows, minutes)
    tournament = Tournament.schedule_round_robin_with_playoffs(teams, times)
    tournament_df = tournament.to_dataframe()
    window_dfs = _split_into_windows(tournament_df, windows)
    tournament_html = ""
    for df in window_dfs:
        tournament_html += df.to_html(index=False)
        tournament_html += "<br><br>"
    tournament_html += tournament.summary().to_html(index=True)
    tournament_html += "<br><br>"
    return tournament_html


def _get_window_from_str(window_str: str, sep=None) -> Optional[TimeWindow]:
    window_str = window_str.strip()
    if not window_str:
        return None

    if sep is None:
        sep = [",", "-", " "]
    elif isinstance(sep, str):
        sep = [sep]

    for char in sep:
        times = [t.strip() for t in window_str.split(char)]
        times = [t for t in times if t]
        if len(times) == 2:
            break
    if len(times) != 2:
        raise ValueError("Two times, start and end, must be provided")
    start, end = times
    return TimeWindow(start, end)


def _get_time_windows(times_text: str) -> List[TimeWindow]:
    return [w for w in map(_get_window_from_str, times_text.split("\n")) if w]


def _split_into_windows(tournament_df: pd.DataFrame, windows: Sequence[TimeWindow]) -> List[pd.DataFrame]:
    splits = []
    window_iter = iter(windows)
    game_iter = iter(tournament_df.iterrows())
    current_window = next(window_iter, None)
    current_game = next(game_iter, (None, None))[1]
    current_split = []
    while current_window is not None and current_game is not None:
        if current_game["time"] in current_window:
            current_split.append(current_game)
            current_game = next(game_iter, (None, None))[1]
        else:
            if current_split:
                splits.append(pd.DataFrame(current_split))
            current_split = []
            current_window = next(window_iter)
    if current_split:
        splits.append(pd.DataFrame(current_split))
    return splits


@click.command()
@click.option('--open/--no-open', 'open_page', default=True, help='Automatically open scheduling page in browser.')
def run(open_page: bool):
    if open_page:
        os.system("open src/schedule.html")  # Comment this out to turn off automatic opening of scheduling web form
    app.run(debug=True)
