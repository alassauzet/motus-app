from datetime import date

import pandas as pd
from filelock import FileLock

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


def get_player_attempts(username, target_date=None):
    """Renvoie le nombre d'essais du joueur pour la date donnée (par défaut aujourd'hui)"""
    if target_date is None:
        target_date = pd.to_datetime(date.today())
    df = load_scores()
    mask = (df.username == username) & (df['date'].dt.date == target_date)
    if mask.any():
        return int(df.loc[mask, "attempts"].iloc[0])
    return None


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


def daily_progress_all(year, month):
    df = load_scores()  # suppose que df a les colonnes : username, date, points
    if df.empty:
        return pd.DataFrame()

    # Filtrer sur le mois et l'année
    df = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]
    if df.empty:
        return pd.DataFrame()

    # Grouper par utilisateur et par date, sommer les points par jour
    daily = df.groupby(['username', 'date'])['points'].sum().sort_index()

    # Transformer en DataFrame où chaque colonne est un utilisateur
    daily_df = daily.reset_index().pivot(index='date', columns='username', values='points').fillna(0)

    # Faire le cumsum pour chaque utilisateur
    daily_df = daily_df.cumsum()

    return daily_df
