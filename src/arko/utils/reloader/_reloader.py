from logging import getLogger
from multiprocessing import Queue
from threading import Thread
from typing import ParamSpec, TypeVar

from arko.utils.reloader._const import SIGNAL
from arko.utils.reloader._process import Process

__all__ = ("Reloader", )


R = TypeVar("R")
P = ParamSpec("P")

logger = getLogger("arko.tools.reloader")


class Reloader(object):
    _process: Process
    _queue: Queue
    _task: Thread

    def __init__(
        self, process: Process, *, parent_process_queue: Queue = Queue()
    ) -> None:
        self._process = process
        self._queue = parent_process_queue

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} {hex(id(self))}>"

    @property
    def process(self) -> Process:
        return self._process

    def _task(self):
        while True:
            if self.process.is_paused:
                continue
            if self.process.is_alive() and self._queue.empty():
                continue
            if not self.process.is_alive() and self._queue.empty():
                logger.debug(f"{self.process} 运行结束")
                self.process.stop()
                break
            if self._queue.empty():
                continue

            self.process.__getattribute__(SIGNAL(self._queue.get()).name.lower())()

    def run(self, *, background: bool = False) -> None:
        self._task = Thread(target=self._task)
        self._queue.put(SIGNAL.STARTUP)
        self._task.start()

        if not background:
            self._task.join()


def test():
    import time

    time.sleep(1)
    print("OK")


def main():
    reloader = Reloader(Process(test))
    reloader.run(background=True)
    print(reloader)
    import time

    time.sleep(2)


if __name__ == "__main__":
    main()
