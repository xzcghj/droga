from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_container
from app.container import Container

router = APIRouter(tags=["meta"])


class MetaRead(BaseModel):
    ai_enabled: bool
    ai_provider: str | None


@router.get("/meta", response_model=MetaRead)
def get_meta(container: Container = Depends(get_container)) -> MetaRead:
    return MetaRead(ai_enabled=container.llm is not None, ai_provider=container.ai_provider)
