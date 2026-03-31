from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from src.api.routes import router
from src.api.specs_routes import router as specs_router
from src.config import settings
from src.core.logging import server_log

app = FastAPI(title="Sefer", version="0.1.0")
app.include_router(router)
app.include_router(specs_router)

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


@app.get("/specs")
async def specs_page():
    return FileResponse(str(templates_dir / "specs.html"))


@app.get("/specs/{spec_id}")
async def spec_detail_page(spec_id: int):
    return FileResponse(str(templates_dir / "spec-detail.html"))


@app.get("/team")
async def team_page():
    return FileResponse(str(templates_dir / "team.html"))


@app.on_event("startup")
async def startup():
    server_log.info("Sefer started on %s:%d", settings.host, settings.port)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
