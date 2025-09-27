#!/usr/bin/env python3

import asyncio

from argparse import ArgumentParser

from websockets.asyncio.client import connect


async def run(host: str, port: int):
    async with connect(f"ws://{host}:{port}") as ws:
        async for msg in ws:
            print(msg)


if __name__ == "__main__":

    argp = ArgumentParser()
    argp.add_argument("host", type=str, help="Node host to connect to")
    argp.add_argument("port", type=int, help="Node port to connect to")
    args = argp.parse_args()

    asyncio.run(run(args.host, args.port))
