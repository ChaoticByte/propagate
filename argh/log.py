# Copyright (c) 2025 Julian Müller (ChaoticByte)

from datetime import datetime

_loglevels = [
    "ERROR",
    "WARN ",
    "INFO ",
]

def log(*args, level: int = 2):
    level = min(len(_loglevels)-1, max(0, level))
    print(datetime.now().isoformat(), _loglevels[level], *args)
