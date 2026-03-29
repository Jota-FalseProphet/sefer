from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json

from src.core.auth import (
    register, login, get_user_by_token,
    create_verification_code, verify_code,
    set_claude_authenticated,
)
from src.core.email import send_verification_email
from src.core.claude_runner import (
    run_claude_stream, start_claude_login,
    submit_oauth_code, check_claude_auth,
)
from src.core.logging import server_log

router = APIRouter(prefix="/api")


# --- Models ---

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class VerifyRequest(BaseModel):
    email: str
    code: str


class ResendCodeRequest(BaseModel):
    email: str


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class OAuthCodeRequest(BaseModel):
    code: str


# --- Auth helpers ---

def _get_user(request: Request) -> dict:
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(401, "Missing authorization token")
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user


# --- Auth endpoints ---

@router.post("/auth/register")
async def api_register(body: RegisterRequest):
    server_log.info("Register attempt: %s", body.email)
    result = register(body.email, body.password)
    if not result["ok"]:
        server_log.warning("Register failed: %s - %s", body.email, result["error"])
        raise HTTPException(400, result["error"])

    code = create_verification_code(body.email)
    try:
        send_verification_email(body.email, code)
    except Exception:
        server_log.error("Failed to send verification email to %s", body.email)
        raise HTTPException(500, "Failed to send verification email. Try again.")

    server_log.info("Register OK + verification sent: %s", body.email)
    return {"message": "Verification code sent to your email"}


@router.post("/auth/verify")
async def api_verify(body: VerifyRequest):
    server_log.info("Verify attempt: %s", body.email)
    result = verify_code(body.email, body.code)
    if not result["ok"]:
        server_log.warning("Verify failed: %s - %s", body.email, result["error"])
        raise HTTPException(400, result["error"])
    server_log.info("Verify OK: %s", body.email)
    return {"message": "Email verified successfully"}


@router.post("/auth/resend-code")
async def api_resend_code(body: ResendCodeRequest):
    server_log.info("Resend code: %s", body.email)
    code = create_verification_code(body.email)
    try:
        send_verification_email(body.email, code)
    except Exception:
        raise HTTPException(500, "Failed to send email. Try again.")
    return {"message": "New code sent"}


@router.post("/auth/login")
async def api_login(body: LoginRequest):
    server_log.info("Login attempt: %s", body.email)
    result = login(body.email, body.password)
    if not result["ok"]:
        server_log.warning("Login failed: %s", body.email)
        raise HTTPException(401, result["error"])
    server_log.info("Login OK: %s", body.email)
    return {
        "token": result["token"],
        "email": result["email"],
        "claude_authenticated": result.get("claude_authenticated", False),
    }


# --- Claude OAuth ---

@router.post("/claude/start-login")
async def api_claude_start_login(request: Request):
    user = _get_user(request)
    server_log.info("Claude OAuth start for user %s", user["email"])
    loop = asyncio.get_event_loop()
    url = await loop.run_in_executor(None, start_claude_login, user["id"])
    if not url:
        raise HTTPException(500, "Failed to start Claude login")
    return {"url": url}


@router.post("/claude/submit-code")
async def api_claude_submit_code(body: OAuthCodeRequest, request: Request):
    user = _get_user(request)
    server_log.info("Claude OAuth code submit for user %s: len=%d has_hash=%s",
                    user["email"], len(body.code), '#' in body.code)
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, submit_oauth_code, user["id"], body.code)
    if success:
        set_claude_authenticated(user["id"], True)
        return {"authenticated": True}
    raise HTTPException(400, "Authentication failed. Try starting login again.")


@router.get("/claude/check-auth")
async def api_claude_check_auth(request: Request):
    user = _get_user(request)
    if user["claude_authenticated"]:
        return {"authenticated": True}
    authenticated = await check_claude_auth(user["id"])
    if authenticated:
        set_claude_authenticated(user["id"], True)
    return {"authenticated": authenticated}


# --- Chat ---

@router.post("/chat")
async def api_chat(body: ChatRequest, request: Request):
    user = _get_user(request)

    if not user["claude_authenticated"]:
        raise HTTPException(403, "Connect your Claude account first.")

    server_log.info("Chat from %s: %s", user["email"], body.message[:100])

    async def event_stream():
        async for event in run_claude_stream(body.message, body.session_id, user_id=user["id"]):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# --- Health ---

@router.get("/health")
async def health():
    return {"status": "ok", "service": "sefer"}
