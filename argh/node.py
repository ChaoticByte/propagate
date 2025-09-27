# Copyright (c) 2025 Julian Müller (ChaoticByte)

import asyncio
import signal

from hashlib import md5

from websockets.asyncio.client import connect
from websockets.asyncio.server import broadcast
from websockets.asyncio.server import serve
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed, ConnectionClosedError

from yaml import safe_load as yml_load

from .log import log
from .nodeaddr import NodeAddr


class Node:

    max_known_hashes_size = 1024 * 1024

    def __init__(self, listen_address: NodeAddr, relays: list[NodeAddr]):
        self.listen_address = listen_address
        self.relays = list(relays)
        for r in relays:
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

    async def _conn_to_relay(self, r: NodeAddr):
        identifier = r.identifier()
        log("Attempting to connect to relay", identifier)
        async for ws in connect(r.ws_uri()):
            log("Connected to relay", identifier)
            self._connections[identifier] = ws
            try:
                async for msg in ws:
                    self._relay(msg)
            except (ConnectionClosed, ConnectionClosedError):
                del self._connections[identifier]
                log(f"Lost connection to relay", identifier, level=1)
                continue

    async def _conn_from_node_or_client(self, ws: ServerConnection):
        host, port = ws.remote_address
        addr = NodeAddr(host, port)
        identifier = addr.identifier()
        self._connections[identifier] = ws
        log("Accepted connection", identifier)
        try:
            async for msg in ws:
                self._relay(msg)
        except:
            log("Lost connection", identifier)
        finally:
            del self._connections[identifier]

    async def run(self):
        # connect to relays
        relay_tasks = []
        for r in self.relays:
            t = asyncio.create_task(self._conn_to_relay(r))
            relay_tasks.append(t)
        # server loop
        async with serve(self._conn_from_node_or_client, self.listen_address.host, self.listen_address.port) as server:
            loop = asyncio.get_running_loop()

            def _close():
                log("Cancelling relay connections")
                for r in relay_tasks:
                    r.cancel()
                log("Closing server...")
                server.close()

            loop.add_signal_handler(signal.SIGTERM, _close)
            await server.wait_closed()


def node_from_yml(yml_data: str) -> Node:
    d = yml_load(yml_data)
    listen_address = NodeAddr(d["listen"]["host"], d["listen"]["port"])
    relays = []
    for e in d["relays"]:
        relays.append(NodeAddr(e["host"], e["port"]))
    return Node(listen_address, relays)
