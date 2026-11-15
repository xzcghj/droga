from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from sqlmodel import Session

from app.container import Container


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session
