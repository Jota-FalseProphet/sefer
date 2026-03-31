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
from src.core.specs import (
    list_conversations, create_conversation, update_conversation,
    delete_conversation, get_conversation_by_session,
    build_chat_context, save_message, get_messages,
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
    conversation_id: int | None = None


class OAuthCodeRequest(BaseModel):
    code: str


class ConversationUpdate(BaseModel):
    title: str | None = None
    context: str | None = None


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


# --- Conversations ---

@router.get("/conversations")
async def api_list_conversations(request: Request):
    user = _get_user(request)
    return list_conversations(user["id"])


@router.post("/conversations")
async def api_create_conversation(request: Request):
    user = _get_user(request)
    return create_conversation(user["id"])


@router.put("/conversations/{conv_id}")
async def api_update_conversation(conv_id: int, body: ConversationUpdate, request: Request):
    _get_user(request)
    result = update_conversation(conv_id, **body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(404, "Conversation not found")
    return result


@router.get("/conversations/{conv_id}/messages")
async def api_get_messages(conv_id: int, request: Request):
    _get_user(request)
    return get_messages(conv_id)


@router.delete("/conversations/{conv_id}")
async def api_delete_conversation(conv_id: int, request: Request):
    _get_user(request)
    if not delete_conversation(conv_id):
        raise HTTPException(404, "Conversation not found")
    return {"ok": True}


# --- Chat ---

@router.post("/chat")
async def api_chat(body: ChatRequest, request: Request):
    user = _get_user(request)

    if not user["claude_authenticated"]:
        raise HTTPException(403, "Connect your Claude account first.")

    server_log.info("Chat from %s: %s", user["email"], body.message[:100])

    # Build dynamic context with current specs/devs state
    conv_context = None
    if body.conversation_id:
        from src.core.specs import get_conversation_by_session
        # We'll look up context from DB if conversation has custom context
        pass
    dynamic_context = build_chat_context(conv_context)

    # Auto-title: use first 50 chars of first message as title
    auto_title = body.message[:50].strip()

    async def event_stream():
        conv_id = None
        assistant_parts = []

        async for event in run_claude_stream(
            body.message,
            body.session_id,
            user_id=user["id"],
            dynamic_context=dynamic_context,
        ):
            # Capture session_id and create/update conversation
            if event.get("type") == "system" and event.get("subtype") == "init":
                session_id = event.get("session_id")
                if not body.session_id and session_id:
                    conv = create_conversation(user["id"], title=auto_title, session_id=session_id)
                    conv_id = conv["id"]
                elif body.session_id:
                    existing = get_conversation_by_session(body.session_id)
                    if existing:
                        conv_id = existing["id"]
                        update_conversation(conv_id, title=existing["title"])
                event["conversation_id"] = conv_id

                # Save user message
                if conv_id:
                    save_message(conv_id, "user", body.message)

            # Collect assistant text
            if event.get("type") == "assistant":
                for block in event.get("message", {}).get("content", []):
                    if block.get("type") == "text":
                        assistant_parts.append(block["text"])
            elif event.get("type") == "result" and event.get("result"):
                if not assistant_parts:
                    assistant_parts.append(event["result"])

            yield f"data: {json.dumps(event)}\n\n"

        # Save assistant response
        if conv_id and assistant_parts:
            save_message(conv_id, "assistant", "".join(assistant_parts))

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# --- Health ---

@router.get("/health")
async def health():
    return {"status": "ok", "service": "sefer"}
