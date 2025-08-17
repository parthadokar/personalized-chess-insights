from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

@app.get('/user')
def get_user(username: str):
    url = f"https://lichess.org/api/games/user/{username}?max=5"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.text
