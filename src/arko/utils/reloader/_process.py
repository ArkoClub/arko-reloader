import multiprocessing
from logging import getLogger
from multiprocessing import Queue, Value, Lock
from typing import Callable, Generic, Optional, TYPE_CHECKING, TypeVar

import psutil
from typing_extensions import ParamSpec

from arko.utils.reloader._const import HANDLED_SIGNALS, HANDLED_SIGNALS_MAP

if TYPE_CHECKING:
    from psutil import Process as PsutilProcess

    # noinspection PyProtectedMember
    from multiprocessing.context import SpawnContext, SpawnProcess

__all__ = ("Process",)

multiprocessing.allow_connection_pickling()
spawn_context: "SpawnContext" = multiprocessing.get_context("spawn")

R = TypeVar("R")
P = ParamSpec("P")
logger = getLogger("arko.tools.reloader")


class Target(Generic[P, R]):
    _target: Callable[P, R]
    _result: Queue

    def _signal_handler(self, s: int, *_) -> None:
        """信号处理"""
        logger.debug(f"Target{self._target}接收到了信号: {HANDLED_SIGNALS_MAP.get(s, s)}")

    def __init__(self, target: Callable[P, R]) -> None:
        self._target = target
        self._result = Queue()

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        import signal
        import inspect

        for sig in HANDLED_SIGNALS:
            signal.signal(sig, self._signal_handler)

        if inspect.iscoroutinefunction(self._target):
            import asyncio

            self._result.put(asyncio.run(self._target(*args, **kwargs)))
        else:
            self._result.put(self._target(*args, **kwargs))
        return self._result

    @property
    def result(self) -> R:
        return self._result.get()


class Process(Generic[P, R]):
    _lock: Lock = Lock()
    _target: Target[P, R]

    _running: Value = Value("i", False)
    _paused: Value = Value("i", False)

    _process: Optional["SpawnProcess"] = None
    _p_process: Optional["PsutilProcess"] = None

    def __init__(
        self, target: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> None:
        self._target = Target(target)
        self._args = args
        self._kwargs = kwargs

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} of {hex(id(self))}>"

    def is_alive(self) -> bool:
        return self._process is not None and self._process.is_alive()

    def startup(self) -> None:
        """启动"""
        with self._lock:
            logger.debug(f"{self} 正在启动")
            
            self._process = spawn_context.Process(target=self._target)
            self._process.start()
            self._p_process = psutil.Process(self._process.pid)
            self._running.value = True
            
            logger.debug(f"{self} 启动完成")

    def stop(self) -> None:
        """停止"""
        with self._lock:
            logger.debug(f"{self} 正在停止")
            try:
                self._p_process.terminate()
                self._p_process.wait(5)
            except (psutil.NoSuchProcess, KeyboardInterrupt):
                pass
            except psutil.TimeoutExpired:
                try:
                    self._p_process.kill()
                except psutil.NoSuchProcess:
                    pass
            self._running.value = False
            logger.debug(f"{self} 已停止")

    def pause(self) -> None:
        with self._lock:
            self._paused.value = True
            self._p_process.suspend()
            logger.debug(f"{self} 已暂停")

    def resume(self) -> None:
        with self._lock:
            self._paused.value = False
            self._p_process.resume()
            logger.debug(f"{self} 已恢复")

    def reload(self, *, safely: bool = True) -> None:
        with self._lock:
            self._paused.value = True
            logger.debug(f"正在重载 {self}")
            if safely:
                self._p_process.suspend()
                logger.debug(f"{self} 已暂停")
            else:
                self._p_process.kill()

            try:
                process = spawn_context.Process(target=self._target)
                process.start()
            except Exception as e:
                logger.exception(e)
                logger.error(f"{self} 重启失败")
                if safely:
                    self._p_process.resume()
                    logger.info(f"{self} 原进程已恢复")
            else:
                self._process = process
                self._p_process.kill()
                self._p_process = psutil.Process(self._process.pid)
                logger.debug(f"{self} 重启成功")
            self._paused.value = False

    def result(self) -> P:
        return self._target.result

    @property
    def pid(self) -> int:
        return self._process.pid

    @property
    def is_running(self) -> bool:
        return bool(self._running.value)

    @property
    def is_paused(self) -> bool:
        return bool(self._paused.value)
