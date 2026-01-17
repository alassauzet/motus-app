import pandas as pd
from pathlib import Path
from filelock import FileLock
from datetime import date, timedelta
from config import SCORES_FILE

LOCK = FileLock(str(SCORES_FILE) + ".lock")

def load_scores():
    if not SCORES_FILE.exists():
        return pd.DataFrame(columns=["date", "username", "attempts", "points"])
    return pd.read_csv(SCORES_FILE, parse_dates=["date"])

def score_from_attempts(attempts):
    mapping = {1: 10, 2: 8, 3: 6, 4: 4, 5: 2}
    return mapping.get(attempts, 0)

def upsert_score(username, attempts):
    today = pd.to_datetime(date.today())
    points = score_from_attempts(attempts)

    with LOCK:
        df = load_scores()
        mask = (df.username == username) & (df.date == today)

        if mask.any():
            df.loc[mask, ["attempts", "points"]] = [attempts, points]
        else:
            df = pd.concat([
                df,
                pd.DataFrame([{
                    "date": today,
                    "username": username,
                    "attempts": attempts,
                    "points": points
                }])
            ])
        df.to_csv(SCORES_FILE, index=False)

def monthly_leaderboard(year, month):
    df = load_scores()
    df = df[(df.date.dt.year == year) & (df.date.dt.month == month)]
    return df.groupby("username")["points"].sum().sort_values(ascending=False)

def daily_progress(username, year, month):
    df = load_scores()
    df = df[(df.username == username) &
            (df.date.dt.year == year) &
            (df.date.dt.month == month)]
    daily = df.groupby("date")["points"].sum().sort_index().cumsum()
    return daily
