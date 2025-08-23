from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship, func
from sqlalchemy import case
from typing import Optional, Annotated
import requests

# ----------------- Database Setup -----------------
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


# ----------------- Models -----------------
class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    rating: Optional[int] = None
    profile_url: Optional[str] = None

    games_as_white: list["Game"] = Relationship(back_populates="white", sa_relationship_kwargs={"foreign_keys": "[Game.white_id]"})
    games_as_black: list["Game"] = Relationship(back_populates="black", sa_relationship_kwargs={"foreign_keys": "[Game.black_id]"})


class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: Optional[str] = None
    pgn: Optional[str] = None
    eco_code: Optional[str] = None
    eco_url: Optional[str] = None
    initial_setup: Optional[str] = None
    fen: Optional[str] = None
    time_control: Optional[str] = None
    time_class: Optional[str] = None
    rules: Optional[str] = None
    rated: Optional[bool] = None
    termination: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    white_result: Optional[str] = None
    black_result: Optional[str] = None

    white_id: Optional[int] = Field(default=None, foreign_key="player.id")
    black_id: Optional[int] = Field(default=None, foreign_key="player.id")

    white: Optional[Player] = Relationship(back_populates="games_as_white", sa_relationship_kwargs={"foreign_keys": "[Game.white_id]"})
    black: Optional[Player] = Relationship(back_populates="games_as_black", sa_relationship_kwargs={"foreign_keys": "[Game.black_id]"})


# ----------------- DB Utilities -----------------
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


# ----------------- FastAPI -----------------
app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# ----------------- Routes -----------------
@app.get("/user/{username}/{year}/{month}")
def get_user(username: str, year: int, month: int, session: SessionDep):
    username = username.lower()

    # Check if player already exists
    player = session.exec(select(Player).where(Player.username == username)).first()
    if not player:
        # Fetch profile (just to populate basic info)
        profile_url = f"https://api.chess.com/pub/player/{username}"
        resp = requests.get(profile_url, headers={"User-Agent": "my-fastapi-app/0.1"})
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        pdata = resp.json()
        player = Player(
            username=username,
            rating=pdata.get("chess_blitz", {}).get("last", {}).get("rating"),
            profile_url=pdata.get("url"),
        )
        session.add(player)
        session.commit()
        session.refresh(player)

    # Fetch games for that month
    games_url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}"
    games_resp = requests.get(games_url, headers={"User-Agent": "my-fastapi-app/0.1"})
    if games_resp.status_code != 200:
        raise HTTPException(status_code=games_resp.status_code, detail=games_resp.text)

    games_data = games_resp.json().get("games", [])

    for g in games_data:
        white_username = g["white"]["username"].lower()
        black_username = g["black"]["username"].lower()

        # Ensure both players exist in DB
        white = session.exec(select(Player).where(Player.username == white_username)).first()
        if not white:
            white = Player(username=white_username)
            session.add(white)
            session.commit()
            session.refresh(white)

        black = session.exec(select(Player).where(Player.username == black_username)).first()
        if not black:
            black = Player(username=black_username)
            session.add(black)
            session.commit()
            session.refresh(black)

        # Save game if not already saved
        existing = session.exec(select(Game).where(Game.url == g["url"])).first()
        if not existing:
            game = Game(
                url=g.get("url"),
                pgn=g.get("pgn"),
                eco_code=g.get("eco"),
                eco_url=g.get("eco_url"),
                initial_setup=g.get("initial_setup"),
                fen=g.get("fen"),
                time_control=g.get("time_control"),
                time_class=g.get("time_class"),
                rules=g.get("rules"),
                rated=g.get("rated"),
                termination=g.get("end_time"),
                start_time=g.get("start_time"),
                end_time=g.get("end_time"),
                white_result=g["white"].get("result"),
                black_result=g["black"].get("result"),
                white_id=white.id,
                black_id=black.id,
            )
            session.add(game)
        # Fetch ratings 
        ratings_url = f"https://api.chess.com/pub/player/{username}/stats"
        ratings_resp = requests.get(ratings_url,headers={"User-Agent": "my-fastapi-app/0.1"})
        if ratings_resp.status_code != 200:
            raise HTTPException(status_code=ratings_resp.status_code,detail=ratings_resp.text)
        
        rating_data = ratings_resp.json()
        # Create db for this and then start analytics
    session.commit()

    return {"player": player, "games_saved": len(games_data)}


# ----------------- Analytics -----------------

@app.get("/analytics/{username}")
def analytics(username: str, session: SessionDep):
    username = username.lower()
    player = session.exec(select(Player).where(Player.username == username)).first()
    if not player:
        raise HTTPException(status_code=404,detail="Player not found")
    return {"id":player.id,"username":player.username,"rating":player.rating}