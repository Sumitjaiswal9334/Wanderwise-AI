"""Persistent LangGraph checkpoint storage."""
import os
import sqlite3
from pathlib import Path
from threading import Lock

_connection = None
_checkpointer = None
_lock = Lock()


def get_checkpointer():
    """Return a process-wide SQLite checkpointer with a persistent connection."""
    global _connection, _checkpointer
    with _lock:
        if _checkpointer is not None:
            return _checkpointer
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
        except ImportError as exc:
            raise RuntimeError(
                "SQLite memory dependency missing. Install langgraph-checkpoint-sqlite."
            ) from exc
        db_path = Path(os.getenv("TRAVEL_MEMORY_DB", "travel_memory.sqlite3"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(db_path), check_same_thread=False)
        _checkpointer = SqliteSaver(_connection)
        _checkpointer.setup()
        return _checkpointer
