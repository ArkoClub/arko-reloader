import os
import sys
from enum import IntEnum
from pathlib import Path
from typing import Union

__all__ = (
    "StrOrPath", "PROJECT_ROOT", "SIGNAL", "HANDLED_SIGNALS", "HANDLED_SIGNALS_MAP",)

StrOrPath = Union[str, Path]

PROJECT_ROOT = Path(os.getcwd()).resolve()


class SIGNAL(IntEnum):
    STARTUP = 0
    PAUSE = 1
    RESUME = 2
    RELOAD = 3
    STOP = 4


if sys.platform == "win32":
    from signal import (
        SIGABRT,
        SIGBREAK,
        SIGINT,
        SIGTERM,
        CTRL_C_EVENT,
    )

    HANDLED_SIGNALS = (
        SIGINT,  # 来自键盘的中断 (CTRL + C)
        SIGTERM,  # 终结信号
        SIGABRT,  # 来自 abort(3) 的中止信号
        SIGBREAK,  # 来自键盘的中断 (CTRL + BREAK) Windows
    )
    HANDLED_SIGNALS_MAP = {
        SIGINT: "SIGINT",
        SIGTERM: "SIGTERM",
        SIGABRT: "SIGABRT",
        SIGBREAK: "SIGBREAK",
    }
else:
    from signal import SIGABRT, SIGINT, SIGTERM, SIGKILL, CTRL_C_EVENT, CTRL_BREAK_EVENT

    HANDLED_SIGNALS = (
        SIGINT,  # 来自键盘的中断 (CTRL + C)
        SIGTERM,  # 终结信号
        SIGABRT,  # 来自 abort(3) 的中止信号
        SIGKILL,
        CTRL_C_EVENT,
        CTRL_BREAK_EVENT,
    )
    HANDLED_SIGNALS_MAP = {
        SIGINT: "SIGINT",
        SIGTERM: "SIGTERM",
        SIGABRT: "SIGABRT",
        SIGKILL: "SIGKILL",
        CTRL_C_EVENT: "CTRL_C_EVENT",
        CTRL_BREAK_EVENT: "CTRL_BREAK_EVENT",
    }
