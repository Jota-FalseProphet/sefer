from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from src.api.routes import router
from src.config import settings
from src.core.logging import server_log

app = FastAPI(title="Sefer", version="0.1.0")
app.include_router(router)

static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def index():
    return FileResponse(str(templates_dir / "index.html"))


@app.get("/login")
async def login_page():
    return FileResponse(str(templates_dir / "login.html"))


@app.get("/connect-claude")
async def connect_claude_page():
    return FileResponse(str(templates_dir / "connect-claude.html"))


@app.on_event("startup")
async def startup():
    server_log.info("Sefer started on %s:%d", settings.host, settings.port)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
