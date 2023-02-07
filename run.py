from typing import List, Optional, Sequence

from flask import Flask, request, url_for

from tourney.time_utils import get_available_times, TimeWindow
from tourney.tournament import Tournament


app = Flask(__name__)


@app.route("/")
def root():
    scheduler_url = url_for("schedule")
    return f"Tournament scheduler. To use, please visit {scheduler_url}"


@app.route("/schedule", methods=["POST"])
def schedule():
    teams = int(request.form["teams"])
    windows = _get_time_windows(request.form["times"])
    minutes = int(request.form["minutes"])
    times = get_available_times(windows, minutes)
    tournament = Tournament.schedule_round_robin_with_playoffs(teams, times)
    tournament_df = tournament.to_dataframe()
    tournament_html = tournament_df.to_html(index=False)
    return tournament_html


def _get_window_from_str(window_str: str) -> Optional[TimeWindow]:
    window_str = window_str.strip()
    if not window_str:
        return None
    times = [t.strip() for t in window_str.split(",")]
    if len(times) != 2:
        raise ValueError("Two times, start and end, must be provided")
    start, end = times
    return TimeWindow(start, end)


def _get_time_windows(times_text: str) -> List[TimeWindow]:
    return [w for w in map(_get_window_from_str, times_text.split("\n")) if w]


if __name__ == "__main__":
    app.run(debug=True)
