import pandas as pd
from pathlib import Path
from filelock import FileLock
from datetime import date
from config import SCORES_FILE

LOCK = FileLock(str(SCORES_FILE) + ".lock")

def load_scores():
    """Charge le CSV scores et convertit la colonne date en datetime"""
    if not SCORES_FILE.exists() or SCORES_FILE.stat().st_size == 0:
        return pd.DataFrame(columns=["date", "username", "attempts", "points"])
    
    df = pd.read_csv(SCORES_FILE)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df

def score_from_attempts(attempts):
    mapping = {1: 60, 2: 50, 3: 40, 4: 30, 5: 20, 6: 10}
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
            ], ignore_index=True)
        df.to_csv(SCORES_FILE, index=False)

def monthly_leaderboard(year, month):
    df = load_scores()
    if df.empty:
        return pd.Series(dtype=int)
    df = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]
    if df.empty:
        return pd.Series(dtype=int)
    return df.groupby("username")["points"].sum().sort_values(ascending=False)

def daily_progress(username, year, month):
    df = load_scores()
    if df.empty:
        return pd.Series(dtype=int)
    df = df[(df.username == username) &
            (df['date'].dt.year == year) &
            (df['date'].dt.month == month)]
    if df.empty:
        return pd.Series(dtype=int)
    daily = df.groupby("date")["points"].sum().sort_index().cumsum()
    return daily
