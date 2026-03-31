from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from src.core.auth import get_user_by_token
from src.core.specs import (
    list_specs, get_spec, create_spec, update_spec, delete_spec, set_spec_tags,
    list_tags, create_tag,
    list_developers, get_developer, create_developer, update_developer, delete_developer,
)

router = APIRouter(prefix="/api")


# --- Models ---

class SpecCreate(BaseModel):
    title: str
    content: str = ""
    priority: str = "medium"
    chat_session_id: str | None = None


class SpecUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to: int | None = None


class SpecMove(BaseModel):
    status: str


class SpecAssign(BaseModel):
    developer_id: int | None = None


class SpecTagsUpdate(BaseModel):
    tag_ids: list[int]


class TagCreate(BaseModel):
    name: str
    color: str = "#888"


class DevCreate(BaseModel):
    name: str
    email: str | None = None
    skills: str | None = None
    notes: str | None = None


class DevUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    skills: str | None = None
    notes: str | None = None


# --- Auth ---

def _get_user(request: Request) -> dict:
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(401, "Missing authorization token")
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user


# --- Specs ---

@router.get("/specs")
async def api_list_specs(request: Request, status: str | None = None,
                         tag: str | None = None, assigned_to: int | None = None):
    _get_user(request)
    return list_specs(status=status, tag=tag, assigned_to=assigned_to)


@router.post("/specs")
async def api_create_spec(body: SpecCreate, request: Request):
    user = _get_user(request)
    spec = create_spec(
        title=body.title,
        content=body.content,
        priority=body.priority,
        created_by=user["id"],
        chat_session_id=body.chat_session_id,
    )
    return spec


@router.get("/specs/{spec_id}")
async def api_get_spec(spec_id: int, request: Request):
    _get_user(request)
    spec = get_spec(spec_id)
    if not spec:
        raise HTTPException(404, "Spec not found")
    return spec


@router.put("/specs/{spec_id}")
async def api_update_spec(spec_id: int, body: SpecUpdate, request: Request):
    _get_user(request)
    spec = update_spec(spec_id, **body.model_dump(exclude_none=True))
    if not spec:
        raise HTTPException(404, "Spec not found")
    return spec


@router.delete("/specs/{spec_id}")
async def api_delete_spec(spec_id: int, request: Request):
    _get_user(request)
    if not delete_spec(spec_id):
        raise HTTPException(404, "Spec not found")
    return {"ok": True}


@router.put("/specs/{spec_id}/move")
async def api_move_spec(spec_id: int, body: SpecMove, request: Request):
    _get_user(request)
    valid = {'draft', 'ready', 'in_progress', 'review', 'done'}
    if body.status not in valid:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid}")
    spec = update_spec(spec_id, status=body.status)
    if not spec:
        raise HTTPException(404, "Spec not found")
    return spec


@router.put("/specs/{spec_id}/assign")
async def api_assign_spec(spec_id: int, body: SpecAssign, request: Request):
    _get_user(request)
    spec = update_spec(spec_id, assigned_to=body.developer_id)
    if not spec:
        raise HTTPException(404, "Spec not found")
    return spec


@router.put("/specs/{spec_id}/tags")
async def api_set_spec_tags(spec_id: int, body: SpecTagsUpdate, request: Request):
    _get_user(request)
    set_spec_tags(spec_id, body.tag_ids)
    return get_spec(spec_id)


# --- Tags ---

@router.get("/tags")
async def api_list_tags(request: Request):
    _get_user(request)
    return list_tags()


@router.post("/tags")
async def api_create_tag(body: TagCreate, request: Request):
    _get_user(request)
    return create_tag(body.name, body.color)


# --- Developers ---

@router.get("/developers")
async def api_list_developers(request: Request):
    _get_user(request)
    return list_developers()


@router.post("/developers")
async def api_create_developer(body: DevCreate, request: Request):
    user = _get_user(request)
    return create_developer(
        name=body.name, email=body.email,
        skills=body.skills, notes=body.notes,
        created_by=user["id"],
    )


@router.put("/developers/{dev_id}")
async def api_update_developer(dev_id: int, body: DevUpdate, request: Request):
    _get_user(request)
    dev = update_developer(dev_id, **body.model_dump(exclude_none=True))
    if not dev:
        raise HTTPException(404, "Developer not found")
    return dev


@router.delete("/developers/{dev_id}")
async def api_delete_developer(dev_id: int, request: Request):
    _get_user(request)
    if not delete_developer(dev_id):
        raise HTTPException(404, "Developer not found")
    return {"ok": True}
