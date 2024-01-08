"""Dumb load test for the server."""
import asyncio
from typing import Iterable

import httpx
from typer import Typer
from tqdm import tqdm

app = Typer()


@app.command()
def main(
    url: str = "http://localhost:8080",
    endpoint: str = "/",
    requests: int = 1000,
    concurrency: int = 100,
    debug: bool = False,
):
    """Send a bunch of requests to the server."""

    async def one_request(client: httpx.AsyncClient, pb: tqdm):
        try:
            await client.get(url + endpoint)
        finally:
            pb.update()

    async def worker(client: httpx.AsyncClient, pb: tqdm, generator: Iterable[int]):
        for _ in generator:
            await one_request(client, pb)

    limit = httpx.Limits(
        max_keepalive_connections=concurrency,
        max_connections=concurrency,
    )

    async def load_test():
        async with httpx.AsyncClient(limits=limit, timeout=None) as client:
            with tqdm(total=requests, desc="Requests") as pb:
                workers = [
                    asyncio.create_task(worker(client, pb, range(requests // concurrency)))
                    for _ in range(concurrency)
                ]
                await asyncio.gather(*workers)

    asyncio.run(load_test())


if __name__ == "__main__":
    app()
