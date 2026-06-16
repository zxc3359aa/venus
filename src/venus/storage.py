from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VenusPaths:
    root: Path
    env_prefix: str = "VENUS_"

    @property
    def data_dir(self) -> Path:
        return self.root / "data" / "venus"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs" / "venus"


class JsonStore:
    def __init__(self, root: Path | str):
        self.paths = VenusPaths(Path(root))
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)

    def read_collection(self, name: str) -> list[dict[str, Any]]:
        self._validate_collection_name(name)
        path = self._collection_path(name)
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def write_collection(self, name: str, records: list[dict[str, Any]]) -> None:
        self._validate_collection_name(name)
        path = self._collection_path(name)
        path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def append_record(self, name: str, record: dict[str, Any]) -> None:
        records = self.read_collection(name)
        records.append(record)
        self.write_collection(name, records)

    def _collection_path(self, name: str) -> Path:
        return self.paths.data_dir / f"{name}.json"

    def _validate_collection_name(self, name: str) -> None:
        lowered = name.lower()
        if "xiaolongxia" in lowered or "小龙虾" in name:
            raise ValueError("Venus storage must not read or write Xiaolongxia collections")
        if not name.replace("_", "").isalnum():
            raise ValueError(f"Invalid Venus collection name: {name}")
