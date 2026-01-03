from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from collections import defaultdict
import requests
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CLK_RE = re.compile(r"\[%clk (\d+:\d+:\d+)\]")

def hms_to_seconds(hms: str) -> int:
    h, m, s = map(int, hms.split(":"))
    return h * 3600 + m * 60 + s

def fetch_games(username: str, year: int, month: int):
    resp = requests.get(
        f"https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}",
        headers={"User-Agent": "fastapi-app"},
    )
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json().get("games", [])

def fetch_stats(username: str):
    resp = requests.get(
        f"https://api.chess.com/pub/player/{username}/stats",
        headers={"User-Agent": "fastapi-app"},
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Stats fetch failed")
    return resp.json()

def avg_move_time(games):
    total_time = 0
    total_moves = 0

    for g in games:
        pgn = g.get("pgn")
        if not pgn or "[%clk" not in pgn:
            continue

        clocks = CLK_RE.findall(pgn)
        if len(clocks) < 2:
            continue

        times = [hms_to_seconds(c) for c in clocks]
        for i in range(len(times) - 1):
            total_time += abs(times[i] - times[i + 1])
            total_moves += 1

    return round(total_time / total_moves, 2) if total_moves else None

@app.get("/analytics/{username}/{year}/{month}/summary")
def analytics_summary(username: str, year: int, month: int):
    username = username.lower()
    games = fetch_games(username, year, month)
    stats = fetch_stats(username)

    wins = 0
    losses = 0
    openings = defaultdict(lambda: {"games": 0, "wins": 0})

    for g in games:
        eco_url = g.get("eco_url")
        eco_code = g.get("eco")

        if eco_url and "/openings/" in eco_url:
            opening = eco_url.split("/openings/")[-1].replace("-", " ")
        elif eco_code:
            opening = f"ECO {eco_code}"
        else:
            continue

        openings[opening]["games"] += 1

        if g["white"]["username"].lower() == username:
            if g["white"]["result"] == "win":
                wins += 1
                openings[opening]["wins"] += 1
            elif g["white"]["result"] in ["resigned", "checkmated"]:
                losses += 1

        elif g["black"]["username"].lower() == username:
            if g["black"]["result"] == "win":
                wins += 1
                openings[opening]["wins"] += 1
            elif g["black"]["result"] in ["resigned", "checkmated"]:
                losses += 1

    ranked = sorted(openings.items(), key=lambda x: x[1]["games"], reverse=True)[:3]

    top_openings = [
        {
            "opening": name,
            "games": data["games"],
            "win_rate": round((data["wins"] / data["games"]) * 100, 2),
        }
        for name, data in ranked
    ]

    latest = {}
    for key in ["chess_blitz", "chess_bullet", "chess_rapid"]:
        mode = stats.get(key)
        if mode and mode.get("last"):
            latest[key.replace("chess_", "")] = mode["last"]["rating"]

    return {
        "username": username,
        "games": len(games),
        "wins": wins,
        "losses": losses,
        "avg_move_time": avg_move_time(games),
        "latest_ratings": latest,
        "top_openings": top_openings,
    }
