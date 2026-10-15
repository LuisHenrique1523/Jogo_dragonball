from __future__ import annotations

import json
from pathlib import Path

from . import settings as cfg


class HighScore:
    def __init__(self, path: Path = cfg.SAVE_FILE):
        self.path = path
        self.best = self._load()

    def _load(self) -> int:
        try:
            return int(json.loads(self.path.read_text(encoding="utf-8")).get("best", 0))
        except (OSError, ValueError, TypeError, AttributeError):
            return 0

    def submit(self, score: int) -> bool:
        if score <= self.best:
            return False
        self.best = score
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"best": score}), encoding="utf-8")
        except OSError:
            pass
        return True
