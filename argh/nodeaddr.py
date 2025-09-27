# Copyright (c) 2025 Julian Müller (ChaoticByte)

class NodeAddr:

    def __init__(self, host: str, port: int):
        self.host = str(host)
        self.port = int(port)

    def ws_uri(self) -> str:
        return f"ws://{self.host}:{self.port}"

    def identifier(self) -> str:
        return f"{self.host}_{self.port}"
