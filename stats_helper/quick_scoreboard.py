import collections
import json
import os
from threading import RLock
from typing import Dict, Optional, List

from stats_helper import constants

Scoreboard = collections.namedtuple('Scoreboard', 'alias cls target title')


class QuickScoreboards:
    def __init__(self, path: str) -> None:
        self.path = path
        self.saved = {}  # type: Dict[str, Scoreboard]
        self.lock = RLock()

    def append(self, scoreboard: Scoreboard) -> bool:
        ret = self.__append(scoreboard)
        self.save()
        return ret

    def __append(self, scoreboard: Scoreboard) -> bool:
        with self.lock:
            existed = self.get(scoreboard.alias)
            if not existed:
                self.saved[scoreboard.alias] = scoreboard
                return True
            else:
                return False

    def remove(self, alias):
        ret = self.__remove(alias)
        self.save()
        return ret

    def __remove(self, alias):
        with self.lock:
            existed = self.get(alias)
            if not existed:
                return False
            else:
                self.saved.pop(alias)
                return True

    def load(self, logger=None):
        def error_log(content): return (
            logger.error if logger is not None else print)(content)
        with self.lock:
            if not os.path.isdir(os.path.dirname(self.path)):
                os.makedirs(os.path.dirname(self.path))
            self.saved.clear()
            need_save = False
            if not os.path.isfile(self.path):
                need_save = True
            else:
                with open(self.path, 'r', encoding='UTF-8') as f:
                    try:
                        for key, value in json.load(f).items():
                            self.__append(Scoreboard(
                                key, value['cls'], value['target'], value['title']))
                    except Exception as e:
                        error_log(e)
                        need_save = True
            if need_save:
                self.save()

    def save(self):
        with self.lock:
            out = {}
            for key, value in self.saved.items():
                out[key] = {
                    'cls': value.cls,
                    'target': value.target,
                    'title': value.title
                }
            with open(self.path, 'w', encoding='UTF-8') as f:
                json.dump(out, f, indent=2, ensure_ascii=False)

    def get(self, name) -> Optional[Scoreboard]:
        with self.lock:
            return self.saved.get(name)

    def list_scoreboard(self) -> List[Scoreboard]:
        with self.lock:
            return list(self.saved.values())


quick_scoreboards = QuickScoreboards(constants.QuickScoreboardFile)
