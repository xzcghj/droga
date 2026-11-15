from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, event
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine


def make_engine(url: str) -> Engine:
    kwargs: dict = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool
        else:
            db_path = url.removeprefix("sqlite:///")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _record) -> None:
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return engine


def init_db(engine: Engine) -> None:
    from app.db import models  # noqa: F401  (rejestracja tabel)

    SQLModel.metadata.create_all(engine)
