from fastapi import FastAPI, HTTPException,Depends
import requests
from sqlmodel import Field,Session,SQLModel,create_engine,select,Relationship
from typing import Annotated,Optional,List

sqllite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqllite_file_name}"

connect_args = {"check_same_thread":False}
engine = create_engine(sqlite_url,connect_args=connect_args)

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    rating: Optional[int] = None
    profile_url: Optional[str] = None

    games_as_white: List["Game"] = Relationship(back_populates="white", sa_relationship_kwargs={"foreign_keys": "[Game.white_id]"})
    games_as_black: List["Game"] = Relationship(back_populates="black", sa_relationship_kwargs={"foreign_keys": "[Game.black_id]"})
    
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

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session,Depends(get_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get('/user/{username}/{year}/{month}')
def get_user(username: str, year: int, month: int, session: SessionDep):
    username = username.lower()

    # 1. Fetch or create Player
    player = session.exec(select(Player).where(Player.username == username)).first()
    if not player:
        profile_url = f"https://api.chess.com/pub/player/{username}"
        headers = {"User-Agent": "my-fastapi-app/0.1 (https://github.com/parthadokar)"}
        profile_resp = requests.get(profile_url, headers=headers)
        if profile_resp.status_code != 200:
            raise HTTPException(status_code=profile_resp.status_code, detail=profile_resp.text)
        profile_data = profile_resp.json()

        player = Player(
            username=username,
            rating=profile_data.get("chess_blitz", {}).get("last", {}).get("rating"),
            profile_url=profile_data.get("url")
        )
        session.add(player)
        session.commit()
        session.refresh(player)

    # 2. Fetch games
    games_url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}"
    headers = {"User-Agent": "my-fastapi-app/0.1 (https://github.com/parthadokar)"}
    games_resp = requests.get(games_url, headers=headers)
    if games_resp.status_code != 200:
        raise HTTPException(status_code=games_resp.status_code, detail=games_resp.text)

    games_data = games_resp.json().get("games", [])

    # 3. Store games
    saved_games = []
    for g in games_data:
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
            termination=g.get("end_time"),  # careful: chess.com does not always have "termination"
            start_time=g.get("start_time"),
            end_time=g.get("end_time"),
            white_result=g.get("white", {}).get("result"),
            black_result=g.get("black", {}).get("result")
        )
        session.add(game)
        saved_games.append(game)

    session.commit()

    return {
        "player": player,
        "games_saved": len(saved_games)
    }

