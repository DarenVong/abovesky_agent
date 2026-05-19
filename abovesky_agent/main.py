from contextlib import asynccontextmanager

from fastapi import FastAPI

from .chat import router as chat_router
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="abovesky", lifespan=lifespan)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}
