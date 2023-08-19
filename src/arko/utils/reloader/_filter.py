import inspect
from functools import lru_cache
from logging import getLogger
from pathlib import Path
from typing import List, TYPE_CHECKING

from arko_reloader._const import PROJECT_ROOT, StrOrPath

if TYPE_CHECKING:
    from watchfiles import Change

__all__ = ("ReloadFileFilter",)

logger = getLogger('arko-reloader')


class ReloadFileFilter:
    _default_includes = ["*.py"]
    _default_excludes = [".*", ".py[cod]", ".sw.*", "~*", __file__]

    def __init__(
        self,
        reload_dirs: List[StrOrPath] = None,
        reload_includes: List[str] = None,
        reload_excludes: List[str] = None,
    ) -> None:
        _reload_dirs = []
        for reload_dir in reload_dirs or []:
            _reload_dirs.append(PROJECT_ROOT.joinpath(Path(reload_dir)))

        self.reload_dirs = []
        for reload_dir in _reload_dirs:
            append = True
            for parent in reload_dir.parents:
                if parent in _reload_dirs:
                    append = False
                    break
            if append:
                self.reload_dirs.append(reload_dir)

        if not self.reload_dirs:
            logger.warning(
                "The list of target folders that need to be detected is empty"
            )

        frame = inspect.currentframe().f_back.f_back
        includes = reload_includes or []
        excludes = (reload_excludes or []) + [frame.f_globals["__file__"]]

        self.includes = [
            include for include in self._default_includes if include not in excludes
        ]
        self.includes.extend(includes)
        self.includes = list(set(self.includes))

        self.excludes = [
            exclude for exclude in self._default_excludes if exclude not in includes
        ]
        self.exclude_dirs = []
        for exclude in excludes:
            path = Path(exclude)
            try:
                is_dir = path.is_dir()
            except OSError:
                is_dir = False

            if is_dir:
                self.exclude_dirs.append(path)
            else:
                self.excludes.append(exclude)
        self.excludes = list(set(self.excludes))

    @lru_cache()
    def __call__(self, change: "Change", path: str) -> bool:
        path = Path(path).resolve()
        for include_pattern in self.includes:
            if path.match(include_pattern):
                for exclude_dir in self.exclude_dirs:
                    if exclude_dir in path.parents:
                        return False

                for exclude_pattern in self.excludes:
                    if path.match(exclude_pattern):
                        return False

                return True
        return False
