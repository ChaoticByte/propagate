#!/usr/bin/env python3

# Copyright (c) 2025 Julian Müller (ChaoticByte)

import asyncio

from argparse import ArgumentParser

from websockets.asyncio.client import ClientConnection
from websockets.asyncio.client import connect


async def run(host: str, port: int):
    ws: ClientConnection
    async with connect(f"ws://{host}:{port}") as ws:
        while True:
            inp = input("> ")
            await (await ws.ping()) # check connection
            await ws.send(inp)


if __name__ == "__main__":

    argp = ArgumentParser()
    argp.add_argument("host", type=str, help="Node host to connect to")
    argp.add_argument("port", type=int, help="Node port to connect to")
    args = argp.parse_args()

    asyncio.run(run(args.host, args.port))
