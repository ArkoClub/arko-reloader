from functools import partial
from logging import getLogger
from multiprocessing import Queue
from pathlib import Path
from threading import Event
from typing import Callable, Generator, Set, TYPE_CHECKING

from watchfiles import Change, DefaultFilter, watch
from watchfiles.main import FileChange

from arko.utils.reloader._const import PROJECT_ROOT, SIGNAL, StrOrPath
from arko.utils.reloader._process import Process
from arko.utils.reloader._reloader import Reloader

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from watchfiles.main import AbstractEvent

__all__ = (
    "FileWatcher",
    "FileReloader",
    "WatchFilterType",
)

logger = getLogger("arko.tools.reloader")

WatchFilterType = Callable[[Change, str], bool]


class FileWatcher:
    def __init__(
        self,
        *paths: StrOrPath,
        watch_filter: WatchFilterType | None = DefaultFilter(),
        debounce: int = 1_600,
        step: int = 50,
        timeout: int = 200,
        debug: bool = False,
        raise_interrupt: bool = True,
        force_polling: bool | None = None,
        poll_delay_ms: int = 300,
        recursive: bool = True,
    ):
        self._watcher = partial(
            watch,
            *paths,
            watch_filter=watch_filter,
            debounce=debounce,
            step=step,
            rust_timeout=timeout,
            yield_on_timeout=True,
            debug=debug,
            raise_interrupt=raise_interrupt,
            force_polling=force_polling,
            poll_delay_ms=poll_delay_ms,
            recursive=recursive,
        )

    def __call__(
        self, stop_event: "AbstractEvent"
    ) -> Generator[Set[FileChange], None, None]:
        return self._watcher(stop_event=stop_event)


class FileReloader(Reloader):
    _watcher: Generator[Set[FileChange], None, None]

    def __init__(
        self,
        process: Process,
        watcher: FileWatcher | None = None,
        *,
        watch_stop_event: "AbstractEvent" = Event(),
        parent_process_queue: Queue = Queue(),
    ):
        super().__init__(process, parent_process_queue=parent_process_queue)
        self._event = watch_stop_event
        self._watcher = (watcher or FileWatcher(PROJECT_ROOT))(self._event)

    def _task(self):
        for file_changes in self._watcher:
            for file_change in file_changes:
                change, str_path = file_change
                path = Path(str_path).resolve().relative_to(PROJECT_ROOT)

                logger.debug(f"检测到文件 {path} 被{['添加', '修改', '删除'][change]}, 正在重载")
                self.process.reload()
                break

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
