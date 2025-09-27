#!/usr/bin/env python3

import asyncio

from argparse import ArgumentParser
from datetime import datetime
from hashlib import md5
from pathlib import Path

from websockets.asyncio.client import connect
from websockets.asyncio.server import broadcast
from websockets.asyncio.server import serve
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed, ConnectionClosedError

from yaml import safe_load as yml_load


def log(msg):
    print(f"{datetime.now().isoformat()} {msg}")


class NodeAddr:

    def __init__(self, host: str, port: int):
        self.host = str(host)
        self.port = int(port)

    def ws_uri(self) -> str:
        return f"ws://{self.host}:{self.port}"

    def identifier(self) -> str:
        return f"{self.host}_{self.port}"


class Node:

    max_known_hashes_size = 1024 * 1024

    def __init__(self, listen_address: NodeAddr, receivers: list[NodeAddr]):
        self.listen_address = listen_address
        self.receivers = list(receivers)
        for r in receivers:
            if not isinstance(r, NodeAddr):
                raise TypeError(f"{r} must be of type NodeAddr")
        # internal
        self._connections: dict = {} # identifer: connection object
        self._known_hashes: list[str] = [] # list of message hashes


    def _relay(self, msg: str):
        msg_hash = md5(msg.encode()).digest()
        if not msg_hash in self._known_hashes:
            self._known_hashes.append(msg_hash)
            broadcast(self._connections.values(), msg)
        while len(self._known_hashes) > self.max_known_hashes_size:
            self._known_hashes.pop(0)


    async def _receiver_connection(self, r: NodeAddr):
        identifier = r.identifier()
        async for ws in connect(r.ws_uri()):
            log(identifier)
            self._connections[identifier] = ws
            try:
                async for msg in ws:
                    log(msg)
                    self._relay(msg)
            except (ConnectionClosed, ConnectionClosedError):
                del self._connections[identifier]
                log(f"Connection from {identifier} closed")
                continue


    async def _server_connection(self, ws: ServerConnection):
        host, port = ws.remote_address
        addr = NodeAddr(host, port)
        identifier = addr.identifier()
        self._connections[identifier] = ws
        log(identifier)
        async for msg in ws:
            log(msg)
            self._relay(msg)
        del self._connections[identifier]


    async def run(self):
        # connect to receivers
        receiver_tasks = []
        for r in self.receivers:
            t = asyncio.create_task(self._receiver_connection(r))
            receiver_tasks.append(t)
        # server loop
        async with serve(self._server_connection, self.listen_address.host, self.listen_address.port) as server:
            await server.serve_forever()
        # wait for receivers
        await asyncio.gather(receiver_tasks)



def node_from_yml(yml_data: str) -> Node:
    d = yml_load(yml_data)
    listen_address = NodeAddr(d["listen"]["host"], d["listen"]["port"])
    receivers = []
    for e in d["receivers"]:
        receivers.append(NodeAddr(e["host"], e["port"]))
    return Node(listen_address, receivers)


if __name__ == "__main__":

    argp = ArgumentParser()
    argp.add_argument("config", type=Path, help="Path to the config yaml file")
    args = argp.parse_args()

    node = node_from_yml(args.config.read_text())

    asyncio.run(node.run())
