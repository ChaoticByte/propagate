#!/usr/bin/env python3

# Copyright (c) 2025 Julian Müller (ChaoticByte)

import asyncio

from argparse import ArgumentParser
from pathlib import Path

from argh.node import node_from_yml


if __name__ == "__main__":

    argp = ArgumentParser()
    argp.add_argument("config", type=Path, help="Path to the config yaml file")
    args = argp.parse_args()

    node = node_from_yml(args.config.read_text())

    asyncio.run(node.run())
