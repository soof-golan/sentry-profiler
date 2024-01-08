import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi.responses import ORJSONResponse
from fastapi import Depends, FastAPI, Request
import httpx

import sentry_sdk


sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    limit = httpx.Limits(
        max_keepalive_connections=100,
        max_connections=100,
    )
    async with httpx.AsyncClient(
        base_url="https://soofgolan.com/",
        timeout=None,
        limits=limit,
    ) as client:
        yield {
            "client": client,
        }


def client(request: Request) -> httpx.AsyncClient:
    return request.state.client


app = FastAPI(lifespan=lifespan)


def compute():
    logger.info("Starting heavy computation")
    l = list(range(10**5))
    bla = [x**2 for x in l]
    result = sum(bla)
    logger.info("Computed sum of %d squares", len(bla))
    # logger.info("squares: %s", bla)  # Good luck
    return {
        "result": result,
        "squares": bla,
    }


@app.get("/", response_class=ORJSONResponse)
async def root(client: Annotated[httpx.AsyncClient, Depends(client)]):
    r = await client.get("/", timeout=10)
    return ORJSONResponse({"data": compute(), "soofgolan": r.text})
