from datetime import date
import pandas as pd
from supabase import create_client
import os
from collections import Counter

# --- Supabase client ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]  # clé backend
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------
# Fonctions Scores
# ---------------------

def score_from_attempts(attempts):
    mapping = {1: 60, 2: 50, 3: 40, 4: 30, 5: 20, 6: 10}
    return mapping.get(attempts, 0)


def load_scores(year=None, month=None):
    """Charge tous les scores depuis Supabase, optionnellement filtrés par mois"""
    query = supabase.table("scores").select("*")
    if year and month:
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month:02d}-31"
        query = query.gte("date", start).lte("date", end)
    res = query.execute()
    if not res.data:
        return pd.DataFrame(columns=["date", "username", "attempts", "points"])
    df = pd.DataFrame(res.data)
    df['date'] = pd.to_datetime(df['date'])
    return df


def get_player_attempts(username, target_date=None):
    if target_date is None:
        target_date = pd.to_datetime(date.today())
    df = load_scores()
    mask = (df.username == username) & (df['date'].dt.date == target_date)
    if mask.any():
        return int(df.loc[mask, "attempts"].iloc[0])
    return 0


def monthly_games_played(target_date: date = None):
    if target_date is None:
        target_date = date.today()
    df = load_scores(target_date.year, target_date.month)
    if df.empty:
        return {}
    counts = df.groupby("username").size()
    return counts.to_dict()


def upsert_score(username, attempts):
    today = pd.to_datetime(date.today())
    points = score_from_attempts(attempts)

    # Vérifie si une ligne existe déjà
    existing = supabase.table("scores").select("*") \
        .eq("username", username).eq("date", today.isoformat()).execute()

    if existing.data:
        # update
        supabase.table("scores").update({
            "attempts": attempts,
            "points": points
        }).eq("username", username).eq("date", today.isoformat()).execute()
    else:
        # insert
        supabase.table("scores").insert({
            "date": today.isoformat(),
            "username": username,
            "attempts": attempts,
            "points": points
        }).execute()


def monthly_leaderboard(year, month):
    df = load_scores(year, month)
    if df.empty:
        return pd.Series(dtype=int)
    return df.groupby("username")["points"].sum().sort_values(ascending=False)


def daily_progress(username, year, month):
    df = load_scores(year, month)
    df = df[(df.username == username)]
    if df.empty:
        return pd.Series(dtype=int)
    daily = df.groupby('date')["points"].sum().sort_index().cumsum()
    return daily


def daily_progress_all(year, month):
    df = load_scores(year, month)
    if df.empty:
        return pd.DataFrame()
    daily = df.groupby(['username', 'date'])['points'].sum().sort_index()
    daily_df = daily.reset_index().pivot(index='date', columns='username', values='points').fillna(0)
    daily_df = daily_df.cumsum()
    return daily_df


def compute_user_trends(progress_df: pd.DataFrame):
    if progress_df.empty or len(progress_df) < 2:
        return {user: "same" for user in progress_df.columns}

    today_scores = progress_df.iloc[-1]
    yesterday_scores = progress_df.iloc[-2]

    today_ranking = today_scores.sort_values(ascending=False).index.tolist()
    yesterday_ranking = yesterday_scores.sort_values(ascending=False).index.tolist()

    today_positions = {user: i + 1 for i, user in enumerate(today_ranking)}
    yesterday_positions = {user: i + 1 for i, user in enumerate(yesterday_ranking)}

    user_trends = {}
    for user in today_positions:
        prev_pos = yesterday_positions.get(user)
        curr_pos = today_positions[user]
        if prev_pos is None:
            user_trends[user] = "new"
        elif curr_pos < prev_pos:
            user_trends[user] = "up"
        elif curr_pos > prev_pos:
            user_trends[user] = "down"
        else:
            user_trends[user] = "same"

    return user_trends
