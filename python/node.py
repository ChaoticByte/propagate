#!/usr/bin/env python3

# Copyright (c) 2025 Julian Müller (ChaoticByte)

import asyncio
import signal

from argparse import ArgumentParser
from pathlib import Path

from propagate.log import log
from propagate.node import node_from_yml


if __name__ == "__main__":

    argp = ArgumentParser()
    argp.add_argument("config", type=Path, help="Path to the config yaml file")
    args = argp.parse_args()

    node = node_from_yml(args.config.read_text())

    def _sigint(*args):
        # don't need special sigint behaviour
        # -> send SIGTERM
        signal.raise_signal(signal.SIGTERM)
    signal.signal(signal.SIGINT, _sigint)

    asyncio.run(node.run())
    log("Bye")
